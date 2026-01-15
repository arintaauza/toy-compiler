"""
Unit tests for the Luna lexer.

Tests all tokenization functionality including:
- Keywords, identifiers, literals
- Operators and punctuation
- Comments
- Error handling
"""

import pytest
from src.lexer.lexer import Lexer, tokenize
from src.lexer.token import Token, TokenType
from src.utils.error import LexerError


class TestBasicTokens:
    """Test basic token recognition."""

    def test_keywords(self):
        """Test all keyword recognition."""
        source = "fn let const if else while return true false"
        tokens = tokenize(source)

        expected_types = [
            TokenType.FN, TokenType.LET, TokenType.CONST,
            TokenType.IF, TokenType.ELSE, TokenType.WHILE,
            TokenType.RETURN, TokenType.TRUE, TokenType.FALSE,
            TokenType.EOF
        ]

        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_type_keywords(self):
        """Test type keyword recognition."""
        source = "int float bool string void"
        tokens = tokenize(source)

        expected_types = [
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING_TYPE, TokenType.VOID, TokenType.EOF
        ]

        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_identifiers(self):
        """Test identifier scanning."""
        source = "x myVar _private foo123 CamelCase snake_case"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"

        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "myVar"

        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "_private"

        assert tokens[3].type == TokenType.IDENTIFIER
        assert tokens[3].value == "foo123"

        assert tokens[4].type == TokenType.IDENTIFIER
        assert tokens[4].value == "CamelCase"

        assert tokens[5].type == TokenType.IDENTIFIER
        assert tokens[5].value == "snake_case"


class TestNumberLiterals:
    """Test number literal tokenization."""

    def test_integers(self):
        """Test integer literals."""
        source = "0 42 123 9999"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == 0
        assert isinstance(tokens[0].value, int)

        assert tokens[1].value == 42
        assert tokens[2].value == 123
        assert tokens[3].value == 9999

    def test_floats(self):
        """Test float literals."""
        source = "3.14 0.5 123.456 99.99"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == 3.14
        assert isinstance(tokens[0].value, float)

        assert tokens[1].value == 0.5
        assert tokens[2].value == 123.456
        assert tokens[3].value == 99.99

    def test_mixed_numbers(self):
        """Test mix of integers and floats."""
        source = "42 3.14 100 0.5"
        tokens = tokenize(source)

        assert isinstance(tokens[0].value, int)
        assert isinstance(tokens[1].value, float)
        assert isinstance(tokens[2].value, int)
        assert isinstance(tokens[3].value, float)


class TestStringLiterals:
    """Test string literal tokenization."""

    def test_simple_string(self):
        """Test simple string literal."""
        source = '"hello"'
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_empty_string(self):
        """Test empty string."""
        source = '""'
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == ""

    def test_string_with_spaces(self):
        """Test string with spaces."""
        source = '"Hello, World!"'
        tokens = tokenize(source)

        assert tokens[0].value == "Hello, World!"

    def test_escape_sequences(self):
        """Test escape sequences in strings."""
        source = r'"Hello\nWorld"'
        tokens = tokenize(source)

        assert tokens[0].value == "Hello\nWorld"

        source = r'"Tab\there"'
        tokens = tokenize(source)
        assert tokens[0].value == "Tab\there"

        source = r'"Quote:\"test\""'
        tokens = tokenize(source)
        assert tokens[0].value == 'Quote:"test"'

        source = r'"Backslash:\\"'
        tokens = tokenize(source)
        assert tokens[0].value == "Backslash:\\"


class TestOperators:
    """Test operator tokenization."""

    def test_arithmetic_operators(self):
        """Test arithmetic operators."""
        source = "+ - * / %"
        tokens = tokenize(source)

        expected_types = [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT, TokenType.EOF
        ]

        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_comparison_operators(self):
        """Test comparison operators."""
        source = "< > <= >= == !="
        tokens = tokenize(source)

        expected_types = [
            TokenType.LESS, TokenType.GREATER,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
            TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
            TokenType.EOF
        ]

        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_logical_operators(self):
        """Test logical operators."""
        source = "! && ||"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.BANG
        assert tokens[1].type == TokenType.AND_AND
        assert tokens[2].type == TokenType.OR_OR

    def test_arrow_operator(self):
        """Test arrow operator for function return types."""
        source = "->"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.ARROW


class TestPunctuation:
    """Test punctuation tokenization."""

    def test_all_punctuation(self):
        """Test all punctuation marks."""
        source = "( ) { } [ ] ; , :"
        tokens = tokenize(source)

        expected_types = [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACE, TokenType.RBRACE,
            TokenType.LBRACKET, TokenType.RBRACKET,
            TokenType.SEMICOLON, TokenType.COMMA, TokenType.COLON,
            TokenType.EOF
        ]

        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type


class TestComments:
    """Test comment handling."""

    def test_single_line_comment(self):
        """Test single-line comments are skipped."""
        source = "let x: int = 5; // This is a comment"
        tokens = tokenize(source)

        # Should only get tokens before comment, not the comment itself
        assert tokens[0].type == TokenType.LET
        # Find the number token
        number_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert number_token.value == 5

    def test_multi_line_comment(self):
        """Test multi-line comments are skipped."""
        source = """
        let x: int = 5;
        /* This is a
           multi-line comment */
        let y: int = 10;
        """
        tokens = tokenize(source)

        # Should have tokens for both let statements
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert token_types.count(TokenType.LET) == 2
        assert token_types.count(TokenType.IDENTIFIER) == 2

    def test_inline_comment(self):
        """Test inline comments."""
        source = "x /* comment */ + /* another */ y"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"
        assert tokens[1].type == TokenType.PLUS
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "y"


