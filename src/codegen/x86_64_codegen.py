"""
x86-64 Assembly Code Generator for the Luna compiler.

This module generates x86-64 assembly code from SSA-based IR,
targeting macOS with System V AMD64 ABI calling convention.

Features:
- Stack-based variable storage (no register allocation)
- Function call support with proper ABI
- All arithmetic, comparison, and logical operations
- Control flow (jumps, branches)
- Phi function resolution

The generated assembly uses AT&T syntax (macOS default) and can be assembled with:
    as -o program.o program.s
    gcc -o program program.o
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

from src.ir.instructions import (
    IRModule,
    IRFunction,
    BasicBlock,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Jump,
    Branch,
    Phi,
    Call,
    Return,
    IRValue,
    IRType,
    OpCode,
)
from src.codegen.stack_frame import StackFrame, StackFrameBuilder


@dataclass
class AsmInstruction:
    """Represents a single assembly instruction."""
    opcode: str
    operands: List[str] = field(default_factory=list)
    comment: str = ""

    def __str__(self) -> str:
        if not self.operands:
            instr = f"    {self.opcode}"
        else:
            instr = f"    {self.opcode} {', '.join(self.operands)}"

        if self.comment:
            instr = f"{instr:<40} # {self.comment}"
        return instr


@dataclass
class AsmLabel:
    """Represents a label in assembly."""
    name: str
    is_global: bool = False

    def __str__(self) -> str:
        if self.is_global:
            return f".globl {self.name}\n{self.name}:"
        return f"{self.name}:"


class X86_64CodeGenerator:
    """
    Generates x86-64 assembly from IR.

    This is a simple stack-based code generator:
    - All variables live on the stack
    - Operations load to rax, operate, store back
    - No register allocation (future optimization)
    """

    # Argument registers (System V AMD64 ABI)
    ARG_REGISTERS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']

    def __init__(self):
        self.frame_builder = StackFrameBuilder()
        self.current_frame: Optional[StackFrame] = None
        self.current_function: Optional[IRFunction] = None
        self.output: List[str] = []
        # Track phi destinations that need copying at block ends
        self.phi_copies: Dict[str, List[Tuple[IRValue, IRValue]]] = {}
        # String literals
        self.string_literals: Dict[str, str] = {}
        self.string_counter = 0

    def generate(self, module: IRModule) -> str:
        """
        Generate assembly for an entire module.

        Args:
            module: The IR module to compile

        Returns:
            Complete assembly code as a string
        """
        self.output = []
        self.string_literals = {}
        self.string_counter = 0

        # Collect all string literals first
        self._collect_strings(module)

        # Generate data section
        self._emit_data_section()

        # Generate text section
        self._emit_text_section(module)

        return "\n".join(self.output)

    def _collect_strings(self, module: IRModule) -> None:
        """Collect all string literals from the module."""
        for func in module.functions.values():
            for block in func.blocks.values():
                for instr in block.instructions:
                    if isinstance(instr, LoadConst) and instr.value_type == IRType.STRING:
                        self._get_string_label(instr.value)
                    elif isinstance(instr, Call):
                        # Check for string arguments
                        for arg in instr.arguments:
                            if arg.is_constant and arg.ir_type == IRType.STRING:
                                self._get_string_label(arg.constant_value)

    def _get_string_label(self, value: str) -> str:
        """Get or create a label for a string literal."""
        if value not in self.string_literals:
            label = f"_str_{self.string_counter}"
            self.string_literals[value] = label
            self.string_counter += 1
        return self.string_literals[value]

    def _emit_data_section(self) -> None:
        """Emit the data section with string literals and format strings."""
        self.output.append(".section __DATA,__data")
        self.output.append("")

        # Format strings for printf
        self.output.append("_fmt_int:")
        self.output.append('    .asciz "%ld\\n"')
        self.output.append("_fmt_str:")
        self.output.append('    .asciz "%s\\n"')
        self.output.append("")

        # User string literals
        for value, label in self.string_literals.items():
            # Escape the string for assembly
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            self.output.append(f"{label}:")
            self.output.append(f'    .asciz "{escaped}"')

        self.output.append("")

    def _emit_text_section(self, module: IRModule) -> None:
        """Emit the text (code) section."""
        self.output.append(".section __TEXT,__text")
        self.output.append("")

        for func in module.functions.values():
            self._generate_function(func)

    def _generate_function(self, func: IRFunction) -> None:
        """Generate assembly for a function."""
        self.current_function = func
        self.current_frame = self.frame_builder.build(func)

        # Collect phi information
        self._collect_phi_info(func)

        # Function label (with underscore prefix for macOS)
        func_label = f"_{func.name}"
        if func.name == "main":
            self.output.append(f".globl {func_label}")
        self.output.append(f"{func_label}:")

        # Prologue
        self._emit_prologue()

        # Copy parameters from registers to stack
        self._emit_param_copies(func)

        # Generate code for each basic block
        block_order = self._get_block_order(func)
        for label in block_order:
            block = func.blocks.get(label)
            if block:
                self._generate_block(block)

        self.output.append("")

    def _collect_phi_info(self, func: IRFunction) -> None:
        """
        Collect phi function information for resolution.

        For each phi instruction, we need to copy the appropriate
        value at the end of each predecessor block.
        """
        self.phi_copies = {}

        for block in func.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, Phi):
                    for source in instr.sources:
                        pred_block = source.block
                        if pred_block not in self.phi_copies:
                            self.phi_copies[pred_block] = []
                        # At end of pred_block, copy source.value to instr.dest
                        self.phi_copies[pred_block].append((source.value, instr.dest))

    def _emit_prologue(self) -> None:
        """Emit function prologue."""
        self.output.append("    pushq %rbp")
        self.output.append("    movq %rsp, %rbp")
        frame_size = self.current_frame.frame_size
        if frame_size > 0:
            self.output.append(f"    subq ${frame_size}, %rsp")

    def _emit_epilogue(self) -> None:
        """Emit function epilogue."""
        self.output.append("    movq %rbp, %rsp")
        self.output.append("    popq %rbp")
        self.output.append("    retq")

    def _emit_param_copies(self, func: IRFunction) -> None:
        """Copy function parameters from registers to stack slots."""
        for i, param in enumerate(func.parameters):
            slot = self.current_frame.get_slot(
                IRValue(name=param.name, version=0, ir_type=param.ir_type)
            )
            if slot is None:
                continue

            if i < len(self.ARG_REGISTERS):
                # Parameter is in a register
                reg = self.ARG_REGISTERS[i]
                self.output.append(f"    movq %{reg}, {slot.offset}(%rbp)")
            else:
                # Parameter is on stack (caller pushed it)
                caller_offset = 16 + (i - len(self.ARG_REGISTERS)) * 8
                self.output.append(f"    movq {caller_offset}(%rbp), %rax")
                self.output.append(f"    movq %rax, {slot.offset}(%rbp)")

    def _get_block_order(self, func: IRFunction) -> List[str]:
        """Get blocks in a sensible order (entry first)."""
        order = []
        if func.entry_block in func.blocks:
            order.append(func.entry_block)

        for label in sorted(func.blocks.keys()):
            if label not in order:
                order.append(label)

        return order

    def _generate_block(self, block: BasicBlock) -> None:
        """Generate assembly for a basic block."""
        # Block label (prefixed with function name to avoid collisions)
        func_name = self.current_function.name
        self.output.append(f"_{func_name}_{block.label}:")

        for instr in block.instructions:
            self._generate_instruction(instr, block.label)

    def _generate_instruction(self, instr: IRInstruction, block_label: str) -> None:
        """Generate assembly for a single IR instruction."""
        if isinstance(instr, LoadConst):
            self._gen_load_const(instr)
        elif isinstance(instr, Copy):
            self._gen_copy(instr)
        elif isinstance(instr, BinaryOp):
            self._gen_binary_op(instr)
        elif isinstance(instr, UnaryOp):
            self._gen_unary_op(instr)
        elif isinstance(instr, Jump):
            self._emit_phi_copies(block_label)
            self._gen_jump(instr)
        elif isinstance(instr, Branch):
            self._emit_phi_copies(block_label)
            self._gen_branch(instr)
        elif isinstance(instr, Call):
            self._gen_call(instr)
        elif isinstance(instr, Return):
            self._gen_return(instr)
        elif isinstance(instr, Phi):
            # Phi instructions are handled at predecessor block ends
            pass

    def _emit_phi_copies(self, block_label: str) -> None:
        """Emit phi resolution copies at end of a block."""
        if block_label not in self.phi_copies:
            return

        copies = self.phi_copies[block_label]
        for src_value, dest_value in copies:
            self._emit_comment(f"phi: {dest_value} = {src_value}")
            src_operand = self._get_operand(src_value)
            dest_slot = self.current_frame.get_slot(dest_value)
            if dest_slot:
                self.output.append(f"    movq {src_operand}, %rax")
                self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _get_operand(self, value: IRValue) -> str:
        """
        Get the assembly operand for an IRValue (AT&T syntax).

        Returns either an immediate value or a memory reference.
        """
        if value.is_constant:
            if value.ir_type == IRType.BOOL:
                return "$1" if value.constant_value else "$0"
            elif value.ir_type == IRType.STRING:
                label = self._get_string_label(value.constant_value)
                return f"{label}(%rip)"
            else:
                return f"${value.constant_value}"

        slot = self.current_frame.get_slot(value)
        if slot:
            return f"{slot.offset}(%rbp)"

        # Shouldn't happen - variable not in frame
        return f"ERROR_{value.name}_{value.version}"

    def _emit_comment(self, comment: str) -> None:
        """Emit a comment."""
        self.output.append(f"    # {comment}")

    def _gen_load_const(self, instr: LoadConst) -> None:
        """Generate code for LoadConst instruction."""
        dest_slot = self.current_frame.get_slot(instr.dest)
        if dest_slot is None:
            return

        self._emit_comment(f"{instr.dest} = {instr.value}")

        if instr.value_type == IRType.STRING:
            # Load address of string literal
            label = self._get_string_label(instr.value)
            self.output.append(f"    leaq {label}(%rip), %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")
        elif instr.value_type == IRType.BOOL:
            val = 1 if instr.value else 0
            self.output.append(f"    movq ${val}, {dest_slot.offset}(%rbp)")
        else:
            self.output.append(f"    movq ${instr.value}, {dest_slot.offset}(%rbp)")

    def _gen_copy(self, instr: Copy) -> None:
        """Generate code for Copy instruction."""
        dest_slot = self.current_frame.get_slot(instr.dest)
        if dest_slot is None:
            return

        self._emit_comment(f"{instr.dest} = {instr.source}")

        src_operand = self._get_operand(instr.source)
        self.output.append(f"    movq {src_operand}, %rax")
        self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _gen_binary_op(self, instr: BinaryOp) -> None:
        """Generate code for BinaryOp instruction."""
        dest_slot = self.current_frame.get_slot(instr.dest)
        if dest_slot is None:
            return

        self._emit_comment(f"{instr.dest} = {instr.left} {instr.op} {instr.right}")

        left_op = self._get_operand(instr.left)
        right_op = self._get_operand(instr.right)

        op = instr.op

        # Arithmetic operations
        if op == OpCode.ADD:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append(f"    addq {right_op}, %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif op == OpCode.SUB:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append(f"    subq {right_op}, %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif op == OpCode.MUL:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append(f"    imulq {right_op}, %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif op == OpCode.DIV:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append("    cqto")  # Sign-extend rax into rdx:rax
            self.output.append(f"    movq {right_op}, %rcx")
            self.output.append("    idivq %rcx")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif op == OpCode.MOD:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append("    cqto")
            self.output.append(f"    movq {right_op}, %rcx")
            self.output.append("    idivq %rcx")
            self.output.append(f"    movq %rdx, {dest_slot.offset}(%rbp)")  # Remainder in rdx

        # Comparison operations
        elif op in (OpCode.LT, OpCode.GT, OpCode.LE, OpCode.GE, OpCode.EQ, OpCode.NE):
            self._gen_comparison(instr, dest_slot, left_op, right_op)

        # Logical operations
        elif op == OpCode.AND:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append(f"    andq {right_op}, %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif op == OpCode.OR:
            self.output.append(f"    movq {left_op}, %rax")
            self.output.append(f"    orq {right_op}, %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _gen_comparison(self, instr: BinaryOp, dest_slot, left_op: str, right_op: str) -> None:
        """Generate code for comparison operations."""
        self.output.append(f"    movq {left_op}, %rax")
        self.output.append(f"    cmpq {right_op}, %rax")

        # Set byte based on comparison
        op = instr.op
        if op == OpCode.LT:
            self.output.append("    setl %al")
        elif op == OpCode.GT:
            self.output.append("    setg %al")
        elif op == OpCode.LE:
            self.output.append("    setle %al")
        elif op == OpCode.GE:
            self.output.append("    setge %al")
        elif op == OpCode.EQ:
            self.output.append("    sete %al")
        elif op == OpCode.NE:
            self.output.append("    setne %al")

        # Zero-extend to 64 bits
        self.output.append("    movzbq %al, %rax")
        self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _gen_unary_op(self, instr: UnaryOp) -> None:
        """Generate code for UnaryOp instruction."""
        dest_slot = self.current_frame.get_slot(instr.dest)
        if dest_slot is None:
            return

        self._emit_comment(f"{instr.dest} = {instr.op} {instr.operand}")

        operand = self._get_operand(instr.operand)

        if instr.op == OpCode.NEG:
            self.output.append(f"    movq {operand}, %rax")
            self.output.append("    negq %rax")
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

        elif instr.op == OpCode.NOT:
            self.output.append(f"    movq {operand}, %rax")
            self.output.append("    xorq $1, %rax")  # Flip the boolean
            self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _gen_jump(self, instr: Jump) -> None:
        """Generate code for Jump instruction."""
        func_name = self.current_function.name
        target = f"_{func_name}_{instr.target}"
        self.output.append(f"    jmp {target}")

    def _gen_branch(self, instr: Branch) -> None:
        """Generate code for Branch instruction."""
        func_name = self.current_function.name
        true_label = f"_{func_name}_{instr.true_target}"
        false_label = f"_{func_name}_{instr.false_target}"

        cond_op = self._get_operand(instr.condition)

        self._emit_comment(f"branch {instr.condition}, {instr.true_target}, {instr.false_target}")
        self.output.append(f"    movq {cond_op}, %rax")
        self.output.append("    cmpq $0, %rax")
        self.output.append(f"    jne {true_label}")
        self.output.append(f"    jmp {false_label}")

    def _gen_call(self, instr: Call) -> None:
        """Generate code for Call instruction."""
        self._emit_comment(f"call {instr.function}({', '.join(str(a) for a in instr.arguments)})")

        # Handle built-in print function specially
        if instr.function == "print":
            self._gen_print_call(instr)
            return

        # Setup arguments in registers (first 6) or stack
        for i, arg in enumerate(instr.arguments):
            arg_operand = self._get_operand(arg)
            if i < len(self.ARG_REGISTERS):
                reg = self.ARG_REGISTERS[i]
                self.output.append(f"    movq {arg_operand}, %{reg}")
            else:
                # Push additional arguments onto stack (in reverse order)
                self.output.append(f"    pushq {arg_operand}")

        # Call the function (with underscore prefix for macOS)
        self.output.append(f"    callq _{instr.function}")

        # Clean up stack arguments if any
        extra_args = len(instr.arguments) - len(self.ARG_REGISTERS)
        if extra_args > 0:
            self.output.append(f"    addq ${extra_args * 8}, %rsp")

        # Store return value if needed
        if instr.dest is not None:
            dest_slot = self.current_frame.get_slot(instr.dest)
            if dest_slot:
                self.output.append(f"    movq %rax, {dest_slot.offset}(%rbp)")

    def _gen_print_call(self, instr: Call) -> None:
        """Generate code for the built-in print function."""
        if not instr.arguments:
            return

        arg = instr.arguments[0]
        arg_operand = self._get_operand(arg)

        # Determine format string based on argument type
        if arg.ir_type == IRType.STRING:
            # Print string
            self.output.append("    leaq _fmt_str(%rip), %rdi")
            if arg.is_constant:
                label = self._get_string_label(arg.constant_value)
                self.output.append(f"    leaq {label}(%rip), %rsi")
            else:
                self.output.append(f"    movq {arg_operand}, %rsi")
        else:
            # Print integer (or bool as 0/1)
            self.output.append("    leaq _fmt_int(%rip), %rdi")
            self.output.append(f"    movq {arg_operand}, %rsi")

        # Call printf (need to zero rax for variadic function)
        self.output.append("    xorq %rax, %rax")
        self.output.append("    callq _printf")

    def _gen_return(self, instr: Return) -> None:
        """Generate code for Return instruction."""
        if instr.value is not None:
            self._emit_comment(f"return {instr.value}")
            ret_operand = self._get_operand(instr.value)
            self.output.append(f"    movq {ret_operand}, %rax")
        else:
            self._emit_comment("return void")
            self.output.append("    xorq %rax, %rax")

        self._emit_epilogue()


def generate_assembly(module: IRModule) -> str:
    """
    Generate x86-64 assembly code from an IR module.

    Args:
        module: The IR module to compile

    Returns:
        Assembly code as a string
    """
    generator = X86_64CodeGenerator()
    return generator.generate(module)
