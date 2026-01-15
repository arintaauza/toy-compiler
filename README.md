# Luna Compiler Project 🌙

A complete compiler implementation for **Luna**, a simple statically-typed programming language, built from scratch in Python as a learning project.

## Project Overview

**Luna** is a C-like programming language designed to teach compiler construction concepts. This project implements a full compiler pipeline from source code to executable output.

### Language Features

- ✅ Static typing (int, bool, string, float)
- ✅ Variables and constants
- ✅ Functions with parameters and return values
- ✅ Control flow (if/else, while loops)
- ✅ Expressions with operators (+, -, *, /, ==, !=, <, >, etc.)
- ✅ Built-in functions (print, input, len)
- ✅ Comments (single-line and multi-line)

### Example Luna Program

```luna
// Fibonacci sequence calculator
fn fibonacci(n: int) -> int {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn main() -> int {
    let count: int = 10;
    print("Fibonacci sequence:");

    let i: int = 0;
    while i < count {
        print(fibonacci(i));
        i = i + 1;
    }

    return 0;
}
```

## Compiler Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Source Code (.luna)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Lexical Analysis (Lexer/Scanner)                  │
│  - Reads source code character by character                  │
│  - Groups characters into tokens                             │
│  - Output: Token stream                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Syntax Analysis (Parser)                          │
│  - Reads token stream                                        │
│  - Builds Abstract Syntax Tree (AST)                         │
│  - Checks grammar rules                                      │
│  - Output: AST                                               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Semantic Analysis                                  │
│  - Type checking                                             │
│  - Symbol table management                                   │
│  - Scope resolution                                          │
│  - Output: Annotated AST                                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: Intermediate Representation (IR)                   │
│  - Three-Address Code (TAC)                                  │
│  - Platform-independent                                      │
│  - Output: IR instructions                                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Code Generation                                    │
│  - Generates target code                                     │
│  - Options: Python bytecode, C code, or interpreter          │
│  - Output: Executable program                                │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
compiler_project/
├── README.md                       ← This file
├── docs/
│   ├── LANGUAGE_SPEC.md           ← Luna language specification
│   ├── COMPILER_DESIGN.md         ← Compiler architecture
│   ├── LEXER_DESIGN.md            ← Lexical analysis details
│   ├── PARSER_DESIGN.md           ← Syntax analysis details
│   ├── SEMANTIC_ANALYSIS.md       ← Type checking & symbols
│   ├── IR_DESIGN.md               ← Intermediate representation
│   ├── CODE_GENERATION.md         ← Code generation strategies
│   ├── TESTING_GUIDE.md           ← Testing approach
│   └── BUILD_PHASES.md            ← Implementation roadmap
├── src/
│   ├── lexer/
│   │   ├── __init__.py
│   │   ├── token.py               ← Token definitions
│   │   └── lexer.py               ← Lexical analyzer
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── ast_nodes.py           ← AST node classes
│   │   └── parser.py              ← Recursive descent parser
│   ├── semantic/
│   │   ├── __init__.py
│   │   ├── symbol_table.py        ← Symbol table
│   │   ├── type_checker.py        ← Type checking
│   │   └── semantic_analyzer.py   ← Semantic analysis pass
│   ├── ir/
│   │   ├── __init__.py
│   │   ├── tac.py                 ← Three-address code
│   │   └── ir_generator.py        ← IR generation
│   ├── codegen/
│   │   ├── __init__.py
│   │   ├── interpreter.py         ← Tree-walking interpreter
│   │   ├── python_codegen.py      ← Python code generator
│   │   └── c_codegen.py           ← C code generator
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error.py               ← Error handling
│   │   └── position.py            ← Source position tracking
│   └── compiler.py                 ← Main compiler driver
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_semantic.py
│   ├── test_codegen.py
│   └── fixtures/
│       └── *.luna                  ← Test programs
├── examples/
│   ├── hello_world.luna
│   ├── fibonacci.luna
│   ├── factorial.luna
│   ├── calculator.luna
│   └── guess_game.luna
├── requirements.txt
├── .gitignore
└── luna.py                         ← CLI entry point
```

## Implementation Phases

### Phase 1: Lexical Analysis (Week 1)
- Define token types
- Implement lexer that converts source code to tokens
- Handle keywords, identifiers, literals, operators
- Add error reporting for invalid characters

### Phase 2: Syntax Analysis (Week 2)
- Design AST node classes
- Implement recursive descent parser
- Parse expressions (precedence climbing)
- Parse statements and functions
- Add syntax error recovery

### Phase 3: Semantic Analysis (Week 3)
- Build symbol table
- Implement scope management
- Add type checking
- Check function signatures
- Validate variable usage

### Phase 4: Intermediate Representation (Week 4)
- Design three-address code format
- Generate IR from AST
- Optimize IR (constant folding, dead code elimination)

### Phase 5: Code Generation (Week 5)
- Option 1: Tree-walking interpreter
- Option 2: Python bytecode generation
- Option 3: C code generation

### Phase 6: Testing & Optimization (Week 6)
- Write comprehensive test suite
- Add optimization passes
- Improve error messages
- Write example programs

## Getting Started

### Prerequisites
- Python 3.8+
- pytest (for testing)

### Installation

```bash
cd compiler_project
pip install -r requirements.txt
```

### Usage

```bash
# Compile and run a Luna program
python luna.py examples/hello_world.luna

# Compile to Python
python luna.py examples/fibonacci.luna --target python -o fib.py

# Compile to C
python luna.py examples/fibonacci.luna --target c -o fib.c

# Show tokens (debugging)
python luna.py examples/test.luna --tokens

# Show AST (debugging)
python luna.py examples/test.luna --ast

# Show IR (debugging)
python luna.py examples/test.luna --ir
```

## Learning Objectives

By building this compiler, you'll learn:

1. **Lexical Analysis**: Pattern matching, regular expressions, tokenization
2. **Parsing**: Grammars, recursive descent, operator precedence
3. **Type Systems**: Static typing, type checking, type inference
4. **Symbol Tables**: Scope management, name resolution
5. **Code Generation**: IR design, target code generation
6. **Error Handling**: Meaningful error messages, error recovery
7. **Software Architecture**: Modular design, separation of concerns
8. **Testing**: Unit tests, integration tests, test-driven development

## Resources

### Books
- "Crafting Interpreters" by Robert Nystrom
- "Engineering a Compiler" by Cooper & Torczon
- "Modern Compiler Implementation in ML/Java/C" by Andrew Appel
- "Compilers: Principles, Techniques, and Tools" (Dragon Book)

### Online
- [Luna Language Spec](docs/LANGUAGE_SPEC.md)
- [Compiler Design Guide](docs/COMPILER_DESIGN.md)
- [Implementation Roadmap](docs/BUILD_PHASES.md)

## Contributing

This is a learning project! Feel free to:
- Add new language features
- Improve error messages
- Add optimizations
- Write more example programs
- Improve documentation

## License

MIT License - Feel free to use this for learning!

## Acknowledgments

- Inspired by "Crafting Interpreters" by Robert Nystrom
- Language design influenced by Rust, Go, and TypeScript
- Built as a hands-on compiler construction learning project

---

**Start building:** Check out [docs/BUILD_PHASES.md](docs/BUILD_PHASES.md) for step-by-step implementation guide!
