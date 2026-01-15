#!/usr/bin/env python3
"""
Demo script to test the Lexer.
Run: python3 demo_lexer.py
"""

from src.lexer.lexer import Lexer, tokenize
from src.lexer.token import TokenType

def demo_basic_tokens():
    """Test basic tokenization."""
    print("=" * 70)
    print("DEMO 1: Basic Tokens")
    print("=" * 70)

    source = "let x: int = 42;"
    print(f"\nSource: {source}\n")

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    print("Tokens:")
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. {token}")

    print()


def demo_operators():
    """Test operator tokenization."""
    print("=" * 70)
    print("DEMO 2: Operators")
    print("=" * 70)

    source = "x == 5 && y != 3 || z >= 10"
    print(f"\nSource: {source}\n")

    tokens = tokenize(source)

    print("Tokens:")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {token}")

    print()


def demo_function():
    """Test function declaration."""
    print("=" * 70)
    print("DEMO 3: Function Declaration")
    print("=" * 70)

    source = """
fn add(a: int, b: int) -> int {
    return a + b;
}
"""
    print(f"Source:{source}")

    tokens = tokenize(source)

    print("Tokens:")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {repr(token)}")

    print()


def demo_strings():
    """Test string literals with escapes."""
    print("=" * 70)
    print("DEMO 4: String Literals")
    print("=" * 70)

    source = r'let msg: string = "Hello\nWorld\t!";'
    print(f"\nSource: {source}\n")

    tokens = tokenize(source)

    print("Tokens:")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {token}")
            if token.type == TokenType.STRING:
                print(f"     Value: {repr(token.value)}")

    print()


def demo_numbers():
    """Test number literals."""
    print("=" * 70)
    print("DEMO 5: Number Literals")
    print("=" * 70)

    source = "let x: int = 42; let y: float = 3.14159;"
    print(f"\nSource: {source}\n")

    tokens = tokenize(source)

    print("Tokens:")
    for token in tokens:
        if token.type == TokenType.NUMBER:
            print(f"  {token} - Type: {type(token.value).__name__}, Value: {token.value}")

    print()


def demo_comments():
    """Test comment handling."""
    print("=" * 70)
    print("DEMO 6: Comments")
    print("=" * 70)

    source = """
// This is a single-line comment
let x: int = 5;  // Inline comment

/* This is a
   multi-line comment */
let y: int = 10;
"""
    print(f"Source:{source}")

    tokens = tokenize(source)

    print("Tokens (comments are skipped):")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {token}")

    print()


def demo_full_program():
    """Test a complete Luna program."""
    print("=" * 70)
    print("DEMO 7: Complete Program (Fibonacci)")
    print("=" * 70)

    source = """
fn fibonacci(n: int) -> int {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn main() -> int {
    let result: int = fibonacci(10);
    print(result);
    return 0;
}
"""
    print(f"Source:{source}")

    tokens = tokenize(source)

    print(f"Total tokens: {len(tokens)}")
    print("\nFirst 20 tokens:")
    for i, token in enumerate(tokens[:20], 1):
        print(f"  {i:2}. {repr(token)}")

    print("\n... (remaining tokens omitted)")
    print()


def demo_error_handling():
    """Test error detection."""
    print("=" * 70)
    print("DEMO 8: Error Handling")
    print("=" * 70)

    # Unterminated string
    print("\n1. Unterminated string:")
    source1 = 'let x: string = "hello'
    print(f"   Source: {source1}")
    tokens1 = tokenize(source1)
    print()

    # Invalid character
    print("2. Invalid character:")
    source2 = "let x: int = 5 @ 3;"
    print(f"   Source: {source2}")
    tokens2 = tokenize(source2)
    print()


def main():
    """Run all demos."""
    demo_basic_tokens()
    demo_operators()
    demo_function()
    demo_strings()
    demo_numbers()
    demo_comments()
    demo_full_program()
    demo_error_handling()

    print("=" * 70)
    print("✅ Lexer demonstration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