class TestComplexExpressions:
    """Test complex expressions."""

    def test_variable_declaration(self):
        """Test variable declaration."""
        source = "let x: int = 42;"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.LET
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "x"
        assert tokens[2].type == TokenType.COLON
        assert tokens[3].type == TokenType.INT
        assert tokens[4].type == TokenType.EQUAL
        assert tokens[5].type == TokenType.NUMBER
        assert tokens[5].value == 42
        assert tokens[6].type == TokenType.SEMICOLON

    def test_function_declaration(self):
        """Test function declaration."""
        source = "fn add(a: int, b: int) -> int"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.FN
        assert tokens[1].value == "add"
        assert tokens[2].type == TokenType.LPAREN
        assert tokens[3].value == "a"
        assert tokens[4].type == TokenType.COLON
        assert tokens[5].type == TokenType.INT
        assert tokens[6].type == TokenType.COMMA
        assert tokens[7].value == "b"
        # Find the arrow token
        arrow_token = [t for t in tokens if t.type == TokenType.ARROW][0]
        assert arrow_token.type == TokenType.ARROW

    def test_arithmetic_expression(self):
        """Test arithmetic expression."""
        source = "x + y * 2 - (a / b)"
        tokens = tokenize(source)

        expected_types = [
            TokenType.IDENTIFIER, TokenType.PLUS,
            TokenType.IDENTIFIER, TokenType.STAR, TokenType.NUMBER,
            TokenType.MINUS, TokenType.LPAREN,
            TokenType.IDENTIFIER, TokenType.SLASH, TokenType.IDENTIFIER,
            TokenType.RPAREN, TokenType.EOF
        ]

        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type


class TestPositionTracking:
    """Test line and column position tracking."""

    def test_line_tracking(self):
        """Test line number tracking."""
        source = """let x: int = 5;
let y: int = 10;
let z: int = 15;"""

        tokens = tokenize(source)

        # First let should be on line 1
        assert tokens[0].line == 1

        # Second let should be on line 2
        second_let = [t for t in tokens if t.type == TokenType.LET][1]
        assert second_let.line == 2

        # Third let should be on line 3
        third_let = [t for t in tokens if t.type == TokenType.LET][2]
        assert third_let.line == 3

    def test_column_tracking(self):
        """Test column number tracking."""
        source = "let x: int = 42;"

        tokens = tokenize(source)

        assert tokens[0].column == 1  # "let" starts at column 1
        assert tokens[1].column == 5  # "x" starts at column 5


class TestErrorHandling:
    """Test error detection and reporting."""

    def test_unterminated_string(self):
        """Test unterminated string error."""
        source = '"hello'

        with pytest.raises(LexerError) as exc_info:
            tokenize(source)

        assert "Unterminated string" in str(exc_info.value)

    def test_invalid_character(self):
        """Test invalid character error."""
        source = "let x: int = 5 @ 3;"

        with pytest.raises(LexerError) as exc_info:
            tokenize(source)

        assert "Unexpected character" in str(exc_info.value)

    def test_unterminated_block_comment(self):
        """Test unterminated block comment error."""
        source = "/* This comment never ends"

        with pytest.raises(LexerError) as exc_info:
            tokenize(source)

        assert "Unterminated block comment" in str(exc_info.value)

    def test_single_ampersand_error(self):
        """Test single & is an error (should be &&)."""
        source = "x & y"

        with pytest.raises(LexerError) as exc_info:
            tokenize(source)

        assert "'&'" in str(exc_info.value)

    def test_single_pipe_error(self):
        """Test single | is an error (should be ||)."""
        source = "x | y"

        with pytest.raises(LexerError) as exc_info:
            tokenize(source)

        assert "'|'" in str(exc_info.value)


class TestWhitespace:
    """Test whitespace handling."""

    def test_spaces_ignored(self):
        """Test that spaces are ignored."""
        source1 = "let x:int=5;"
        source2 = "let  x  :  int  =  5  ;"

        tokens1 = tokenize(source1)
        tokens2 = tokenize(source2)

        # Should produce same token types regardless of spacing
        types1 = [t.type for t in tokens1]
        types2 = [t.type for t in tokens2]
        assert types1 == types2

    def test_tabs_ignored(self):
        """Test that tabs are ignored."""
        source = "let\tx:\tint\t=\t5;"
        tokens = tokenize(source)

        assert tokens[0].type == TokenType.LET
        assert tokens[1].type == TokenType.IDENTIFIER

    def test_newlines_ignored(self):
        """Test that newlines are ignored."""
        source = """
        let
        x
        :
        int
        =
        5
        ;
        """
        tokens = tokenize(source)

        # Should tokenize properly despite newlines
        assert tokens[0].type == TokenType.LET
        assert tokens[1].value == "x"


class TestEOF:
    """Test EOF token."""

    def test_eof_always_last(self):
        """Test that EOF is always the last token."""
        sources = [
            "let x: int = 5;",
            "fn main() -> int { return 0; }",
            "",
            "// just a comment",
        ]

        for source in sources:
            tokens = tokenize(source)
            assert tokens[-1].type == TokenType.EOF

    def test_empty_source(self):
        """Test tokenizing empty source."""
        source = ""
        tokens = tokenize(source)

        # Should only have EOF token
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
