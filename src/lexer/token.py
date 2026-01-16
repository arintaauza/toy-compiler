"""
Token definitions for the Toy compiler.

This module defines:
- TokenType: Enum of all token types in the Toy language
- Token: Class representing a single token with position information
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    """All token types in the Toy language."""

    # Keywords
    FN = auto()          # fn
    LET = auto()         # let
    CONST = auto()       # const
    IF = auto()          # if
    ELSE = auto()        # else
    WHILE = auto()       # while
    RETURN = auto()      # return
    TRUE = auto()        # true
    FALSE = auto()       # false

    # Types
    INT = auto()         # int
    FLOAT = auto()       # float
    BOOL = auto()        # bool
    STRING_TYPE = auto() # string (STRING_TYPE to avoid conflict with STRING literal)
    VOID = auto()        # void

    # Literals
    NUMBER = auto()      # Integer or float literal (42, 3.14)
    STRING = auto()      # String literal ("hello")
    IDENTIFIER = auto()  # Variable/function names (foo, bar_123)

    # Operators
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %

    BANG = auto()        # !
    EQUAL = auto()       # =
    EQUAL_EQUAL = auto() # ==
    BANG_EQUAL = auto()  # !=
    LESS = auto()        # <
    LESS_EQUAL = auto()  # <=
    GREATER = auto()     # >
    GREATER_EQUAL = auto() # >=

    AND_AND = auto()     # &&
    OR_OR = auto()       # ||

    # Punctuation
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [ (future: arrays)
    RBRACKET = auto()    # ] (future: arrays)

    SEMICOLON = auto()   # ;
    COMMA = auto()       # ,
    COLON = auto()       # :
    ARROW = auto()       # ->

    # Special
    EOF = auto()         # End of file
    NEWLINE = auto()     # Newline (may be ignored by parser)

    def __repr__(self) -> str:
        """Return a readable representation of the token type."""
        return f"TokenType.{self.name}"


# Mapping of keywords to their token types
KEYWORDS = {
    "fn": TokenType.FN,
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "bool": TokenType.BOOL,
    "string": TokenType.STRING_TYPE,
    "void": TokenType.VOID,
}


@dataclass
class Token:
    """
    Represents a single token in the Toy language.

    Attributes:
        type: The type of token (from TokenType enum)
        value: The literal value of the token (string, number, etc.)
        line: Line number where token appears (1-indexed)
        column: Column number where token starts (1-indexed)
        lexeme: The original text from source code
    """
    type: TokenType
    value: Any
    line: int
    column: int
    lexeme: str = ""

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        if self.value is not None and self.value != self.lexeme:
            return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
        return f"Token({self.type.name}, {self.line}:{self.column})"

    def __str__(self) -> str:
        """Return a concise string representation."""
        if self.value is not None:
            return f"{self.type.name}({self.value})"
        return self.type.name

    @property
    def is_keyword(self) -> bool:
        """Check if this token is a keyword."""
        return self.type in {
            TokenType.FN, TokenType.LET, TokenType.CONST,
            TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.RETURN,
            TokenType.TRUE, TokenType.FALSE,
        }

    @property
    def is_type(self) -> bool:
        """Check if this token is a type keyword."""
        return self.type in {
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING_TYPE, TokenType.VOID,
        }

    @property
    def is_literal(self) -> bool:
        """Check if this token is a literal value."""
        return self.type in {
            TokenType.NUMBER, TokenType.STRING,
            TokenType.TRUE, TokenType.FALSE,
        }

    @property
    def is_operator(self) -> bool:
        """Check if this token is an operator."""
        return self.type in {
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT,
            TokenType.BANG, TokenType.EQUAL,
            TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
            TokenType.LESS, TokenType.LESS_EQUAL,
            TokenType.GREATER, TokenType.GREATER_EQUAL,
            TokenType.AND_AND, TokenType.OR_OR,
        }

    @property
    def is_binary_operator(self) -> bool:
        """Check if this token is a binary operator."""
        return self.type in {
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT,
            TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
            TokenType.LESS, TokenType.LESS_EQUAL,
            TokenType.GREATER, TokenType.GREATER_EQUAL,
            TokenType.AND_AND, TokenType.OR_OR,
        }

    @property
    def is_unary_operator(self) -> bool:
        """Check if this token is a unary operator."""
        return self.type in {TokenType.BANG, TokenType.MINUS}


def create_token(
    type: TokenType,
    value: Any = None,
    line: int = 1,
    column: int = 1,
    lexeme: str = ""
) -> Token:
    """
    Factory function to create a token.

    Args:
        type: The token type
        value: The token value (if applicable)
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        lexeme: The original text from source

    Returns:
        A new Token instance
    """
    if lexeme == "" and value is not None:
        lexeme = str(value)

    return Token(
        type=type,
        value=value,
        line=line,
        column=column,
        lexeme=lexeme
    )


# Helper function to check if a string is a keyword
def is_keyword(text: str) -> bool:
    """Check if the given text is a Toy keyword."""
    return text in KEYWORDS


# Helper function to get token type for a keyword
def keyword_type(text: str) -> Optional[TokenType]:
    """
    Get the TokenType for a keyword.

    Args:
        text: The keyword text

    Returns:
        The corresponding TokenType, or None if not a keyword
    """
    return KEYWORDS.get(text)
