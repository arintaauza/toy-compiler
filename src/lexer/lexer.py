"""
Lexer for the Luna compiler.

The lexer (also called scanner or tokenizer) converts source code text
into a stream of tokens. It handles:
- Whitespace and comments
- Keywords and identifiers
- Number literals (integers and floats)
- String literals with escape sequences
- Operators and punctuation
"""

from typing import List, Optional
from src.lexer.token import Token, TokenType, create_token, keyword_type


class Lexer:
    """
    Lexical analyzer for Luna source code.

    Scans source code character by character and produces tokens.
    Tracks line and column positions for error reporting.
    """

    def __init__(self, source: str):
        """
        Initialize the lexer with source code.

        Args:
            source: The Luna source code as a string
        """
        self.source = source
        self.start = 0      # Start of current token
        self.current = 0    # Current character position
        self.line = 1       # Current line number (1-indexed)
        self.column = 1     # Current column number (1-indexed)
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire source code.

        Returns:
            List of tokens including EOF token at the end
        """
        while not self._is_at_end():
            # Start of next token
            self.start = self.current
            self._scan_token()

        # Add EOF token
        self.tokens.append(create_token(
            TokenType.EOF,
            None,
            self.line,
            self.column,
            ""
        ))

        return self.tokens

    def _scan_token(self):
        """Scan a single token from the current position."""
        c = self._advance()

        # Whitespace
        if c in ' \t\r':
            return  # Skip whitespace

        if c == '\n':
            self.line += 1
            self.column = 1
            return

        # Comments
        if c == '/':
            if self._match('/'):
                # Single-line comment: skip until end of line
                self._skip_line_comment()
                return
            elif self._match('*'):
                # Multi-line comment: skip until */
                self._skip_block_comment()
                return
            else:
                # Division operator
                self._add_token(TokenType.SLASH, '/')
                return

        # String literals
        if c == '"':
            self._scan_string()
            return

        # Number literals
        if c.isdigit():
            self._scan_number()
            return

        # Identifiers and keywords
        if c.isalpha() or c == '_':
            self._scan_identifier()
            return

        # Operators and punctuation
        self._scan_operator_or_punctuation(c)

    def _scan_operator_or_punctuation(self, c: str):
        """Scan operators and punctuation marks."""
        # Two-character operators (must check before single-character)
        if c == '=':
            if self._match('='):
                self._add_token(TokenType.EQUAL_EQUAL, '==')
            else:
                self._add_token(TokenType.EQUAL, '=')

        elif c == '!':
            if self._match('='):
                self._add_token(TokenType.BANG_EQUAL, '!=')
            else:
                self._add_token(TokenType.BANG, '!')

        elif c == '<':
            if self._match('='):
                self._add_token(TokenType.LESS_EQUAL, '<=')
            else:
                self._add_token(TokenType.LESS, '<')

        elif c == '>':
            if self._match('='):
                self._add_token(TokenType.GREATER_EQUAL, '>=')
            else:
                self._add_token(TokenType.GREATER, '>')

        elif c == '&':
            if self._match('&'):
                self._add_token(TokenType.AND_AND, '&&')
            else:
                self._error(f"Unexpected character '&' (did you mean '&&'?)")

        elif c == '|':
            if self._match('|'):
                self._add_token(TokenType.OR_OR, '||')
            else:
                self._error(f"Unexpected character '|' (did you mean '||'?)")

        elif c == '-':
            if self._match('>'):
                self._add_token(TokenType.ARROW, '->')
            else:
                self._add_token(TokenType.MINUS, '-')

        # Single-character operators
        elif c == '+':
            self._add_token(TokenType.PLUS, '+')
        elif c == '*':
            self._add_token(TokenType.STAR, '*')
        elif c == '%':
            self._add_token(TokenType.PERCENT, '%')

        # Punctuation
        elif c == '(':
            self._add_token(TokenType.LPAREN, '(')
        elif c == ')':
            self._add_token(TokenType.RPAREN, ')')
        elif c == '{':
            self._add_token(TokenType.LBRACE, '{')
        elif c == '}':
            self._add_token(TokenType.RBRACE, '}')
        elif c == '[':
            self._add_token(TokenType.LBRACKET, '[')
        elif c == ']':
            self._add_token(TokenType.RBRACKET, ']')
        elif c == ';':
            self._add_token(TokenType.SEMICOLON, ';')
        elif c == ',':
            self._add_token(TokenType.COMMA, ',')
        elif c == ':':
            self._add_token(TokenType.COLON, ':')

        else:
            self._error(f"Unexpected character '{c}'")

    def _scan_identifier(self):
        """Scan an identifier or keyword."""
        # Continue while alphanumeric or underscore
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == '_'):
            self._advance()

        # Get the identifier text
        text = self.source[self.start:self.current]

        # Check if it's a keyword
        token_type = keyword_type(text)
        if token_type:
            # It's a keyword
            self._add_token(token_type, text)
        else:
            # It's an identifier
            self._add_token(TokenType.IDENTIFIER, text)

    def _scan_number(self):
        """Scan a number literal (integer or float)."""
        # Scan integer part
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()

        # Check for decimal point
        is_float = False
        if not self._is_at_end() and self._peek() == '.' and self._peek_next().isdigit():
            is_float = True
            self._advance()  # Consume '.'

            # Scan fractional part
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        # Get the number text and convert to value
        text = self.source[self.start:self.current]

        if is_float:
            value = float(text)
        else:
            value = int(text)

        self._add_token(TokenType.NUMBER, value, text)

    def _scan_string(self):
        """Scan a string literal with escape sequences."""
        value = ""

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == '\n':
                # Multi-line strings not allowed
                self._error("Unterminated string (newline in string)")
                return

            if self._peek() == '\\':
                # Escape sequence
                self._advance()  # Consume '\'
                if self._is_at_end():
                    self._error("Unterminated string (incomplete escape)")
                    return

                escape_char = self._advance()

                # Handle escape sequences
                if escape_char == 'n':
                    value += '\n'
                elif escape_char == 't':
                    value += '\t'
                elif escape_char == 'r':
                    value += '\r'
                elif escape_char == '\\':
                    value += '\\'
                elif escape_char == '"':
                    value += '"'
                elif escape_char == '0':
                    value += '\0'
                else:
                    self._error(f"Invalid escape sequence '\\{escape_char}'")
                    value += escape_char  # Add it anyway
            else:
                # Regular character
                value += self._advance()

        if self._is_at_end():
            self._error("Unterminated string (missing closing quote)")
            return

        # Consume closing quote
        self._advance()

        # Get original text with quotes
        text = self.source[self.start:self.current]

        self._add_token(TokenType.STRING, value, text)

    def _skip_line_comment(self):
        """Skip a single-line comment (// ...)."""
        # Skip until end of line or end of file
        while not self._is_at_end() and self._peek() != '\n':
            self._advance()

    def _skip_block_comment(self):
        """Skip a multi-line comment (/* ... */)."""
        # Track nesting level for nested comments (optional feature)
        while not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.column = 0  # Will be incremented by _advance()

            if self._peek() == '*' and self._peek_next() == '/':
                # End of comment
                self._advance()  # Consume '*'
                self._advance()  # Consume '/'
                return

            self._advance()

        # Reached end of file without closing comment
        self._error("Unterminated block comment (missing */)")

    # Helper methods

    def _advance(self) -> str:
        """
        Consume and return the current character.
        Also updates column position.
        """
        if self._is_at_end():
            return '\0'

        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def _match(self, expected: str) -> bool:
        """
        Check if current character matches expected.
        If so, consume it and return True.
        """
        if self._is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.current += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        """Look at current character without consuming it."""
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        """Look at next character without consuming it."""
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of source code."""
        return self.current >= len(self.source)

    def _add_token(self, token_type: TokenType, value=None, lexeme: str = ""):
        """Add a token to the token list."""
        if lexeme == "":
            lexeme = self.source[self.start:self.current]

        # Calculate column of token start
        token_column = self.column - (self.current - self.start)

        token = create_token(
            type=token_type,
            value=value if value is not None else lexeme,
            line=self.line,
            column=token_column,
            lexeme=lexeme
        )

        self.tokens.append(token)

    def _error(self, message: str):
        """
        Report a lexical error.
        For now, just print. Later we'll use proper error handling.
        """
        print(f"Lexer Error at line {self.line}, column {self.column}: {message}")


# Convenience function
def tokenize(source: str) -> List[Token]:
    """
    Tokenize Luna source code.

    Args:
        source: Luna source code as a string

    Returns:
        List of tokens
    """
    lexer = Lexer(source)
    return lexer.tokenize()
