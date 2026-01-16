"""
Type checker for the Luna compiler.

The type checker traverses the AST and verifies that all operations
are type-safe according to Luna's type system. It:
- Validates expression types
- Checks assignment compatibility
- Verifies function call arguments
- Ensures control flow conditions are boolean
- Validates return statement types
"""

from typing import Optional, List
from src.parser.ast_nodes import (
    ASTVisitor,
    # Expressions
    Expression,
    LiteralExpr,
    VariableExpr,
    BinaryExpr,
    UnaryExpr,
    GroupingExpr,
    CallExpr,
    AssignmentExpr,
    # Statements
    Statement,
    ExprStmt,
    VarDeclStmt,
    BlockStmt,
    IfStmt,
    WhileStmt,
    ReturnStmt,
    # Declarations
    Parameter,
    FunctionDecl,
    Program,
)
from src.semantic.types import (
    LunaType,
    FunctionType,
    INT, FLOAT, BOOL, STRING, VOID,
    type_from_annotation,
    get_binary_result_type,
    get_unary_result_type,
    format_type_mismatch,
)
from src.semantic.symbol_table import (
    SymbolTable,
    Symbol,
    SymbolKind,
)
from src.utils.error import SemanticError


class TypeChecker(ASTVisitor):
    """
    Visitor that performs type checking on the AST.

    The type checker:
    1. Resolves variable references to their declared types
    2. Validates that operators are applied to compatible types
    3. Checks that function calls have correct argument types
    4. Ensures return types match function declarations
    5. Validates control flow conditions are boolean

    Attributes:
        symbol_table: The symbol table for looking up declarations
        current_function: The function currently being checked (for return validation)
        errors: List of semantic errors found during checking
    """

    def __init__(self, symbol_table: SymbolTable):
        """
        Initialize the type checker.

        Args:
            symbol_table: Symbol table with all declarations
        """
        self.symbol_table = symbol_table
        self.current_function: Optional[FunctionDecl] = None
        self.current_function_type: Optional[LunaType] = None
        self.errors: List[SemanticError] = []

    def check(self, program: Program) -> List[SemanticError]:
        """
        Type check a complete program.

        Args:
            program: The program AST to check

        Returns:
            List of semantic errors found
        """
        self.errors = []
        program.accept(self)
        return self.errors

    def _error(self, message: str, line: int = 0, column: int = 0) -> SemanticError:
        """Create and record a semantic error."""
        error = SemanticError(message, line, column)
        self.errors.append(error)
        return error

    # =========================================================================
    # Expression Type Checking
    # =========================================================================

    def visit_literal_expr(self, expr: LiteralExpr) -> LunaType:
        """
        Type check a literal expression.

        Literals have known types based on their literal_type.
        """
        type_map = {
            "INT": INT,
            "FLOAT": FLOAT,
            "BOOL": BOOL,
            "STRING": STRING,
        }

        if expr.literal_type is not None:
            luna_type = type_from_annotation(expr.literal_type)
            expr.resolved_type = luna_type
            return luna_type

        # Fallback: infer from value type
        if isinstance(expr.value, bool):
            expr.resolved_type = BOOL
            return BOOL
        elif isinstance(expr.value, int):
            expr.resolved_type = INT
            return INT
        elif isinstance(expr.value, float):
            expr.resolved_type = FLOAT
            return FLOAT
        elif isinstance(expr.value, str):
            expr.resolved_type = STRING
            return STRING

        self._error(f"Unknown literal type for value: {expr.value}", expr.line, expr.column)
        return VOID

    def visit_variable_expr(self, expr: VariableExpr) -> LunaType:
        """
        Type check a variable reference.

        Looks up the variable in the symbol table and returns its type.
        """
        symbol = self.symbol_table.lookup(expr.name)

        if symbol is None:
            self._error(f"Undefined variable '{expr.name}'", expr.line, expr.column)
            return VOID

        expr.resolved_type = symbol.type
        return symbol.type

    def visit_binary_expr(self, expr: BinaryExpr) -> LunaType:
        """
        Type check a binary expression.

        Validates that the operator can be applied to the operand types
        and determines the result type.
        """
        left_type = expr.left.accept(self)
        right_type = expr.right.accept(self)

        result_type = get_binary_result_type(expr.operator, left_type, right_type)

        if result_type is None:
            self._error(
                f"Invalid operand types for '{expr.operator}': "
                f"'{left_type}' and '{right_type}'",
                expr.line, expr.column
            )
            return VOID

        expr.resolved_type = result_type
        return result_type

    def visit_unary_expr(self, expr: UnaryExpr) -> LunaType:
        """
        Type check a unary expression.

        Validates that the operator can be applied to the operand type.
        """
        operand_type = expr.operand.accept(self)
        result_type = get_unary_result_type(expr.operator, operand_type)

        if result_type is None:
            self._error(
                f"Invalid operand type for '{expr.operator}': '{operand_type}'",
                expr.line, expr.column
            )
            return VOID

        expr.resolved_type = result_type
        return result_type

    def visit_grouping_expr(self, expr: GroupingExpr) -> LunaType:
        """Type check a grouping expression (parenthesized expression)."""
        inner_type = expr.expression.accept(self)
        expr.resolved_type = inner_type
        return inner_type

    def visit_call_expr(self, expr: CallExpr) -> LunaType:
        """
        Type check a function call expression.

        Validates that:
        1. The function exists
        2. The correct number of arguments is provided
        3. Each argument type matches the parameter type
        """
        # Look up the function
        symbol = self.symbol_table.lookup(expr.callee)

        if symbol is None:
            self._error(f"Undefined function '{expr.callee}'", expr.line, expr.column)
            return VOID

        if not symbol.is_function:
            self._error(f"'{expr.callee}' is not a function", expr.line, expr.column)
            return VOID

        func_type = symbol.type
        if not isinstance(func_type, FunctionType):
            self._error(f"'{expr.callee}' is not callable", expr.line, expr.column)
            return VOID

        # Special handling for print() - accepts any single argument
        if expr.callee == "print":
            if len(expr.arguments) != 1:
                self._error(
                    f"Function 'print' expects 1 argument but got {len(expr.arguments)}",
                    expr.line, expr.column
                )
            else:
                # Type check the argument but accept any type
                expr.arguments[0].accept(self)
            expr.resolved_type = VOID
            return VOID

        # Check argument count
        if len(expr.arguments) != len(func_type.parameter_types):
            self._error(
                f"Function '{expr.callee}' expects {len(func_type.parameter_types)} "
                f"argument(s) but got {len(expr.arguments)}",
                expr.line, expr.column
            )
            # Type check arguments anyway
            for arg in expr.arguments:
                arg.accept(self)
            expr.resolved_type = func_type.return_type
            return func_type.return_type

        # Check argument types
        for i, (arg, param_type) in enumerate(zip(expr.arguments, func_type.parameter_types)):
            arg_type = arg.accept(self)
            if arg_type != param_type:
                self._error(
                    f"Argument {i + 1} of '{expr.callee}' has wrong type: "
                    f"expected '{param_type}', got '{arg_type}'",
                    arg.line, arg.column
                )

        expr.resolved_type = func_type.return_type
        return func_type.return_type

    def visit_assignment_expr(self, expr: AssignmentExpr) -> LunaType:
        """
        Type check an assignment expression.

        Validates that:
        1. The variable exists
        2. The variable is not a constant
        3. The value type matches the variable type
        """
        # Look up the variable
        symbol = self.symbol_table.lookup(expr.name)

        if symbol is None:
            self._error(f"Undefined variable '{expr.name}'", expr.line, expr.column)
            value_type = expr.value.accept(self)
            return value_type

        # Check if assigning to a constant
        if symbol.is_const:
            self._error(
                f"Cannot assign to constant '{expr.name}'",
                expr.line, expr.column
            )

        # Check value type
        value_type = expr.value.accept(self)

        if value_type != symbol.type:
            self._error(
                f"Cannot assign '{value_type}' to variable '{expr.name}' of type '{symbol.type}'",
                expr.line, expr.column
            )

        expr.resolved_type = symbol.type
        return symbol.type

    # =========================================================================
    # Statement Type Checking
    # =========================================================================

    def visit_expr_stmt(self, stmt: ExprStmt) -> None:
        """Type check an expression statement."""
        stmt.expression.accept(self)

    def visit_var_decl_stmt(self, stmt: VarDeclStmt) -> None:
        """
        Type check a variable declaration.

        The symbol should already be in the symbol table (from declaration pass).
        Here we validate the initializer type matches the declared type.
        """
        if stmt.initializer is not None:
            init_type = stmt.initializer.accept(self)
            declared_type = type_from_annotation(stmt.type_annotation)

            if init_type != declared_type:
                self._error(
                    f"Cannot initialize variable '{stmt.name}' of type '{declared_type}' "
                    f"with value of type '{init_type}'",
                    stmt.line, stmt.column
                )

    def visit_block_stmt(self, stmt: BlockStmt) -> None:
        """Type check a block of statements."""
        # Enter a new scope
        self.symbol_table.enter_scope("block")

        # Process declarations in this block first (forward references)
        for s in stmt.statements:
            if isinstance(s, VarDeclStmt):
                self._declare_variable(s)

        # Type check all statements
        for s in stmt.statements:
            s.accept(self)

        # Exit the scope
        self.symbol_table.exit_scope()

    def visit_if_stmt(self, stmt: IfStmt) -> None:
        """
        Type check an if statement.

        Validates that the condition is a boolean expression.
        """
        condition_type = stmt.condition.accept(self)

        if condition_type != BOOL:
            self._error(
                f"If condition must be a boolean, got '{condition_type}'",
                stmt.condition.line, stmt.condition.column
            )

        # Type check branches
        stmt.then_branch.accept(self)
        if stmt.else_branch is not None:
            stmt.else_branch.accept(self)

    def visit_while_stmt(self, stmt: WhileStmt) -> None:
        """
        Type check a while statement.

        Validates that the condition is a boolean expression.
        """
        condition_type = stmt.condition.accept(self)

        if condition_type != BOOL:
            self._error(
                f"While condition must be a boolean, got '{condition_type}'",
                stmt.condition.line, stmt.condition.column
            )

        stmt.body.accept(self)

    def visit_return_stmt(self, stmt: ReturnStmt) -> None:
        """
        Type check a return statement.

        Validates that the return value type matches the function's return type.
        """
        if self.current_function_type is None:
            self._error("Return statement outside of function", stmt.line, stmt.column)
            return

        if stmt.value is not None:
            return_type = stmt.value.accept(self)

            if self.current_function_type == VOID:
                self._error(
                    "Cannot return a value from void function",
                    stmt.line, stmt.column
                )
            elif return_type != self.current_function_type:
                self._error(
                    f"Return type mismatch: expected '{self.current_function_type}', "
                    f"got '{return_type}'",
                    stmt.line, stmt.column
                )
        else:
            # Return without value
            if self.current_function_type != VOID:
                self._error(
                    f"Function must return a value of type '{self.current_function_type}'",
                    stmt.line, stmt.column
                )

    # =========================================================================
    # Declaration Type Checking
    # =========================================================================

    def visit_function_decl(self, decl: FunctionDecl) -> None:
        """
        Type check a function declaration.

        Sets up the function context and type checks the body.
        """
        # Save current function context
        prev_function = self.current_function
        prev_function_type = self.current_function_type

        self.current_function = decl
        self.current_function_type = type_from_annotation(decl.return_type)

        # Enter function scope
        self.symbol_table.enter_scope(f"function_{decl.name}")

        # Add parameters to scope
        for param in decl.parameters:
            param_type = type_from_annotation(param.type_annotation)
            symbol = Symbol(
                name=param.name,
                type=param_type,
                kind=SymbolKind.PARAMETER,
                line=param.line,
                column=param.column,
                is_initialized=True
            )
            if not self.symbol_table.define(symbol):
                self._error(
                    f"Duplicate parameter name '{param.name}'",
                    param.line, param.column
                )

        # Process local variable declarations first
        for stmt in decl.body.statements:
            if isinstance(stmt, VarDeclStmt):
                self._declare_variable(stmt)

        # Type check the function body
        for stmt in decl.body.statements:
            stmt.accept(self)

        # Exit function scope
        self.symbol_table.exit_scope()

        # Restore previous function context
        self.current_function = prev_function
        self.current_function_type = prev_function_type

    def visit_program(self, program: Program) -> None:
        """
        Type check a complete program.

        Type checks all declarations in the program.
        """
        for decl in program.declarations:
            decl.accept(self)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _declare_variable(self, stmt: VarDeclStmt) -> None:
        """
        Add a variable declaration to the current scope.

        Called during the declaration pass before type checking.
        """
        var_type = type_from_annotation(stmt.type_annotation)
        kind = SymbolKind.CONSTANT if stmt.is_const else SymbolKind.VARIABLE

        symbol = Symbol(
            name=stmt.name,
            type=var_type,
            kind=kind,
            line=stmt.line,
            column=stmt.column,
            is_initialized=stmt.initializer is not None
        )

        if not self.symbol_table.define(symbol):
            self._error(
                f"Variable '{stmt.name}' is already declared in this scope",
                stmt.line, stmt.column
            )
