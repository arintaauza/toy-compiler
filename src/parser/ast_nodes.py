"""
Abstract Syntax Tree (AST) node definitions for the Toy compiler.

This module defines all AST node types used to represent Toy programs
after parsing. The AST is a hierarchical representation of the source code
structure that can be traversed for semantic analysis and code generation.

Node Hierarchy:
- ASTNode (base)
  - Expression (base for expressions)
    - LiteralExpr (numbers, strings, booleans)
    - VariableExpr (variable references)
    - BinaryExpr (a + b, a && b, etc.)
    - UnaryExpr (-a, !b)
    - CallExpr (function calls)
    - GroupingExpr (parenthesized expressions)
    - AssignmentExpr (a = b)
  - Statement (base for statements)
    - ExprStmt (expression as statement)
    - VarDeclStmt (let/const declarations)
    - BlockStmt (compound statements)
    - IfStmt (if/else)
    - WhileStmt (while loops)
    - ReturnStmt (return)
  - Declaration (base for top-level declarations)
    - FunctionDecl (function definitions)
    - Program (root node)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, List, TYPE_CHECKING
from enum import Enum, auto

if TYPE_CHECKING:
    from src.lexer.token import Token


class TypeAnnotation(Enum):
    """Type annotations available in Toy."""
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    VOID = auto()

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return f"TypeAnnotation.{self.name}"


# =============================================================================
# Base Classes
# =============================================================================

@dataclass
class ASTNode(ABC):
    """
    Base class for all AST nodes.

    All nodes track their position in source code for error reporting.
    """
    line: int = 0
    column: int = 0

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        """Accept a visitor for traversal (Visitor pattern)."""
        pass

    def position_str(self) -> str:
        """Return a formatted position string for error messages."""
        return f"line {self.line}, column {self.column}"


@dataclass
class Expression(ASTNode):
    """Base class for all expression nodes."""

    # Type annotation set during semantic analysis
    resolved_type: Optional[TypeAnnotation] = field(default=None, compare=False)


@dataclass
class Statement(ASTNode):
    """Base class for all statement nodes."""
    pass


@dataclass
class Declaration(ASTNode):
    """Base class for top-level declarations."""
    pass


# =============================================================================
# Expression Nodes
# =============================================================================

@dataclass
class LiteralExpr(Expression):
    """
    Represents a literal value (number, string, boolean).

    Examples:
        42
        3.14
        "hello"
        true
        false
    """
    value: Any = None
    literal_type: Optional[TypeAnnotation] = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_literal_expr(self)

    def __repr__(self) -> str:
        return f"LiteralExpr({self.value!r}, {self.literal_type})"


@dataclass
class VariableExpr(Expression):
    """
    Represents a variable reference.

    Examples:
        x
        counter
        myVar
    """
    name: str = ""

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_variable_expr(self)

    def __repr__(self) -> str:
        return f"VariableExpr({self.name!r})"


@dataclass
class BinaryExpr(Expression):
    """
    Represents a binary operation.

    Examples:
        a + b
        x * y
        count < 10
        flag && condition
    """
    left: Expression = None
    operator: str = ""  # The operator symbol: +, -, *, /, %, ==, !=, <, >, <=, >=, &&, ||
    right: Expression = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_expr(self)

    def __repr__(self) -> str:
        return f"BinaryExpr({self.left!r} {self.operator} {self.right!r})"


@dataclass
class UnaryExpr(Expression):
    """
    Represents a unary operation.

    Examples:
        -x
        !flag
    """
    operator: str = ""  # The operator symbol: -, !
    operand: Expression = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_unary_expr(self)

    def __repr__(self) -> str:
        return f"UnaryExpr({self.operator}{self.operand!r})"


@dataclass
class GroupingExpr(Expression):
    """
    Represents a parenthesized expression.

    Examples:
        (a + b)
        (x * (y + z))
    """
    expression: Expression = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_grouping_expr(self)

    def __repr__(self) -> str:
        return f"GroupingExpr({self.expression!r})"


@dataclass
class CallExpr(Expression):
    """
    Represents a function call.

    Examples:
        print("hello")
        add(1, 2)
        fibonacci(n - 1)
    """
    callee: str = ""  # Function name
    arguments: List[Expression] = field(default_factory=list)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_call_expr(self)

    def __repr__(self) -> str:
        args = ", ".join(repr(arg) for arg in self.arguments)
        return f"CallExpr({self.callee}({args}))"


@dataclass
class AssignmentExpr(Expression):
    """
    Represents an assignment expression.

    Note: In Toy, assignment is an expression that returns the assigned value.

    Examples:
        x = 42
        y = x + 1
    """
    name: str = ""
    value: Expression = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assignment_expr(self)

    def __repr__(self) -> str:
        return f"AssignmentExpr({self.name} = {self.value!r})"


# =============================================================================
# Statement Nodes
# =============================================================================

@dataclass
class ExprStmt(Statement):
    """
    Represents an expression used as a statement.

    Examples:
        print("hello");
        x = 42;
        add(1, 2);
    """
    expression: Expression = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_expr_stmt(self)

    def __repr__(self) -> str:
        return f"ExprStmt({self.expression!r})"


@dataclass
class VarDeclStmt(Statement):
    """
    Represents a variable or constant declaration.

    Examples:
        let x: int = 42;
        let name: string;
        const PI: float = 3.14;
    """
    name: str = ""
    type_annotation: Optional[TypeAnnotation] = None
    initializer: Optional[Expression] = None
    is_const: bool = False

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_var_decl_stmt(self)

    def __repr__(self) -> str:
        keyword = "const" if self.is_const else "let"
        init = f" = {self.initializer!r}" if self.initializer else ""
        return f"VarDeclStmt({keyword} {self.name}: {self.type_annotation}{init})"


@dataclass
class BlockStmt(Statement):
    """
    Represents a block of statements enclosed in braces.

    Examples:
        {
            let x: int = 1;
            print(x);
        }
    """
    statements: List[Statement] = field(default_factory=list)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_block_stmt(self)

    def __repr__(self) -> str:
        return f"BlockStmt({len(self.statements)} statements)"


@dataclass
class IfStmt(Statement):
    """
    Represents an if/else statement.

    Examples:
        if x > 0 { print("positive"); }
        if condition { ... } else { ... }
        if a { ... } else if b { ... } else { ... }
    """
    condition: Expression = None
    then_branch: Statement = None  # Usually a BlockStmt
    else_branch: Optional[Statement] = None  # BlockStmt or another IfStmt (else if)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_if_stmt(self)

    def __repr__(self) -> str:
        else_part = f" else {self.else_branch!r}" if self.else_branch else ""
        return f"IfStmt(if {self.condition!r} {self.then_branch!r}{else_part})"


@dataclass
class WhileStmt(Statement):
    """
    Represents a while loop.

    Examples:
        while i < 10 { i = i + 1; }
        while true { ... }
    """
    condition: Expression = None
    body: Statement = None  # Usually a BlockStmt

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_while_stmt(self)

    def __repr__(self) -> str:
        return f"WhileStmt(while {self.condition!r} {self.body!r})"


@dataclass
class ReturnStmt(Statement):
    """
    Represents a return statement.

    Examples:
        return;
        return 42;
        return x + y;
    """
    value: Optional[Expression] = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_return_stmt(self)

    def __repr__(self) -> str:
        if self.value:
            return f"ReturnStmt(return {self.value!r})"
        return "ReturnStmt(return)"


# =============================================================================
# Declaration Nodes
# =============================================================================

@dataclass
class Parameter:
    """
    Represents a function parameter.

    Examples:
        a: int
        name: string
    """
    name: str = ""
    type_annotation: TypeAnnotation = None
    line: int = 0
    column: int = 0

    def __repr__(self) -> str:
        return f"Parameter({self.name}: {self.type_annotation})"


@dataclass
class FunctionDecl(Declaration):
    """
    Represents a function declaration.

    Examples:
        fn add(a: int, b: int) -> int { return a + b; }
        fn main() -> int { return 0; }
        fn greet() -> void { print("hello"); }
    """
    name: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: TypeAnnotation = None
    body: BlockStmt = None

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_function_decl(self)

    def __repr__(self) -> str:
        params = ", ".join(repr(p) for p in self.parameters)
        return f"FunctionDecl(fn {self.name}({params}) -> {self.return_type})"


@dataclass
class Program(Declaration):
    """
    Represents a complete Toy program (root of the AST).

    A program consists of:
    - Global variable/constant declarations
    - Function declarations
    """
    declarations: List[Declaration] = field(default_factory=list)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_program(self)

    @property
    def functions(self) -> List[FunctionDecl]:
        """Return all function declarations in the program."""
        return [d for d in self.declarations if isinstance(d, FunctionDecl)]

    @property
    def global_variables(self) -> List[VarDeclStmt]:
        """Return all global variable declarations in the program."""
        return [d for d in self.declarations if isinstance(d, VarDeclStmt)]

    def __repr__(self) -> str:
        return f"Program({len(self.declarations)} declarations)"


# =============================================================================
# Visitor Pattern
# =============================================================================

class ASTVisitor(ABC):
    """
    Abstract visitor for traversing AST nodes.

    Implement this class to perform operations on the AST,
    such as type checking, code generation, or pretty printing.
    """

    # Expression visitors
    @abstractmethod
    def visit_literal_expr(self, expr: LiteralExpr) -> Any:
        pass

    @abstractmethod
    def visit_variable_expr(self, expr: VariableExpr) -> Any:
        pass

    @abstractmethod
    def visit_binary_expr(self, expr: BinaryExpr) -> Any:
        pass

    @abstractmethod
    def visit_unary_expr(self, expr: UnaryExpr) -> Any:
        pass

    @abstractmethod
    def visit_grouping_expr(self, expr: GroupingExpr) -> Any:
        pass

    @abstractmethod
    def visit_call_expr(self, expr: CallExpr) -> Any:
        pass

    @abstractmethod
    def visit_assignment_expr(self, expr: AssignmentExpr) -> Any:
        pass

    # Statement visitors
    @abstractmethod
    def visit_expr_stmt(self, stmt: ExprStmt) -> Any:
        pass

    @abstractmethod
    def visit_var_decl_stmt(self, stmt: VarDeclStmt) -> Any:
        pass

    @abstractmethod
    def visit_block_stmt(self, stmt: BlockStmt) -> Any:
        pass

    @abstractmethod
    def visit_if_stmt(self, stmt: IfStmt) -> Any:
        pass

    @abstractmethod
    def visit_while_stmt(self, stmt: WhileStmt) -> Any:
        pass

    @abstractmethod
    def visit_return_stmt(self, stmt: ReturnStmt) -> Any:
        pass

    # Declaration visitors
    @abstractmethod
    def visit_function_decl(self, decl: FunctionDecl) -> Any:
        pass

    @abstractmethod
    def visit_program(self, program: Program) -> Any:
        pass


# =============================================================================
# AST Pretty Printer
# =============================================================================

class ASTPrinter(ASTVisitor):
    """
    Visitor that produces a formatted string representation of the AST.

    Usage:
        printer = ASTPrinter()
        result = printer.print(ast)
        print(result)
    """

    def __init__(self):
        self._indent = 0
        self._indent_str = "  "

    def print(self, node: ASTNode) -> str:
        """Print the AST starting from the given node."""
        return node.accept(self)

    def _indent_line(self, text: str) -> str:
        """Return the text with current indentation."""
        return self._indent_str * self._indent + text

    def _with_indent(self, func):
        """Execute func with increased indentation."""
        self._indent += 1
        result = func()
        self._indent -= 1
        return result

    # Expression visitors

    def visit_literal_expr(self, expr: LiteralExpr) -> str:
        if isinstance(expr.value, str):
            return f'"{expr.value}"'
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        return str(expr.value)

    def visit_variable_expr(self, expr: VariableExpr) -> str:
        return expr.name

    def visit_binary_expr(self, expr: BinaryExpr) -> str:
        left = expr.left.accept(self)
        right = expr.right.accept(self)
        return f"({left} {expr.operator} {right})"

    def visit_unary_expr(self, expr: UnaryExpr) -> str:
        operand = expr.operand.accept(self)
        return f"({expr.operator}{operand})"

    def visit_grouping_expr(self, expr: GroupingExpr) -> str:
        inner = expr.expression.accept(self)
        return f"(group {inner})"

    def visit_call_expr(self, expr: CallExpr) -> str:
        args = ", ".join(arg.accept(self) for arg in expr.arguments)
        return f"{expr.callee}({args})"

    def visit_assignment_expr(self, expr: AssignmentExpr) -> str:
        value = expr.value.accept(self)
        return f"(assign {expr.name} = {value})"

    # Statement visitors

    def visit_expr_stmt(self, stmt: ExprStmt) -> str:
        expr = stmt.expression.accept(self)
        return self._indent_line(f"{expr};")

    def visit_var_decl_stmt(self, stmt: VarDeclStmt) -> str:
        keyword = "const" if stmt.is_const else "let"
        type_str = str(stmt.type_annotation) if stmt.type_annotation else "?"
        if stmt.initializer:
            init = stmt.initializer.accept(self)
            return self._indent_line(f"{keyword} {stmt.name}: {type_str} = {init};")
        return self._indent_line(f"{keyword} {stmt.name}: {type_str};")

    def visit_block_stmt(self, stmt: BlockStmt) -> str:
        lines = ["{"]
        self._indent += 1
        for s in stmt.statements:
            lines.append(s.accept(self))
        self._indent -= 1
        lines.append(self._indent_line("}"))
        return "\n".join(lines)

    def visit_if_stmt(self, stmt: IfStmt) -> str:
        cond = stmt.condition.accept(self)
        then_str = stmt.then_branch.accept(self)

        result = self._indent_line(f"if {cond} {then_str}")

        if stmt.else_branch:
            if isinstance(stmt.else_branch, IfStmt):
                # else if
                else_str = stmt.else_branch.accept(self).lstrip()
                result += f" else {else_str}"
            else:
                # else block
                else_str = stmt.else_branch.accept(self)
                result += f" else {else_str}"

        return result

    def visit_while_stmt(self, stmt: WhileStmt) -> str:
        cond = stmt.condition.accept(self)
        body_str = stmt.body.accept(self)
        return self._indent_line(f"while {cond} {body_str}")

    def visit_return_stmt(self, stmt: ReturnStmt) -> str:
        if stmt.value:
            value = stmt.value.accept(self)
            return self._indent_line(f"return {value};")
        return self._indent_line("return;")

    # Declaration visitors

    def visit_function_decl(self, decl: FunctionDecl) -> str:
        params = ", ".join(
            f"{p.name}: {p.type_annotation}" for p in decl.parameters
        )
        header = f"fn {decl.name}({params}) -> {decl.return_type}"
        body = decl.body.accept(self)
        return self._indent_line(f"{header} {body}")

    def visit_program(self, program: Program) -> str:
        parts = []
        for decl in program.declarations:
            parts.append(decl.accept(self))
            parts.append("")  # Empty line between declarations
        return "\n".join(parts).rstrip()


# =============================================================================
# Helper Functions
# =============================================================================

def type_from_string(type_str: str) -> Optional[TypeAnnotation]:
    """
    Convert a type string to a TypeAnnotation.

    Args:
        type_str: The type string (e.g., "int", "float", "bool")

    Returns:
        The corresponding TypeAnnotation, or None if invalid
    """
    mapping = {
        "int": TypeAnnotation.INT,
        "float": TypeAnnotation.FLOAT,
        "bool": TypeAnnotation.BOOL,
        "string": TypeAnnotation.STRING,
        "void": TypeAnnotation.VOID,
    }
    return mapping.get(type_str.lower())


def make_literal(value: Any, line: int = 0, column: int = 0) -> LiteralExpr:
    """
    Factory function to create a LiteralExpr with the correct type.

    Args:
        value: The literal value
        line: Source line number
        column: Source column number

    Returns:
        A new LiteralExpr with the appropriate literal_type set
    """
    if isinstance(value, bool):
        lit_type = TypeAnnotation.BOOL
    elif isinstance(value, int):
        lit_type = TypeAnnotation.INT
    elif isinstance(value, float):
        lit_type = TypeAnnotation.FLOAT
    elif isinstance(value, str):
        lit_type = TypeAnnotation.STRING
    else:
        lit_type = None

    return LiteralExpr(
        line=line,
        column=column,
        value=value,
        literal_type=lit_type
    )
