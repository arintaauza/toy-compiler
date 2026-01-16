"""
IR Generator for the Toy compiler.

This module translates the typed AST into SSA-form IR.
It uses the visitor pattern to traverse the AST and emit
IR instructions for each node.

Key responsibilities:
- Convert AST expressions to IR instructions
- Handle control flow (if/while) with basic blocks
- Generate SSA variable versions
- Insert phi functions at control flow merge points
- Maintain variable-to-SSA-value mapping

Usage:
    generator = IRGenerator()
    module = generator.generate(program)  # Returns IRModule
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

from src.parser.ast_nodes import (
    ASTVisitor,
    ASTNode,
    Expression,
    Statement,
    Declaration,
    LiteralExpr,
    VariableExpr,
    BinaryExpr,
    UnaryExpr,
    GroupingExpr,
    CallExpr,
    AssignmentExpr,
    ExprStmt,
    VarDeclStmt,
    BlockStmt,
    IfStmt,
    WhileStmt,
    ReturnStmt,
    FunctionDecl,
    Program,
    TypeAnnotation,
)
from src.ir.instructions import (
    IRType,
    IRValue,
    OpCode,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Jump,
    Branch,
    Phi,
    PhiSource,
    Call,
    Return,
    BasicBlock,
    IRParameter,
    IRFunction,
    IRModule,
    make_constant,
)
from src.ir.ssa import SSANameGenerator, toy_type_to_ir_type
from src.ir.cfg import CFG, CFGBuilder


# Mapping from Toy operators to IR opcodes
BINARY_OP_MAP = {
    "+": OpCode.ADD,
    "-": OpCode.SUB,
    "*": OpCode.MUL,
    "/": OpCode.DIV,
    "%": OpCode.MOD,
    "<": OpCode.LT,
    ">": OpCode.GT,
    "<=": OpCode.LE,
    ">=": OpCode.GE,
    "==": OpCode.EQ,
    "!=": OpCode.NE,
    "and": OpCode.AND,
    "or": OpCode.OR,
    "&&": OpCode.AND,
    "||": OpCode.OR,
}

UNARY_OP_MAP = {
    "-": OpCode.NEG,
    "!": OpCode.NOT,
    "not": OpCode.NOT,
}


def type_annotation_to_ir_type(annotation: Optional[TypeAnnotation]) -> IRType:
    """Convert AST TypeAnnotation to IRType."""
    if annotation is None:
        return IRType.VOID

    mapping = {
        TypeAnnotation.INT: IRType.INT,
        TypeAnnotation.FLOAT: IRType.FLOAT,
        TypeAnnotation.BOOL: IRType.BOOL,
        TypeAnnotation.STRING: IRType.STRING,
        TypeAnnotation.VOID: IRType.VOID,
    }
    return mapping.get(annotation, IRType.VOID)


class IRGenerator(ASTVisitor):
    """
    Generates SSA-form IR from a typed AST.

    The generator uses the visitor pattern to traverse the AST
    and emit IR instructions. It maintains:
    - Current function being generated
    - Current basic block for instruction emission
    - SSA name generator for variable versioning
    - CFG builder for control flow construction

    Usage:
        generator = IRGenerator()
        ir_module = generator.generate(program)
    """

    def __init__(self):
        """Initialize the IR generator."""
        self._module: Optional[IRModule] = None
        self._current_function: Optional[IRFunction] = None
        self._cfg_builder: Optional[CFGBuilder] = None
        self._ssa: Optional[SSANameGenerator] = None

        # Track current return type for validation
        self._current_return_type: IRType = IRType.VOID

    def generate(self, program: Program) -> IRModule:
        """
        Generate IR for a complete program.

        Args:
            program: The typed AST program

        Returns:
            IRModule containing all generated functions
        """
        self._module = IRModule(name="main_module")
        program.accept(self)
        return self._module

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _emit(self, instruction: IRInstruction) -> None:
        """Emit an instruction to the current block."""
        if self._cfg_builder:
            self._cfg_builder.emit(instruction)

    def _new_block(self, prefix: str = "B") -> BasicBlock:
        """Create a new basic block."""
        return self._cfg_builder.new_block(prefix)

    def _current_block(self) -> Optional[BasicBlock]:
        """Get the current block."""
        return self._cfg_builder.get_current_block()

    def _current_block_label(self) -> str:
        """Get the current block label."""
        return self._cfg_builder.get_current_label()

    def _position_at(self, block: BasicBlock) -> None:
        """Position at end of block for emission."""
        self._cfg_builder.position_at_end(block)

    def _is_block_terminated(self) -> bool:
        """Check if current block has a terminator."""
        block = self._current_block()
        return block is not None and block.is_terminated()

    # =========================================================================
    # Expression Visitors (return IRValue)
    # =========================================================================

    def visit_literal_expr(self, expr: LiteralExpr) -> IRValue:
        """
        Generate IR for a literal expression.

        Emits a LoadConst instruction and returns the destination.
        """
        # Determine IR type from literal type
        ir_type = type_annotation_to_ir_type(expr.literal_type)

        # For simple cases, we can return a constant directly
        # But for consistency, emit a LoadConst instruction
        dest = self._ssa.new_temp(ir_type)
        self._emit(LoadConst(dest=dest, value=expr.value, value_type=ir_type))
        return dest

    def visit_variable_expr(self, expr: VariableExpr) -> IRValue:
        """
        Generate IR for a variable reference.

        Returns the current SSA version of the variable.
        """
        if self._ssa.has_variable(expr.name):
            return self._ssa.get_current(expr.name)
        else:
            # Variable should exist (semantic analysis verified this)
            # This might be a function parameter or global
            raise RuntimeError(f"Variable '{expr.name}' not found in SSA context")

    def visit_binary_expr(self, expr: BinaryExpr) -> IRValue:
        """
        Generate IR for a binary expression.

        Emits left operand, right operand, then binary operation.
        """
        left = expr.left.accept(self)
        right = expr.right.accept(self)

        # Get the operation code
        op = BINARY_OP_MAP.get(expr.operator)
        if op is None:
            raise RuntimeError(f"Unknown binary operator: {expr.operator}")

        # Determine result type
        if op in (OpCode.LT, OpCode.GT, OpCode.LE, OpCode.GE, OpCode.EQ, OpCode.NE,
                  OpCode.AND, OpCode.OR):
            result_type = IRType.BOOL
        else:
            # Arithmetic: inherit from operands
            result_type = left.ir_type

        dest = self._ssa.new_temp(result_type)
        self._emit(BinaryOp(dest=dest, op=op, left=left, right=right))
        return dest

    def visit_unary_expr(self, expr: UnaryExpr) -> IRValue:
        """
        Generate IR for a unary expression.

        Emits operand, then unary operation.
        """
        operand = expr.operand.accept(self)

        op = UNARY_OP_MAP.get(expr.operator)
        if op is None:
            raise RuntimeError(f"Unknown unary operator: {expr.operator}")

        # Result type: NOT produces bool, NEG preserves type
        if op == OpCode.NOT:
            result_type = IRType.BOOL
        else:
            result_type = operand.ir_type

        dest = self._ssa.new_temp(result_type)
        self._emit(UnaryOp(dest=dest, op=op, operand=operand))
        return dest

    def visit_grouping_expr(self, expr: GroupingExpr) -> IRValue:
        """Generate IR for a grouping expression (just visit inner)."""
        return expr.expression.accept(self)

    def visit_call_expr(self, expr: CallExpr) -> IRValue:
        """
        Generate IR for a function call.

        Emits arguments, then call instruction.
        """
        # Evaluate arguments
        args = [arg.accept(self) for arg in expr.arguments]

        # Determine return type (should be available from semantic analysis)
        # For built-ins, we know the types
        if expr.callee == "print":
            return_type = IRType.VOID
        elif expr.callee == "input":
            return_type = IRType.STRING
        elif expr.callee == "len":
            return_type = IRType.INT
        else:
            # User-defined function - get from resolved_type if available
            if expr.resolved_type is not None:
                return_type = type_annotation_to_ir_type(expr.resolved_type)
            else:
                return_type = IRType.INT  # Default fallback

        # Emit call
        if return_type == IRType.VOID:
            self._emit(Call(dest=None, function=expr.callee, arguments=args))
            # Return a dummy value for void
            return make_constant(0, IRType.VOID)
        else:
            dest = self._ssa.new_temp(return_type)
            self._emit(Call(dest=dest, function=expr.callee, arguments=args))
            return dest

    def visit_assignment_expr(self, expr: AssignmentExpr) -> IRValue:
        """
        Generate IR for an assignment expression.

        Creates a new SSA version of the variable.
        """
        # Evaluate the right-hand side
        value = expr.value.accept(self)

        # Create new SSA version for the variable
        new_version = self._ssa.new_version(expr.name)

        # Emit copy instruction
        self._emit(Copy(dest=new_version, source=value))

        return new_version

    # =========================================================================
    # Statement Visitors (return None, emit instructions)
    # =========================================================================

    def visit_expr_stmt(self, stmt: ExprStmt) -> None:
        """Generate IR for an expression statement."""
        stmt.expression.accept(self)

    def visit_var_decl_stmt(self, stmt: VarDeclStmt) -> None:
        """
        Generate IR for a variable declaration.

        Creates initial SSA version (version 0) for the variable.
        """
        ir_type = type_annotation_to_ir_type(stmt.type_annotation)

        # Create the variable in SSA context
        var = self._ssa.new_variable(stmt.name, ir_type)

        if stmt.initializer is not None:
            # Evaluate initializer
            init_value = stmt.initializer.accept(self)
            # Emit copy/assignment
            self._emit(Copy(dest=var, source=init_value))
        else:
            # Uninitialized - emit a default value
            if ir_type == IRType.INT:
                self._emit(LoadConst(dest=var, value=0, value_type=ir_type))
            elif ir_type == IRType.FLOAT:
                self._emit(LoadConst(dest=var, value=0.0, value_type=ir_type))
            elif ir_type == IRType.BOOL:
                self._emit(LoadConst(dest=var, value=False, value_type=ir_type))
            elif ir_type == IRType.STRING:
                self._emit(LoadConst(dest=var, value="", value_type=ir_type))

    def visit_block_stmt(self, stmt: BlockStmt) -> None:
        """Generate IR for a block of statements."""
        for s in stmt.statements:
            # Don't emit into terminated blocks
            if self._is_block_terminated():
                break
            s.accept(self)

    def visit_if_stmt(self, stmt: IfStmt) -> None:
        """
        Generate IR for an if statement.

        Creates basic blocks for then, else, and merge.
        Inserts phi functions at merge point if needed.
        """
        # Evaluate condition
        cond = stmt.condition.accept(self)

        # Create blocks
        then_block = self._new_block("then")
        merge_block = self._new_block("merge")

        if stmt.else_branch is not None:
            else_block = self._new_block("else")
        else:
            else_block = merge_block

        # Emit conditional branch
        self._cfg_builder.emit_branch(cond, then_block.label, else_block.label)

        # Save variable versions before branches for phi insertion
        versions_before = self._ssa.get_scope_snapshot()

        # Generate then branch
        self._position_at(then_block)
        stmt.then_branch.accept(self)
        versions_after_then = self._ssa.get_scope_snapshot()
        then_exit_label = self._current_block_label()

        if not self._is_block_terminated():
            self._cfg_builder.emit_jump(merge_block.label)

        # Generate else branch if present
        if stmt.else_branch is not None:
            # DON'T restore SSA version counters - we want new versions in else
            # But we need to track which variables map to which versions from each path
            # Store the current versions (after then branch)
            then_final_versions = self._ssa.get_scope_snapshot()

            # For the else branch, we need to generate code that sees the
            # original pre-if versions when reading variables, but creates
            # new unique versions when writing
            self._position_at(else_block)
            stmt.else_branch.accept(self)
            versions_after_else = self._ssa.get_scope_snapshot()
            else_exit_label = self._current_block_label()

            if not self._is_block_terminated():
                self._cfg_builder.emit_jump(merge_block.label)
        else:
            versions_after_else = versions_before
            else_exit_label = ""

        # Position at merge block
        self._position_at(merge_block)

        # Insert phi functions for variables modified in either branch
        self._insert_phi_functions_v2(
            versions_before,
            versions_after_then, then_exit_label,
            versions_after_else, else_exit_label,
            stmt.else_branch is not None
        )

    def visit_while_stmt(self, stmt: WhileStmt) -> None:
        """
        Generate IR for a while loop.

        Creates basic blocks for header (condition), body, and exit.
        Inserts phi functions at loop header.

        The key insight is that we need to:
        1. Generate the body first to find which variables are modified
        2. Insert phi functions at the header
        3. Update the SSA versions so the condition uses the phi results
        4. Generate the condition using the phi versions
        """
        # Create blocks
        header_block = self._new_block("loop_header")
        body_block = self._new_block("loop_body")
        exit_block = self._new_block("loop_exit")

        # Save versions before loop and entry label
        versions_before = self._ssa.get_scope_snapshot()
        entry_label = self._current_block_label()

        # Jump from entry to header
        self._cfg_builder.emit_jump(header_block.label)

        # === PASS 1: Generate body to find modified variables ===
        # We need to know which variables are modified in the body
        # Save the current state so we can "replay" body generation
        saved_ssa_state = self._ssa.get_scope_snapshot()

        # Position at body block and generate body (temporary, to find modified vars)
        self._position_at(body_block)
        stmt.body.accept(self)
        versions_after_body = self._ssa.get_scope_snapshot()

        # Find which variables were modified
        modified_vars = self._get_modified_variables(versions_before, versions_after_body)

        # === PASS 2: Regenerate with correct phi functions ===
        # Clear the body block - we'll regenerate it
        body_block.instructions = []

        # Position at header block
        self._position_at(header_block)

        # Create phi functions for modified variables and update SSA versions
        phi_var_versions = {}  # Maps var_name -> phi_dest version
        for var_name in modified_vars:
            if var_name not in versions_before:
                continue

            ir_type = self._get_var_type(var_name)

            # Create phi destination (new version)
            phi_dest = self._ssa.new_version(var_name)
            phi_var_versions[var_name] = phi_dest.version

            # Entry version (from before the loop)
            entry_version = IRValue(name=var_name, version=versions_before[var_name], ir_type=ir_type)

            # Body version (we'll patch this later after regenerating the body)
            # For now, use a placeholder that we'll update
            body_version = IRValue(name=var_name, version=versions_after_body[var_name], ir_type=ir_type)

            phi = Phi(
                dest=phi_dest,
                sources=[
                    PhiSource(entry_version, entry_label),
                    PhiSource(body_version, body_block.label)  # Will be patched
                ]
            )
            self._emit(phi)

        # Now generate the condition - it will use the phi versions because
        # we called new_version for each modified variable
        cond = stmt.condition.accept(self)

        # Branch: if true goto body, else goto exit
        self._cfg_builder.emit_branch(cond, body_block.label, exit_block.label)

        # === Regenerate body with correct versions ===
        self._position_at(body_block)

        # Reset SSA versions for modified vars to use phi versions
        for var_name, phi_version in phi_var_versions.items():
            self._ssa.set_version(var_name, phi_version)

        # Regenerate body
        stmt.body.accept(self)
        final_versions = self._ssa.get_scope_snapshot()
        body_exit_label = self._current_block_label()

        if not self._is_block_terminated():
            self._cfg_builder.emit_jump(header_block.label)

        # === Patch phi functions with correct body exit versions ===
        for instr in header_block.instructions:
            if isinstance(instr, Phi):
                var_name = instr.dest.name
                if var_name in final_versions:
                    # Update the body source with the final version
                    for source in instr.sources:
                        if source.block == body_block.label:
                            source.value = IRValue(
                                name=var_name,
                                version=final_versions[var_name],
                                ir_type=instr.dest.ir_type
                            )
                    # Also update block label if body was extended
                    for source in instr.sources:
                        if source.block == body_block.label:
                            source.block = body_exit_label

        # Position at exit block
        # Restore phi versions so code after the loop uses the phi results
        for var_name, phi_version in phi_var_versions.items():
            self._ssa.set_version(var_name, phi_version)

        self._position_at(exit_block)

    def visit_return_stmt(self, stmt: ReturnStmt) -> None:
        """Generate IR for a return statement."""
        if stmt.value is not None:
            value = stmt.value.accept(self)
            self._cfg_builder.emit_return(value)
        else:
            self._cfg_builder.emit_return(None)

    # =========================================================================
    # Declaration Visitors
    # =========================================================================

    def visit_function_decl(self, decl: FunctionDecl) -> None:
        """
        Generate IR for a function declaration.

        Creates a new IRFunction with its CFG.
        """
        # Create new SSA context and CFG builder for this function
        self._ssa = SSANameGenerator()
        self._cfg_builder = CFGBuilder()

        # Determine return type
        return_type = type_annotation_to_ir_type(decl.return_type)
        self._current_return_type = return_type

        # Create function
        ir_func = IRFunction(
            name=decl.name,
            return_type=return_type
        )

        # Add parameters
        for param in decl.parameters:
            param_type = type_annotation_to_ir_type(param.type_annotation)
            ir_func.parameters.append(IRParameter(param.name, param_type))

            # Register parameter in SSA context (version 0)
            self._ssa.new_variable(param.name, param_type)

        # Create entry block
        entry = self._new_block("entry")
        self._cfg_builder.set_entry(entry.label)
        ir_func.entry_block = entry.label
        self._position_at(entry)

        # Generate function body
        decl.body.accept(self)

        # Ensure function has a terminator (add implicit return for void)
        if not self._is_block_terminated():
            if return_type == IRType.VOID:
                self._cfg_builder.emit_return(None)
            else:
                # Non-void function without return - semantic analysis should catch this
                # but add a default return just in case
                default_val = self._ssa.new_temp(return_type)
                if return_type == IRType.INT:
                    self._emit(LoadConst(dest=default_val, value=0, value_type=return_type))
                elif return_type == IRType.FLOAT:
                    self._emit(LoadConst(dest=default_val, value=0.0, value_type=return_type))
                elif return_type == IRType.BOOL:
                    self._emit(LoadConst(dest=default_val, value=False, value_type=return_type))
                self._cfg_builder.emit_return(default_val)

        # Finalize CFG
        cfg = self._cfg_builder.finalize()
        ir_func.blocks = cfg.blocks

        # Store function and reset context
        self._current_function = ir_func
        self._module.add_function(ir_func)

    def visit_program(self, program: Program) -> None:
        """Generate IR for the complete program."""
        # Process global variable declarations first
        for decl in program.declarations:
            if isinstance(decl, VarDeclStmt):
                # Handle global variables (stored in module.globals)
                ir_type = type_annotation_to_ir_type(decl.type_annotation)
                if decl.initializer is not None:
                    # For now, only support constant initializers for globals
                    if isinstance(decl.initializer, LiteralExpr):
                        self._module.globals[decl.name] = IRValue(
                            name=decl.name,
                            version=0,
                            ir_type=ir_type,
                            is_constant=decl.is_const,
                            constant_value=decl.initializer.value
                        )
                else:
                    self._module.globals[decl.name] = IRValue(
                        name=decl.name,
                        version=0,
                        ir_type=ir_type
                    )

        # Process function declarations
        for decl in program.declarations:
            if isinstance(decl, FunctionDecl):
                decl.accept(self)

    # =========================================================================
    # Phi Function Helpers
    # =========================================================================

    def _insert_phi_functions(
        self,
        versions_before: Dict[str, int],
        versions_after_then: Dict[str, int],
        then_label: str,
        versions_after_else: Dict[str, int],
        else_label: str,
        has_else: bool
    ) -> None:
        """
        Insert phi functions at merge point for if statements.

        Creates phi functions for any variables whose versions differ
        between the then and else branches.
        """
        modified_vars = self._get_modified_variables(
            versions_before,
            versions_after_then
        )

        if has_else:
            modified_vars |= self._get_modified_variables(
                versions_before,
                versions_after_else
            )

        for var_name in modified_vars:
            if var_name not in versions_before:
                continue

            ir_type = self._get_var_type(var_name)

            # Get versions from each branch
            then_version = versions_after_then.get(var_name, versions_before[var_name])
            else_version = versions_after_else.get(var_name, versions_before[var_name])

            # Only insert phi if versions differ
            if then_version != else_version:
                phi_dest = self._ssa.new_version(var_name)

                then_val = IRValue(name=var_name, version=then_version, ir_type=ir_type)
                else_val = IRValue(name=var_name, version=else_version, ir_type=ir_type)

                sources = [PhiSource(then_val, then_label)]
                if has_else and else_label:
                    sources.append(PhiSource(else_val, else_label))

                self._emit(Phi(dest=phi_dest, sources=sources))

    def _insert_phi_functions_v2(
        self,
        versions_before: Dict[str, int],
        versions_after_then: Dict[str, int],
        then_label: str,
        versions_after_else: Dict[str, int],
        else_label: str,
        has_else: bool
    ) -> None:
        """
        Insert phi functions at merge point for if statements (v2).

        This version handles the case where both branches may modify
        the same variable with different versions because we don't
        reset SSA counters between branches.
        """
        modified_vars = self._get_modified_variables(
            versions_before,
            versions_after_then
        )

        if has_else:
            modified_vars |= self._get_modified_variables(
                versions_before,
                versions_after_else
            )

        for var_name in modified_vars:
            if var_name not in versions_before:
                continue

            ir_type = self._get_var_type(var_name)

            # Get versions from each branch
            then_version = versions_after_then.get(var_name, versions_before[var_name])
            else_version = versions_after_else.get(var_name, versions_before[var_name])
            before_version = versions_before[var_name]

            # Insert phi if either branch modified the variable
            # (versions differ from before, and we have both branches)
            then_modified = then_version != before_version
            else_modified = else_version != before_version

            if has_else and (then_modified or else_modified):
                # Both branches exist, need phi
                phi_dest = self._ssa.new_version(var_name)

                then_val = IRValue(name=var_name, version=then_version, ir_type=ir_type)
                else_val = IRValue(name=var_name, version=else_version, ir_type=ir_type)

                sources = [
                    PhiSource(then_val, then_label),
                    PhiSource(else_val, else_label)
                ]

                self._emit(Phi(dest=phi_dest, sources=sources))
            elif then_modified and not has_else:
                # Only then branch, no else - need phi between then and before
                phi_dest = self._ssa.new_version(var_name)

                then_val = IRValue(name=var_name, version=then_version, ir_type=ir_type)
                before_val = IRValue(name=var_name, version=before_version, ir_type=ir_type)

                # For if without else, the "else" path comes from the entry block
                sources = [
                    PhiSource(then_val, then_label),
                    PhiSource(before_val, else_label) if else_label else PhiSource(before_val, "entry")
                ]

                self._emit(Phi(dest=phi_dest, sources=sources))

    def _get_modified_variables(
        self,
        before: Dict[str, int],
        after: Dict[str, int]
    ) -> set:
        """Find variables whose versions changed between snapshots."""
        modified = set()
        for var_name, version in after.items():
            if var_name in before and before[var_name] != version:
                modified.add(var_name)
        return modified

    def _get_var_type(self, var_name: str) -> IRType:
        """Get the IR type of a variable."""
        if self._ssa.has_variable(var_name):
            return self._ssa.get_current(var_name).ir_type
        return IRType.INT  # Default


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_ir(program: Program) -> IRModule:
    """
    Generate IR from a typed AST program.

    Args:
        program: The typed AST

    Returns:
        IRModule containing the generated IR
    """
    generator = IRGenerator()
    return generator.generate(program)


def generate_ir_from_source(source: str) -> IRModule:
    """
    Lex, parse, analyze, and generate IR from Toy source code.

    Args:
        source: Toy source code as a string

    Returns:
        IRModule containing the generated IR

    Raises:
        LexerError, ParserError, SemanticError: If compilation fails
    """
    from src.semantic.semantic_analyzer import analyze_source
    from src.parser.parser import parse_source

    # Parse and analyze
    program = parse_source(source)
    analyze_source(source)  # Run semantic analysis to type-check

    # Generate IR
    return generate_ir(program)
