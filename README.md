# Toy Compiler

A complete compiler for **Toy**, a simple statically-typed programming language built for learning compiler construction.

## Features

- **Full compilation pipeline**: Lexer, Parser, Semantic Analysis, IR Generation, Optimization, Code Generation
- **Two backends**: x86-64 native assembly and LLVM IR
- **SSA-based IR**: Static Single Assignment form with phi functions
- **6 optimization passes**: Constant folding, DCE, CSE, copy propagation, algebraic simplification, control flow
- **390 tests** with comprehensive coverage

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/toy-compiler.git
cd toy-compiler

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the compiler
pip install -e .
```

After installation, the `toy` command is available:

```bash
toy examples/fibonacci.toy
```

## Quick Start

```bash
# Run a Toy program
toy examples/fibonacci.toy

# With optimizations
toy -O examples/fibonacci.toy

# Show generated LLVM IR
toy --llvm examples/fibonacci.toy

# Show x86-64 assembly
toy --asm examples/factorial.toy
```

## Example Toy Program

```toy
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
toy [options] <file.toy>

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
  --help        Show help message
  --version     Show version
```

## Project Structure

```
toy-compiler/
├── toy.py                  # CLI entry point
├── pyproject.toml          # Package configuration
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
Source (.toy)
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
pytest

# Run specific phase
pytest tests/test_semantic.py -v

# With coverage
pytest --cov=src
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

- [LANGUAGE_SPEC.md](docs/LANGUAGE_SPEC.md) - Toy language specification
- [COMPILER_DESIGN.md](docs/COMPILER_DESIGN.md) - Architecture overview
- [COMPILER_INTERNALS.md](docs/COMPILER_INTERNALS.md) - Type system, IR, optimizations

## Requirements

- Python 3.8+
- llvmlite (installed automatically)

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run specific example
toy examples/prime_checker.toy
```

## License

MIT License
