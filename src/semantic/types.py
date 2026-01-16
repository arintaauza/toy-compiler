"""
Type system for the Toy compiler.

This module defines the Toy type system including:
- ToyType base class and concrete type classes
- Type compatibility and equality checking
- Built-in type instances (INT, FLOAT, BOOL, STRING, VOID)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.parser.ast_nodes import TypeAnnotation


class ToyType(ABC):
    """
    Abstract base class for all Toy types.

    All types must implement equality checking and string representation.
    """

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def is_numeric(self) -> bool:
        """Check if this type is numeric (int or float)."""
        return False

    def is_compatible_with(self, other: 'ToyType') -> bool:
        """
        Check if this type is compatible with another type.

        By default, types are compatible only if they are equal.
        Subclasses may override this for more permissive rules.
        """
        return self == other


class PrimitiveType(ToyType):
    """
    Represents a primitive (built-in) type in Toy.

    Primitive types: int, float, bool, string, void
    """

    def __init__(self, name: str):
        self._name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PrimitiveType):
            return False
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"PrimitiveType({self._name})"

    @property
    def name(self) -> str:
        return self._name

    def is_numeric(self) -> bool:
        return self._name in ("int", "float")


@dataclass
class FunctionType(ToyType):
    """
    Represents a function type in Toy.

    Function types track parameter types and return type for
    type checking function calls.
    """
    parameter_types: List[ToyType] = field(default_factory=list)
    return_type: ToyType = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunctionType):
            return False
        if self.return_type != other.return_type:
            return False
        if len(self.parameter_types) != len(other.parameter_types):
            return False
        return all(
            p1 == p2
            for p1, p2 in zip(self.parameter_types, other.parameter_types)
        )

    def __hash__(self) -> int:
        return hash((tuple(self.parameter_types), self.return_type))

    def __str__(self) -> str:
        params = ", ".join(str(p) for p in self.parameter_types)
        return f"fn({params}) -> {self.return_type}"


# =============================================================================
# Built-in Type Instances
# =============================================================================

# Singleton instances for primitive types
INT = PrimitiveType("int")
FLOAT = PrimitiveType("float")
BOOL = PrimitiveType("bool")
STRING = PrimitiveType("string")
VOID = PrimitiveType("void")

# Type lookup by name
BUILTIN_TYPES = {
    "int": INT,
    "float": FLOAT,
    "bool": BOOL,
    "string": STRING,
    "void": VOID,
}


# =============================================================================
# Type Conversion Utilities
# =============================================================================

def type_from_annotation(annotation: 'TypeAnnotation') -> ToyType:
    """
    Convert a TypeAnnotation (from AST) to a ToyType.

    Args:
        annotation: TypeAnnotation enum value from the parser

    Returns:
        Corresponding ToyType

    Raises:
        ValueError: If the annotation is unknown
    """
    from src.parser.ast_nodes import TypeAnnotation

    mapping = {
        TypeAnnotation.INT: INT,
        TypeAnnotation.FLOAT: FLOAT,
        TypeAnnotation.BOOL: BOOL,
        TypeAnnotation.STRING: STRING,
        TypeAnnotation.VOID: VOID,
    }

    if annotation in mapping:
        return mapping[annotation]

    raise ValueError(f"Unknown type annotation: {annotation}")


def type_from_name(name: str) -> Optional[ToyType]:
    """
    Get a ToyType by name.

    Args:
        name: Type name (e.g., "int", "float")

    Returns:
        Corresponding ToyType, or None if not found
    """
    return BUILTIN_TYPES.get(name.lower())


# =============================================================================
# Type Checking Utilities
# =============================================================================

def is_assignable(target_type: ToyType, value_type: ToyType) -> bool:
    """
    Check if a value of value_type can be assigned to a variable of target_type.

    Toy has strict typing - no implicit conversions are allowed.

    Args:
        target_type: The type of the variable being assigned to
        value_type: The type of the value being assigned

    Returns:
        True if the assignment is valid
    """
    return target_type == value_type


def get_binary_result_type(
    op: str,
    left_type: ToyType,
    right_type: ToyType
) -> Optional[ToyType]:
    """
    Determine the result type of a binary operation.

    Args:
        op: The operator (e.g., "+", "==", "&&")
        left_type: Type of the left operand
        right_type: Type of the right operand

    Returns:
        The result type, or None if the operation is invalid
    """
    # Arithmetic operators: +, -, *, /, %
    if op in ("+", "-", "*", "/"):
        if left_type == INT and right_type == INT:
            return INT
        if left_type == FLOAT and right_type == FLOAT:
            return FLOAT
        # Allow int/float mixed for arithmetic? Toy spec says no implicit conversion
        # So we require same types
        return None

    if op == "%":
        # Modulo only works on integers
        if left_type == INT and right_type == INT:
            return INT
        return None

    # String concatenation
    if op == "+":
        if left_type == STRING and right_type == STRING:
            return STRING

    # Comparison operators: <, >, <=, >=
    if op in ("<", ">", "<=", ">="):
        # Both operands must be the same numeric type
        if left_type == right_type and left_type.is_numeric():
            return BOOL
        return None

    # Equality operators: ==, !=
    if op in ("==", "!="):
        # Both operands must be the same type
        if left_type == right_type:
            return BOOL
        return None

    # Logical operators: &&, ||
    if op in ("&&", "||"):
        if left_type == BOOL and right_type == BOOL:
            return BOOL
        return None

    return None


def get_unary_result_type(op: str, operand_type: ToyType) -> Optional[ToyType]:
    """
    Determine the result type of a unary operation.

    Args:
        op: The operator ("-" or "!")
        operand_type: Type of the operand

    Returns:
        The result type, or None if the operation is invalid
    """
    if op == "-":
        # Negation works on numeric types
        if operand_type.is_numeric():
            return operand_type
        return None

    if op == "!":
        # Logical NOT only works on bool
        if operand_type == BOOL:
            return BOOL
        return None

    return None


def types_match(expected: ToyType, actual: ToyType) -> bool:
    """
    Check if two types match exactly.

    Args:
        expected: The expected type
        actual: The actual type

    Returns:
        True if the types match
    """
    return expected == actual


def format_type_mismatch(expected: ToyType, actual: ToyType) -> str:
    """
    Format a type mismatch error message.

    Args:
        expected: The expected type
        actual: The actual type

    Returns:
        Formatted error message
    """
    return f"Type mismatch: expected '{expected}', got '{actual}'"
