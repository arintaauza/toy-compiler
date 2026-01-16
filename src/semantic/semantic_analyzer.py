"""
Semantic analyzer for the Luna compiler.

The semantic analyzer is the main entry point for semantic analysis.
It orchestrates:
1. Building the symbol table (declaration pass)
2. Type checking (validation pass)
3. Additional semantic validations

Usage:
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)  # Raises SemanticError if invalid
"""

from typing import List, Optional
from src.parser.ast_nodes import (
    Program,
    FunctionDecl,
    VarDeclStmt,
    BlockStmt,
    Statement,
)
from src.semantic.types import (
    LunaType,
    FunctionType,
    INT, FLOAT, BOOL, STRING, VOID,
    type_from_annotation,
)
from src.semantic.symbol_table import (
    SymbolTable,
    Symbol,
    SymbolKind,
    create_symbol_table_with_builtins,
)
from src.semantic.type_checker import TypeChecker
from src.utils.error import SemanticError


class SemanticAnalyzer:
    """
    Performs complete semantic analysis on a Luna program.

    The analyzer runs multiple passes:
    1. Declaration pass: Build symbol table with all global declarations
    2. Type checking pass: Validate types throughout the program
    3. Validation pass: Check semantic rules (main function, etc.)
    """

    def __init__(self):
        """Initialize the semantic analyzer."""
        self.symbol_table: Optional[SymbolTable] = None
        self.errors: List[SemanticError] = []

    def analyze(self, program: Program) -> SymbolTable:
        """
        Perform semantic analysis on a program.

        Args:
            program: The parsed AST

        Returns:
            The symbol table with all declarations

        Raises:
            SemanticError: If any semantic errors are found
        """
        self.errors = []

        # Create symbol table with built-in functions
        self.symbol_table = create_symbol_table_with_builtins()

        # Pass 1: Register all global declarations
        self._declaration_pass(program)

        # Pass 2: Type check the program
        self._type_checking_pass(program)

        # Pass 3: Validate semantic rules
        self._validation_pass(program)

        # Raise first error if any
        if self.errors:
            raise self.errors[0]

        return self.symbol_table

    def _declaration_pass(self, program: Program) -> None:
        """
        First pass: Register all top-level declarations.

        This pass:
        - Registers all function declarations in the global scope
        - Registers global variables/constants
        - Does NOT type check function bodies yet
        """
        for decl in program.declarations:
            if isinstance(decl, FunctionDecl):
                self._declare_function(decl)
            elif isinstance(decl, VarDeclStmt):
                self._declare_global_variable(decl)

    def _declare_function(self, decl: FunctionDecl) -> None:
        """Register a function in the global symbol table."""
        # Build function type
        param_types = [
            type_from_annotation(p.type_annotation)
            for p in decl.parameters
        ]
        return_type = type_from_annotation(decl.return_type)

        func_type = FunctionType(
            parameter_types=param_types,
            return_type=return_type
        )

        symbol = Symbol(
            name=decl.name,
            type=func_type,
            kind=SymbolKind.FUNCTION,
            line=decl.line,
            column=decl.column,
            is_initialized=True
        )

        if not self.symbol_table.define(symbol):
            self._error(
                f"Function '{decl.name}' is already defined",
                decl.line, decl.column
            )

    def _declare_global_variable(self, stmt: VarDeclStmt) -> None:
        """Register a global variable in the symbol table."""
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
                f"Global variable '{stmt.name}' is already defined",
                stmt.line, stmt.column
            )

    def _type_checking_pass(self, program: Program) -> None:
        """
        Second pass: Type check the entire program.

        Uses the TypeChecker visitor to validate types.
        """
        type_checker = TypeChecker(self.symbol_table)
        errors = type_checker.check(program)
        self.errors.extend(errors)

    def _validation_pass(self, program: Program) -> None:
        """
        Third pass: Validate semantic rules.

        Checks:
        - main() function exists with correct signature
        - Non-void functions have return statements
        """
        self._validate_main_function(program)
        self._validate_return_paths(program)

    def _validate_main_function(self, program: Program) -> None:
        """Validate that main() function exists with correct signature."""
        main_symbol = self.symbol_table.lookup("main")

        if main_symbol is None:
            self._error("Program must have a 'main' function", 0, 0)
            return

        if not main_symbol.is_function:
            self._error("'main' must be a function", main_symbol.line, main_symbol.column)
            return

        func_type = main_symbol.type
        if not isinstance(func_type, FunctionType):
            return

        # main() should return int
        if func_type.return_type != INT:
            self._error(
                f"Function 'main' must return 'int', not '{func_type.return_type}'",
                main_symbol.line, main_symbol.column
            )

        # main() should have no parameters
        if len(func_type.parameter_types) > 0:
            self._error(
                "Function 'main' should not have parameters",
                main_symbol.line, main_symbol.column
            )

    def _validate_return_paths(self, program: Program) -> None:
        """
        Validate that non-void functions have return statements.

        Note: This is a simplified check. A full implementation would
        do control flow analysis to ensure ALL paths return.
        """
        for decl in program.declarations:
            if isinstance(decl, FunctionDecl):
                return_type = type_from_annotation(decl.return_type)
                if return_type != VOID:
                    if not self._has_return_statement(decl.body):
                        self._error(
                            f"Function '{decl.name}' may not return a value on all paths",
                            decl.line, decl.column
                        )

    def _has_return_statement(self, block: BlockStmt) -> bool:
        """
        Check if a block has a return statement.

        This is a simplified check - a full implementation would
        analyze all control flow paths.
        """
        from src.parser.ast_nodes import ReturnStmt, IfStmt, WhileStmt

        for stmt in block.statements:
            if isinstance(stmt, ReturnStmt):
                return True
            elif isinstance(stmt, IfStmt):
                # If both branches return, the if statement returns
                if stmt.else_branch is not None:
                    then_returns = (
                        isinstance(stmt.then_branch, BlockStmt) and
                        self._has_return_statement(stmt.then_branch)
                    )
                    else_returns = (
                        isinstance(stmt.else_branch, BlockStmt) and
                        self._has_return_statement(stmt.else_branch)
                    ) or (
                        isinstance(stmt.else_branch, IfStmt) and
                        self._if_returns(stmt.else_branch)
                    )
                    if then_returns and else_returns:
                        return True
            elif isinstance(stmt, BlockStmt):
                if self._has_return_statement(stmt):
                    return True

        return False

    def _if_returns(self, if_stmt) -> bool:
        """Check if an if statement always returns."""
        from src.parser.ast_nodes import IfStmt, BlockStmt

        if if_stmt.else_branch is None:
            return False

        then_returns = (
            isinstance(if_stmt.then_branch, BlockStmt) and
            self._has_return_statement(if_stmt.then_branch)
        )

        if isinstance(if_stmt.else_branch, BlockStmt):
            else_returns = self._has_return_statement(if_stmt.else_branch)
        elif isinstance(if_stmt.else_branch, IfStmt):
            else_returns = self._if_returns(if_stmt.else_branch)
        else:
            else_returns = False

        return then_returns and else_returns

    def _error(self, message: str, line: int, column: int) -> None:
        """Record a semantic error."""
        self.errors.append(SemanticError(message, line, column))


# =============================================================================
# Convenience Functions
# =============================================================================

def analyze(program: Program) -> SymbolTable:
    """
    Perform semantic analysis on a program.

    Args:
        program: The parsed AST

    Returns:
        The symbol table with all declarations

    Raises:
        SemanticError: If any semantic errors are found
    """
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)


def analyze_source(source: str) -> SymbolTable:
    """
    Lex, parse, and analyze Luna source code.

    Args:
        source: Luna source code as a string

    Returns:
        The symbol table with all declarations

    Raises:
        LexerError: If a lexical error is encountered
        ParserError: If a syntax error is encountered
        SemanticError: If a semantic error is encountered
    """
    from src.parser.parser import parse_source
    program = parse_source(source)
    return analyze(program)
