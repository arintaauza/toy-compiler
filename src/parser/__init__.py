"""
Parser module for the Toy compiler.

This module provides:
- AST node definitions (ast_nodes.py)
- Parser implementation (parser.py)
"""

from src.parser.ast_nodes import (
    # Type annotation
    TypeAnnotation,

    # Base classes
    ASTNode,
    Expression,
    Statement,
    Declaration,

    # Expression nodes
    LiteralExpr,
    VariableExpr,
    BinaryExpr,
    UnaryExpr,
    GroupingExpr,
    CallExpr,
    AssignmentExpr,

    # Statement nodes
    ExprStmt,
    VarDeclStmt,
    BlockStmt,
    IfStmt,
    WhileStmt,
    ReturnStmt,

    # Declaration nodes
    Parameter,
    FunctionDecl,
    Program,

    # Visitor
    ASTVisitor,
    ASTPrinter,

    # Helpers
    type_from_string,
    make_literal,
)

__all__ = [
    # Type annotation
    "TypeAnnotation",

    # Base classes
    "ASTNode",
    "Expression",
    "Statement",
    "Declaration",

    # Expression nodes
    "LiteralExpr",
    "VariableExpr",
    "BinaryExpr",
    "UnaryExpr",
    "GroupingExpr",
    "CallExpr",
    "AssignmentExpr",

    # Statement nodes
    "ExprStmt",
    "VarDeclStmt",
    "BlockStmt",
    "IfStmt",
    "WhileStmt",
    "ReturnStmt",

    # Declaration nodes
    "Parameter",
    "FunctionDecl",
    "Program",

    # Visitor
    "ASTVisitor",
    "ASTPrinter",

    # Helpers
    "type_from_string",
    "make_literal",

    # Parser
    "Parser",
    "parse",
    "parse_source",
]

from src.parser.parser import Parser, parse, parse_source
