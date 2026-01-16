"""
LLVM IR Code Generator for the Luna compiler.

This module generates LLVM IR from Luna's SSA-based IR using the llvmlite library.
LLVM provides world-class optimizations and multi-target support (x86, ARM, etc.).

Key features:
- Direct mapping from Luna SSA IR to LLVM IR
- JIT compilation support via MCJIT
- Multiple target architecture support
- Integration with LLVM optimization passes
"""

from typing import Dict, Optional, List, Any
from llvmlite import ir, binding

from src.ir.instructions import (
    IRModule, IRFunction, IRValue, IRType, IRParameter,
    BasicBlock, IRInstruction,
    BinaryOp, UnaryOp, Copy, LoadConst,
    Jump, Branch, Phi, PhiSource, Call, Return,
    OpCode,
)


class LLVMCodeGenerator:
    """
    Generates LLVM IR from Luna's SSA-based IR.

    The generator maintains mappings between Luna IR values and LLVM values,
    handling the translation of instructions, control flow, and function calls.

    Example:
        generator = LLVMCodeGenerator()
        llvm_module = generator.generate(ir_module)
        print(str(llvm_module))  # LLVM IR text
    """

    def __init__(self):
        """Initialize the LLVM code generator."""
        # Initialize LLVM
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        # Current LLVM module being generated
        self.module: Optional[ir.Module] = None

        # Current IR builder
        self.builder: Optional[ir.IRBuilder] = None

        # Current function being generated
        self.func: Optional[ir.Function] = None

        # Maps Luna IRValue key (name_version) -> LLVM Value
        self.value_map: Dict[str, ir.Value] = {}

        # Maps Luna function name -> LLVM Function
        self.function_map: Dict[str, ir.Function] = {}

        # Maps Luna block label -> LLVM BasicBlock
        self.block_map: Dict[str, ir.Block] = {}

        # Maps string content -> global string constant
        self.string_map: Dict[str, ir.GlobalVariable] = {}

        # Printf function reference
        self.printf: Optional[ir.Function] = None

        # String counter for unique names
        self._string_counter: int = 0

    def generate(self, ir_module: IRModule) -> ir.Module:
        """
        Generate LLVM IR from a Luna IR module.

        Args:
            ir_module: The Luna IR module to compile

        Returns:
            LLVM IR module
        """
        # Create LLVM module
        self.module = ir.Module(name=ir_module.name)
        self.module.triple = binding.get_default_triple()

        # Declare external functions (printf for print())
        self._declare_externals()

        # First pass: declare all functions
        for func in ir_module.functions.values():
            self._declare_function(func)

        # Second pass: generate function bodies
        for func in ir_module.functions.values():
            self._generate_function(func)

        return self.module

    def _get_llvm_type(self, ir_type: IRType) -> ir.Type:
        """
        Convert Luna IRType to LLVM type.

        Args:
            ir_type: Luna IR type

        Returns:
            Corresponding LLVM type
        """
        type_map = {
            IRType.INT: ir.IntType(64),
            IRType.FLOAT: ir.DoubleType(),
            IRType.BOOL: ir.IntType(1),
            IRType.STRING: ir.IntType(8).as_pointer(),
            IRType.VOID: ir.VoidType(),
        }
        return type_map.get(ir_type, ir.IntType(64))

    def _declare_externals(self) -> None:
        """Declare external C functions (printf, etc.)."""
        # Declare printf: int printf(const char* format, ...)
        printf_type = ir.FunctionType(
            ir.IntType(32),
            [ir.IntType(8).as_pointer()],
            var_arg=True
        )
        self.printf = ir.Function(self.module, printf_type, name="printf")

    def _declare_function(self, func: IRFunction) -> None:
        """
        Declare a Luna function in LLVM IR.

        Args:
            func: Luna IR function
        """
        # Build parameter types
        param_types = [self._get_llvm_type(p.ir_type) for p in func.parameters]
        return_type = self._get_llvm_type(func.return_type)

        # Create function type
        func_type = ir.FunctionType(return_type, param_types)

        # Create function
        llvm_func = ir.Function(self.module, func_type, name=func.name)

        # Name parameters
        for i, param in enumerate(func.parameters):
            llvm_func.args[i].name = f"{param.name}_0"

        self.function_map[func.name] = llvm_func

    def _generate_function(self, func: IRFunction) -> None:
        """
        Generate LLVM IR for a Luna function body.

        Args:
            func: Luna IR function
        """
        self.func = self.function_map[func.name]
        self.value_map.clear()
        self.block_map.clear()

        # Map parameters to their LLVM values
        for i, param in enumerate(func.parameters):
            key = f"{param.name}_0"
            self.value_map[key] = self.func.args[i]

        # Create LLVM basic blocks for all Luna blocks
        for label in self._get_block_order(func):
            llvm_block = self.func.append_basic_block(name=label)
            self.block_map[label] = llvm_block

        # Generate instructions for each block
        for label in self._get_block_order(func):
            block = func.blocks[label]
            llvm_block = self.block_map[label]
            self.builder = ir.IRBuilder(llvm_block)

            # First, generate phi nodes (must be at start of block)
            phi_nodes = self._generate_phi_placeholders(block)

            # Generate other instructions
            for instr in block.instructions:
                if isinstance(instr, Phi):
                    continue  # Already handled
                self._generate_instruction(instr)

        # Second pass: fill in phi node incoming values
        for label in self._get_block_order(func):
            block = func.blocks[label]
            self._complete_phi_nodes(block)

    def _get_block_order(self, func: IRFunction) -> List[str]:
        """
        Get blocks in reverse postorder for proper SSA dominance.

        This ensures that definitions dominate uses (except for loop back-edges,
        which are handled by phi nodes).

        Args:
            func: Luna IR function

        Returns:
            List of block labels in reverse postorder
        """
        if not func.blocks:
            return []

        visited = set()
        postorder = []

        def dfs(label: str):
            if label in visited or label not in func.blocks:
                return
            visited.add(label)

            block = func.blocks[label]
            # Visit successors
            for succ in block.successors:
                dfs(succ)

            postorder.append(label)

        # Start DFS from entry block
        dfs(func.entry_block)

        # Reverse postorder
        order = list(reversed(postorder))

        # Add any blocks not reachable from entry (shouldn't happen normally)
        for label in func.blocks:
            if label not in order:
                order.append(label)

        return order

    def _generate_phi_placeholders(self, block: BasicBlock) -> Dict[str, ir.PhiInstr]:
        """
        Generate phi node placeholders at the start of a block.

        Args:
            block: Luna basic block

        Returns:
            Dictionary of phi node key -> LLVM phi instruction
        """
        phi_nodes = {}

        for instr in block.instructions:
            if not isinstance(instr, Phi):
                break  # Phi nodes must be at start

            phi_type = self._get_llvm_type(instr.dest.ir_type)
            phi = self.builder.phi(phi_type, name=self._value_key(instr.dest))
            self._set_value(instr.dest, phi)
            phi_nodes[self._value_key(instr.dest)] = phi

        return phi_nodes

    def _complete_phi_nodes(self, block: BasicBlock) -> None:
        """
        Fill in incoming values for phi nodes after all blocks are generated.

        Args:
            block: Luna basic block
        """
        for instr in block.instructions:
            if not isinstance(instr, Phi):
                break

            phi = self._get_value(instr.dest)
            if not isinstance(phi, ir.PhiInstr):
                continue

            for source in instr.sources:
                incoming_value = self._get_value(source.value)
                incoming_block = self.block_map[source.block]
                phi.add_incoming(incoming_value, incoming_block)

    def _generate_instruction(self, instr: IRInstruction) -> None:
        """
        Generate LLVM IR for a single instruction.

        Args:
            instr: Luna IR instruction
        """
        if isinstance(instr, LoadConst):
            self._gen_load_const(instr)
        elif isinstance(instr, Copy):
            self._gen_copy(instr)
        elif isinstance(instr, BinaryOp):
            self._gen_binary_op(instr)
        elif isinstance(instr, UnaryOp):
            self._gen_unary_op(instr)
        elif isinstance(instr, Jump):
            self._gen_jump(instr)
        elif isinstance(instr, Branch):
            self._gen_branch(instr)
        elif isinstance(instr, Call):
            self._gen_call(instr)
        elif isinstance(instr, Return):
            self._gen_return(instr)
        # Phi is handled separately

    def _value_key(self, value: IRValue) -> str:
        """Get the key for an IRValue in the value map."""
        if value.is_constant:
            return f"const_{value.constant_value}_{value.ir_type}"
        return f"{value.name}_{value.version}"

    def _get_value(self, value: IRValue) -> ir.Value:
        """
        Get the LLVM value for a Luna IRValue.

        Args:
            value: Luna IR value

        Returns:
            Corresponding LLVM value
        """
        if value.is_constant:
            return self._get_constant(value)

        key = self._value_key(value)
        if key in self.value_map:
            return self.value_map[key]

        raise KeyError(f"Value not found: {key}")

    def _set_value(self, ir_value: IRValue, llvm_value: ir.Value) -> None:
        """
        Store a mapping from Luna IRValue to LLVM value.

        Args:
            ir_value: Luna IR value
            llvm_value: LLVM value
        """
        key = self._value_key(ir_value)
        self.value_map[key] = llvm_value

    def _get_constant(self, value: IRValue) -> ir.Constant:
        """
        Get an LLVM constant for a Luna constant value.

        Args:
            value: Luna constant IR value

        Returns:
            LLVM constant
        """
        if value.ir_type == IRType.INT:
            return ir.Constant(ir.IntType(64), value.constant_value)
        elif value.ir_type == IRType.FLOAT:
            return ir.Constant(ir.DoubleType(), value.constant_value)
        elif value.ir_type == IRType.BOOL:
            return ir.Constant(ir.IntType(1), 1 if value.constant_value else 0)
        elif value.ir_type == IRType.STRING:
            return self._get_string_constant(value.constant_value)
        else:
            return ir.Constant(ir.IntType(64), 0)

    def _get_string_constant(self, string_value: str) -> ir.Value:
        """
        Get or create a global string constant.

        Args:
            string_value: The string content

        Returns:
            Pointer to the string constant
        """
        if string_value in self.string_map:
            gvar = self.string_map[string_value]
        else:
            # Create null-terminated string
            string_bytes = bytearray(string_value.encode('utf-8'))
            string_bytes.append(0)  # Null terminator

            # Create global constant
            str_type = ir.ArrayType(ir.IntType(8), len(string_bytes))
            gvar = ir.GlobalVariable(self.module, str_type, name=f".str.{self._string_counter}")
            self._string_counter += 1
            gvar.global_constant = True
            gvar.linkage = 'private'
            gvar.initializer = ir.Constant(str_type, string_bytes)

            self.string_map[string_value] = gvar

        # Return pointer to first element
        zero = ir.Constant(ir.IntType(32), 0)
        return self.builder.gep(gvar, [zero, zero], inbounds=True)

    def _get_or_create_format_string(self, fmt: str) -> ir.Value:
        """Get or create a format string for printf."""
        return self._get_string_constant(fmt)

    def _gen_load_const(self, instr: LoadConst) -> None:
        """Generate LLVM IR for LoadConst instruction."""
        if instr.value_type == IRType.STRING:
            value = self._get_string_constant(instr.value)
        elif instr.value_type == IRType.BOOL:
            value = ir.Constant(ir.IntType(1), 1 if instr.value else 0)
        elif instr.value_type == IRType.FLOAT:
            value = ir.Constant(ir.DoubleType(), instr.value)
        else:
            value = ir.Constant(ir.IntType(64), instr.value)

        self._set_value(instr.dest, value)

    def _gen_copy(self, instr: Copy) -> None:
        """Generate LLVM IR for Copy instruction."""
        source_value = self._get_value(instr.source)
        self._set_value(instr.dest, source_value)

    def _gen_binary_op(self, instr: BinaryOp) -> None:
        """Generate LLVM IR for BinaryOp instruction."""
        left = self._get_value(instr.left)
        right = self._get_value(instr.right)
        name = self._value_key(instr.dest)

        op = instr.op

        # Arithmetic operations
        if op == OpCode.ADD:
            result = self.builder.add(left, right, name=name)
        elif op == OpCode.SUB:
            result = self.builder.sub(left, right, name=name)
        elif op == OpCode.MUL:
            result = self.builder.mul(left, right, name=name)
        elif op == OpCode.DIV:
            result = self.builder.sdiv(left, right, name=name)
        elif op == OpCode.MOD:
            result = self.builder.srem(left, right, name=name)

        # Comparison operations
        elif op == OpCode.LT:
            result = self.builder.icmp_signed('<', left, right, name=name)
        elif op == OpCode.GT:
            result = self.builder.icmp_signed('>', left, right, name=name)
        elif op == OpCode.LE:
            result = self.builder.icmp_signed('<=', left, right, name=name)
        elif op == OpCode.GE:
            result = self.builder.icmp_signed('>=', left, right, name=name)
        elif op == OpCode.EQ:
            result = self.builder.icmp_signed('==', left, right, name=name)
        elif op == OpCode.NE:
            result = self.builder.icmp_signed('!=', left, right, name=name)

        # Logical operations
        elif op == OpCode.AND:
            result = self.builder.and_(left, right, name=name)
        elif op == OpCode.OR:
            result = self.builder.or_(left, right, name=name)
        else:
            raise ValueError(f"Unknown binary op: {op}")

        self._set_value(instr.dest, result)

    def _gen_unary_op(self, instr: UnaryOp) -> None:
        """Generate LLVM IR for UnaryOp instruction."""
        operand = self._get_value(instr.operand)
        name = self._value_key(instr.dest)

        if instr.op == OpCode.NEG:
            result = self.builder.neg(operand, name=name)
        elif instr.op == OpCode.NOT:
            result = self.builder.not_(operand, name=name)
        else:
            raise ValueError(f"Unknown unary op: {instr.op}")

        self._set_value(instr.dest, result)

    def _gen_jump(self, instr: Jump) -> None:
        """Generate LLVM IR for Jump instruction."""
        target_block = self.block_map[instr.target]
        self.builder.branch(target_block)

    def _gen_branch(self, instr: Branch) -> None:
        """Generate LLVM IR for Branch instruction."""
        condition = self._get_value(instr.condition)
        true_block = self.block_map[instr.true_target]
        false_block = self.block_map[instr.false_target]

        # Ensure condition is i1 (boolean)
        if condition.type != ir.IntType(1):
            # Convert to boolean by comparing with 0
            condition = self.builder.icmp_signed('!=', condition,
                ir.Constant(condition.type, 0))

        self.builder.cbranch(condition, true_block, false_block)

    def _gen_call(self, instr: Call) -> None:
        """Generate LLVM IR for Call instruction."""
        # Handle built-in print function
        if instr.function == "print":
            self._gen_print_call(instr)
            return

        # Get the function
        if instr.function not in self.function_map:
            raise ValueError(f"Unknown function: {instr.function}")

        callee = self.function_map[instr.function]

        # Get arguments
        args = [self._get_value(arg) for arg in instr.arguments]

        # Generate call
        if instr.dest is not None:
            result = self.builder.call(callee, args, name=self._value_key(instr.dest))
            self._set_value(instr.dest, result)
        else:
            self.builder.call(callee, args)

    def _gen_print_call(self, instr: Call) -> None:
        """Generate LLVM IR for the built-in print function."""
        if not instr.arguments:
            return

        arg = instr.arguments[0]
        arg_value = self._get_value(arg)

        # Determine format string based on type
        if arg.ir_type == IRType.STRING:
            fmt = self._get_or_create_format_string("%s\n")
            self.builder.call(self.printf, [fmt, arg_value])
        elif arg.ir_type == IRType.FLOAT:
            fmt = self._get_or_create_format_string("%f\n")
            self.builder.call(self.printf, [fmt, arg_value])
        elif arg.ir_type == IRType.BOOL:
            # Extend bool to i64 for printf
            extended = self.builder.zext(arg_value, ir.IntType(64))
            fmt = self._get_or_create_format_string("%ld\n")
            self.builder.call(self.printf, [fmt, extended])
        else:
            # Integer
            fmt = self._get_or_create_format_string("%ld\n")
            self.builder.call(self.printf, [fmt, arg_value])

    def _gen_return(self, instr: Return) -> None:
        """Generate LLVM IR for Return instruction."""
        if instr.value is not None:
            ret_value = self._get_value(instr.value)
            self.builder.ret(ret_value)
        else:
            self.builder.ret_void()


def generate_llvm_ir(module: IRModule) -> ir.Module:
    """
    Generate LLVM IR from a Luna IR module.

    Args:
        module: The Luna IR module to compile

    Returns:
        LLVM IR module
    """
    generator = LLVMCodeGenerator()
    return generator.generate(module)
