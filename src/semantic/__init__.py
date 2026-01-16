"""
Semantic analysis module for the Toy compiler.

This module provides:
- Type system (types.py)
- Symbol table (symbol_table.py)
- Type checker (type_checker.py)
- Semantic analyzer (semantic_analyzer.py)
"""

from src.semantic.types import (
    # Types
    ToyType,
    PrimitiveType,
    FunctionType,
    # Built-in type instances
    INT,
    FLOAT,
    BOOL,
    STRING,
    VOID,
    BUILTIN_TYPES,
    # Utilities
    type_from_annotation,
    type_from_name,
    is_assignable,
    get_binary_result_type,
    get_unary_result_type,
    types_match,
    format_type_mismatch,
)

from src.semantic.symbol_table import (
    SymbolKind,
    Symbol,
    Scope,
    SymbolTable,
    create_symbol_table_with_builtins,
)

from src.semantic.type_checker import TypeChecker

from src.semantic.semantic_analyzer import (
    SemanticAnalyzer,
    analyze,
    analyze_source,
)

__all__ = [
    # Types
    "ToyType",
    "PrimitiveType",
    "FunctionType",
    "INT",
    "FLOAT",
    "BOOL",
    "STRING",
    "VOID",
    "BUILTIN_TYPES",
    "type_from_annotation",
    "type_from_name",
    "is_assignable",
    "get_binary_result_type",
    "get_unary_result_type",
    "types_match",
    "format_type_mismatch",

    # Symbol table
    "SymbolKind",
    "Symbol",
    "Scope",
    "SymbolTable",
    "create_symbol_table_with_builtins",

    # Type checker
    "TypeChecker",

    # Semantic analyzer
    "SemanticAnalyzer",
    "analyze",
    "analyze_source",
]
