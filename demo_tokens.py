#!/usr/bin/env python3
"""
Demo script to showcase the Token and TokenType classes.
Run: python demo_tokens.py
"""

from src.lexer.token import Token, TokenType, KEYWORDS, create_token, keyword_type

def main():
    print("=" * 70)
    print("LUNA COMPILER - TOKEN DEMONSTRATION")
    print("=" * 70)
    print()

    # 1. Show all token types
    print("📋 ALL TOKEN TYPES:")
    print("-" * 70)

    print("\nKeywords:")
    keywords = [t for t in TokenType if t.name in {k.name for k in KEYWORDS.values()}]
    for token_type in keywords:
        print(f"  {token_type.name:15} - {token_type.value}")

    print("\nOperators:")
    operators = [
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
        TokenType.EQUAL, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
        TokenType.LESS, TokenType.GREATER, TokenType.AND_AND, TokenType.OR_OR
    ]
    for token_type in operators:
        print(f"  {token_type.name:15} - {token_type.value}")

    print("\nLiterals:")
    for token_type in [TokenType.NUMBER, TokenType.STRING, TokenType.IDENTIFIER]:
        print(f"  {token_type.name:15} - {token_type.value}")

    print()

    # 2. Create example tokens
    print("🔨 CREATING EXAMPLE TOKENS:")
    print("-" * 70)

    tokens = [
        create_token(TokenType.LET, "let", line=1, column=1, lexeme="let"),
        create_token(TokenType.IDENTIFIER, "x", line=1, column=5, lexeme="x"),
        create_token(TokenType.COLON, ":", line=1, column=6, lexeme=":"),
        create_token(TokenType.INT, "int", line=1, column=8, lexeme="int"),
        create_token(TokenType.EQUAL, "=", line=1, column=12, lexeme="="),
        create_token(TokenType.NUMBER, 42, line=1, column=14, lexeme="42"),
        create_token(TokenType.SEMICOLON, ";", line=1, column=16, lexeme=";"),
    ]

    print("\nTokens for: let x: int = 42;")
    print()
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. {repr(token)}")
        print(f"     └─ String: {str(token)}")
    print()

    # 3. Demonstrate token properties
    print("🔍 TOKEN PROPERTIES:")
    print("-" * 70)

    test_tokens = [
        create_token(TokenType.FN, "fn", lexeme="fn"),
        create_token(TokenType.NUMBER, 123, lexeme="123"),
        create_token(TokenType.PLUS, "+", lexeme="+"),
        create_token(TokenType.IDENTIFIER, "myVar", lexeme="myVar"),
    ]

    for token in test_tokens:
        print(f"\n{token}:")
        print(f"  is_keyword: {token.is_keyword}")
        print(f"  is_type: {token.is_type}")
        print(f"  is_literal: {token.is_literal}")
        print(f"  is_operator: {token.is_operator}")
        print(f"  is_binary_operator: {token.is_binary_operator}")
        print(f"  is_unary_operator: {token.is_unary_operator}")

    print()

    # 4. Keyword lookup
    print("📚 KEYWORD LOOKUP:")
    print("-" * 70)

    test_words = ["fn", "let", "while", "myVariable", "true", "int"]
    print("\nTesting keyword detection:")
    for word in test_words:
        token_type = keyword_type(word)
        if token_type:
            print(f"  '{word}' → {token_type.name} (keyword)")
        else:
            print(f"  '{word}' → IDENTIFIER (not a keyword)")

    print()
    print("=" * 70)
    print("✅ Token module demonstration complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
