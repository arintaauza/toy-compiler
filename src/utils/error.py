"""
Error handling for the Luna compiler.

Defines custom exception classes for different compiler phases
and provides utilities for error reporting.
"""

from typing import Optional


class CompilerError(Exception):
    """Base exception for all compiler errors."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        """
        Initialize a compiler error.

        Args:
            message: Error description
            line: Line number where error occurred (1-indexed)
            column: Column number where error occurred (1-indexed)
        """
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with position information."""
        if self.line > 0 and self.column > 0:
            return f"Error at line {self.line}, column {self.column}: {self.message}"
        elif self.line > 0:
            return f"Error at line {self.line}: {self.message}"
        else:
            return f"Error: {self.message}"


class LexerError(CompilerError):
    """Exception raised during lexical analysis."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        """
        Initialize a lexer error.

        Args:
            message: Error description
            line: Line number
            column: Column number
        """
        super().__init__(message, line, column)

    def _format_message(self) -> str:
        """Format lexer error message."""
        if self.line > 0 and self.column > 0:
            return f"Lexer Error at line {self.line}, column {self.column}: {self.message}"
        else:
            return f"Lexer Error: {self.message}"


class ParserError(CompilerError):
    """Exception raised during syntax analysis (parsing)."""

    def __init__(self, message: str, line: int = 0, column: int = 0, token_lexeme: str = ""):
        """
        Initialize a parser error.

        Args:
            message: Error description
            line: Line number
            column: Column number
            token_lexeme: The problematic token text
        """
        self.token_lexeme = token_lexeme
        super().__init__(message, line, column)

    def _format_message(self) -> str:
        """Format parser error message."""
        if self.line > 0 and self.column > 0:
            if self.token_lexeme:
                return f"Parser Error at line {self.line}, column {self.column} (token '{self.token_lexeme}'): {self.message}"
            return f"Parser Error at line {self.line}, column {self.column}: {self.message}"
        return f"Parser Error: {self.message}"


class SemanticError(CompilerError):
    """Exception raised during semantic analysis (type checking)."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        """
        Initialize a semantic error.

        Args:
            message: Error description
            line: Line number
            column: Column number
        """
        super().__init__(message, line, column)

    def _format_message(self) -> str:
        """Format semantic error message."""
        if self.line > 0 and self.column > 0:
            return f"Semantic Error at line {self.line}, column {self.column}: {self.message}"
        return f"Semantic Error: {self.message}"


class CodeGenError(CompilerError):
    """Exception raised during code generation."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        """
        Initialize a code generation error.

        Args:
            message: Error description
            line: Line number
            column: Column number
        """
        super().__init__(message, line, column)

    def _format_message(self) -> str:
        """Format code generation error message."""
        if self.line > 0:
            return f"CodeGen Error at line {self.line}: {self.message}"
        return f"CodeGen Error: {self.message}"


def report_error(error: CompilerError, source: Optional[str] = None):
    """
    Report an error with source code context.

    Args:
        error: The compiler error to report
        source: Optional source code to show context
    """
    print(str(error))

    if source and error.line > 0:
        # Show the problematic line
        lines = source.split('\n')
        if 0 < error.line <= len(lines):
            line_text = lines[error.line - 1]
            print()
            print(f"    {line_text}")

            # Show pointer to error column
            if error.column > 0:
                pointer = ' ' * (error.column - 1) + '^'
                print(f"    {pointer}")
