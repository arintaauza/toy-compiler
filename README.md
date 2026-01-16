# Luna Compiler

A complete compiler for **Luna**, a statically-typed programming language, built from scratch in Python.

## Features

- **Full compilation pipeline**: Lexer, Parser, Semantic Analysis, IR Generation, Optimization, Code Generation
- **Two backends**: x86-64 native assembly and LLVM IR
- **SSA-based IR**: Static Single Assignment form with phi functions
- **6 optimization passes**: Constant folding, DCE, CSE, copy propagation, algebraic simplification, control flow
- **390 tests** with comprehensive coverage

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run a Luna program
python luna.py examples/fibonacci.luna

# With optimizations
python luna.py -O examples/fibonacci.luna

# Show generated LLVM IR
python luna.py --llvm examples/fibonacci.luna
```

## Example Luna Program

```luna
fn fibonacci(n: int) -> int {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn main() -> int {
    let i: int = 0;
    while i <= 10 {
        print(fibonacci(i));
        i = i + 1;
    }
    return 0;
}
```

## Language Features

| Feature | Syntax |
|---------|--------|
| Variables | `let x: int = 42;` |
| Functions | `fn add(a: int, b: int) -> int { return a + b; }` |
| If/Else | `if x > 0 { ... } else { ... }` |
| While | `while i < 10 { ... }` |
| Types | `int`, `float`, `bool`, `string`, `void` |
| Operators | `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `\|\|`, `!` |
| Print | `print(value);` |
| Comments | `// single-line` and `/* multi-line */` |

## CLI Usage

```bash
python luna.py [options] <file.luna>

Options:
  --tokens      Show lexer output
  --ast         Show parsed AST
  --ir          Show unoptimized IR
  --ir-opt      Show optimized IR
  --asm         Show x86-64 assembly
  --llvm        Show LLVM IR
  -O            Enable optimizations
  -o FILE       Output to file
  -v            Verbose mode (timing stats)
  --backend     Choose backend: x86 (default) or llvm
  --no-color    Disable colored output
```

## Project Structure

```
compiler_project/
├── luna.py                 # CLI entry point
├── src/
│   ├── lexer/              # Tokenization
│   ├── parser/             # AST construction
│   ├── semantic/           # Type checking
│   ├── ir/                 # SSA IR generation
│   │   └── optimizations/  # Optimization passes
│   ├── codegen/            # x86-64 and LLVM backends
│   └── utils/              # Error handling
├── tests/                  # 390 tests
├── examples/               # 10 example programs
└── docs/                   # Documentation
```

## Compiler Pipeline

```
Source (.luna)
    |
    v
[1] Lexer -----------> Tokens
    |
    v
[2] Parser ----------> AST
    |
    v
[3] Semantic --------> Type-checked AST + Symbol Table
    |
    v
[4] IR Generator ----> SSA IR + CFG
    |
    v
[5] Optimizer -------> Optimized IR
    |
    +---> [6] x86-64 Codegen ---> Native Binary
    |
    +---> [7] LLVM Codegen -----> LLVM IR ---> Native Binary
```

## Tests

```bash
# Run all tests
python -m pytest

# Run specific phase
python -m pytest tests/test_semantic.py -v

# With coverage
python -m pytest --cov=src
```

Test breakdown:
- Lexer: 33 tests
- Parser: 63 tests
- Semantic: 65 tests
- IR: 58 tests
- Optimizations: 52 tests
- x86-64 Codegen: 39 tests
- LLVM Codegen: 41 tests
- Integration: 39 tests

## Documentation

- [LANGUAGE_SPEC.md](docs/LANGUAGE_SPEC.md) - Luna language specification
- [COMPILER_DESIGN.md](docs/COMPILER_DESIGN.md) - Architecture overview
- [COMPILER_INTERNALS.md](docs/COMPILER_INTERNALS.md) - Type system, IR, optimizations
- [BUILD_PHASES.md](docs/BUILD_PHASES.md) - Implementation roadmap

## Dependencies

- Python 3.8+
- pytest
- llvmlite (for LLVM backend)

## License

MIT License
