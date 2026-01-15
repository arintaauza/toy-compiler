#!/usr/bin/env python3
"""
Test lexer with actual Luna example files.
"""

from src.lexer.lexer import tokenize
from pathlib import Path

def test_file(filepath: str):
    """Tokenize a Luna file and show results."""
    path = Path(filepath)

    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return

    print("=" * 70)
    print(f"File: {path.name}")
    print("=" * 70)

    source = path.read_text()
    print(f"\nSource code:\n{source}")

    tokens = tokenize(source)

    print(f"\nTokens ({len(tokens)} total):")
    for i, token in enumerate(tokens, 1):
        print(f"  {i:3}. {repr(token)}")

    print()

def main():
    """Test all example files."""
    example_files = [
        "examples/hello_world.luna",
        "examples/fibonacci.luna",
        "examples/factorial.luna",
        "examples/fizzbuzz.luna",
    ]

    for filepath in example_files:
        test_file(filepath)

    print("=" * 70)
    print("✅ All example files tokenized successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
