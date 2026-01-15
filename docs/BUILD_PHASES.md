# Luna Compiler - Implementation Roadmap

This document provides a step-by-step guide to building the Luna compiler from scratch.

## Overview

We'll build the compiler in **6 phases** over approximately **6 weeks**. Each phase builds on the previous one, allowing you to test incrementally.

```
Week 1: Lexer      → Tokens
Week 2: Parser     → AST
Week 3: Semantic   → Type-checked AST
Week 4: IR         → Three-Address Code
Week 5: Codegen    → Executable
Week 6: Polish     → Production-ready
```

---

## Phase 1: Lexical Analysis (Week 1)

**Goal:** Convert source code text into a stream of tokens

### Tasks

#### 1.1: Token Definition
- [ ] Create `src/lexer/token.py`
- [ ] Define `TokenType` enum (all token types)
- [ ] Create `Token` class (type, value, position)
- [ ] Add position tracking (line, column)

#### 1.2: Lexer Implementation
- [ ] Create `src/lexer/lexer.py`
- [ ] Implement character stream reader
- [ ] Add whitespace skipping
- [ ] Implement comment handling (// and /*)
- [ ] Add keyword recognition
- [ ] Implement identifier scanning
- [ ] Add number literal scanning (int and float)
- [ ] Implement string literal scanning (with escapes)
- [ ] Add operator recognition
- [ ] Implement punctuation scanning

#### 1.3: Error Handling
- [ ] Create `src/utils/error.py`
- [ ] Add `LexerError` exception
- [ ] Implement error reporting with position
- [ ] Add helpful error messages

#### 1.4: Testing
- [ ] Write `tests/test_lexer.py`
- [ ] Test keyword recognition
- [ ] Test identifier scanning
- [ ] Test number literals
- [ ] Test string literals with escapes
- [ ] Test operators and punctuation
- [ ] Test comment handling
- [ ] Test error cases
- [ ] Aim for 100% coverage

### Example Test

```python
def test_basic_tokens():
    source = "let x: int = 42;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.LET
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "x"
    assert tokens[2].type == TokenType.COLON
    # ... etc
```

### Deliverables

✅ Lexer that converts source code to tokens
✅ Comprehensive error messages
✅ 100% test coverage for lexer
✅ Can run: `python -m lexer.lexer examples/hello.luna`

---

## Phase 2: Syntax Analysis (Week 2)

**Goal:** Build Abstract Syntax Tree (AST) from tokens

### Tasks

#### 2.1: AST Node Design
- [ ] Create `src/parser/ast_nodes.py`
- [ ] Define base `ASTNode` class
- [ ] Create expression nodes:
  - [ ] `LiteralExpr` (numbers, strings, bools)
  - [ ] `BinaryExpr` (a + b)
  - [ ] `UnaryExpr` (-a, !b)
  - [ ] `VariableExpr` (variable reference)
  - [ ] `CallExpr` (function call)
- [ ] Create statement nodes:
  - [ ] `VarDeclStmt`
  - [ ] `AssignmentStmt`
  - [ ] `IfStmt`
  - [ ] `WhileStmt`
  - [ ] `ReturnStmt`
  - [ ] `BlockStmt`
  - [ ] `ExprStmt`
- [ ] Create declaration nodes:
  - [ ] `FunctionDecl`
  - [ ] `Program`

#### 2.2: Parser Implementation
- [ ] Create `src/parser/parser.py`
- [ ] Implement recursive descent parser
- [ ] Add `parse_program()`
- [ ] Add `parse_function()`
- [ ] Add `parse_statement()` dispatcher
- [ ] Add `parse_expression()` with precedence
- [ ] Implement expression parsing:
  - [ ] `parse_primary()` (literals, identifiers)
  - [ ] `parse_call()` (function calls)
  - [ ] `parse_unary()` (-, !)
  - [ ] `parse_factor()` (*, /, %)
  - [ ] `parse_term()` (+, -)
  - [ ] `parse_comparison()` (<, >, <=, >=)
  - [ ] `parse_equality()` (==, !=)
  - [ ] `parse_logic_and()` (&&)
  - [ ] `parse_logic_or()` (||)
  - [ ] `parse_assignment()` (=)

#### 2.3: Error Handling
- [ ] Add `ParserError` exception
- [ ] Implement synchronization (error recovery)
- [ ] Add helpful error messages
- [ ] Show expected vs actual tokens

#### 2.4: Pretty Printing
- [ ] Add `__repr__()` methods to AST nodes
- [ ] Create AST visualizer
- [ ] Add indented tree printing

#### 2.5: Testing
- [ ] Write `tests/test_parser.py`
- [ ] Test expression parsing
- [ ] Test statement parsing
- [ ] Test function parsing
- [ ] Test operator precedence
- [ ] Test error recovery
- [ ] Test edge cases

### Example Test

```python
def test_parse_function():
    source = """
    fn add(a: int, b: int) -> int {
        return a + b;
    }
    """
    parser = Parser(Lexer(source).tokenize())
    ast = parser.parse()

    assert isinstance(ast.functions[0], FunctionDecl)
    assert ast.functions[0].name == "add"
    assert len(ast.functions[0].params) == 2
```

### Deliverables

✅ Parser that builds AST from tokens
✅ Handles all Luna language constructs
✅ Good error messages with recovery
✅ Can visualize AST
✅ Can run: `python -m parser.parser --ast examples/hello.luna`

---

## Phase 3: Semantic Analysis (Week 3)

**Goal:** Type check the AST and build symbol tables

### Tasks

#### 3.1: Symbol Table
- [ ] Create `src/semantic/symbol_table.py`
- [ ] Define `Symbol` class (name, type, scope)
- [ ] Create `SymbolTable` class
- [ ] Implement scope management (push/pop)
- [ ] Add symbol lookup (with scope chain)
- [ ] Add symbol insertion (with duplicate check)

#### 3.2: Type System
- [ ] Create `src/semantic/types.py`
- [ ] Define built-in types (int, float, bool, string, void)
- [ ] Add type compatibility checking
- [ ] Implement type equality

#### 3.3: Type Checker
- [ ] Create `src/semantic/type_checker.py`
- [ ] Implement visitor pattern for AST traversal
- [ ] Add type checking for expressions:
  - [ ] Literals (trivial)
  - [ ] Binary operations (arithmetic, comparison, logical)
  - [ ] Unary operations (-, !)
  - [ ] Variable references
  - [ ] Function calls
- [ ] Add type checking for statements:
  - [ ] Variable declarations
  - [ ] Assignments
  - [ ] If statements (bool condition)
  - [ ] While statements (bool condition)
  - [ ] Return statements (match function type)
- [ ] Check function declarations:
  - [ ] Parameter types
  - [ ] Return type
  - [ ] All code paths return (for non-void)

#### 3.4: Semantic Analyzer
- [ ] Create `src/semantic/semantic_analyzer.py`
- [ ] Build symbol table pass
- [ ] Run type checking pass
- [ ] Validate main() function exists
- [ ] Check for undefined variables
- [ ] Check for redeclarations

#### 3.5: Error Reporting
- [ ] Add `SemanticError` exception
- [ ] Create helpful error messages:
  - [ ] "Type mismatch: expected int, got string"
  - [ ] "Undefined variable 'x'"
  - [ ] "Function 'foo' expects 2 arguments but got 1"
  - [ ] "Cannot assign to constant"

#### 3.6: Testing
- [ ] Write `tests/test_semantic.py`
- [ ] Test type checking (valid cases)
- [ ] Test type errors (invalid cases)
- [ ] Test symbol table scoping
- [ ] Test undefined variable detection
- [ ] Test function signature validation

### Example Test

```python
def test_type_mismatch():
    source = """
    fn main() -> int {
        let x: int = "hello";  // Type error!
        return 0;
    }
    """
    with pytest.raises(SemanticError) as exc:
        compile_program(source, stop_after="semantic")
    assert "Type mismatch" in str(exc.value)
```

### Deliverables

✅ Symbol table with scope management
✅ Type checker that validates all operations
✅ Semantic error detection
✅ Helpful error messages
✅ Can run: `python -m semantic.semantic_analyzer examples/test.luna`

---

## Phase 4: Intermediate Representation (Week 4)

**Goal:** Generate platform-independent three-address code (TAC)

### Tasks

#### 4.1: TAC Design
- [ ] Create `src/ir/tac.py`
- [ ] Define `TACInstruction` class
- [ ] Create instruction types:
  - [ ] `Assign` (x = y)
  - [ ] `BinaryOp` (x = y op z)
  - [ ] `UnaryOp` (x = op y)
  - [ ] `Copy` (x = y)
  - [ ] `Goto` (unconditional jump)
  - [ ] `IfGoto` (conditional jump)
  - [ ] `Label` (jump target)
  - [ ] `Call` (function call)
  - [ ] `Return` (return value)
  - [ ] `Param` (function parameter)

#### 4.2: Temporary Variables
- [ ] Implement temporary variable generator (t0, t1, t2, ...)
- [ ] Implement label generator (L0, L1, L2, ...)

#### 4.3: IR Generator
- [ ] Create `src/ir/ir_generator.py`
- [ ] Implement AST-to-TAC translator
- [ ] Generate IR for expressions:
  - [ ] Literals → temporaries
  - [ ] Binary ops → three-address code
  - [ ] Function calls → param + call
- [ ] Generate IR for statements:
  - [ ] Assignments
  - [ ] If statements (with labels and jumps)
  - [ ] While loops (with labels and jumps)
  - [ ] Return statements
- [ ] Generate IR for functions

#### 4.4: IR Optimization (Optional)
- [ ] Constant folding (2 + 3 → 5)
- [ ] Dead code elimination
- [ ] Copy propagation

#### 4.5: IR Printing
- [ ] Add `__str__()` for TAC instructions
- [ ] Create IR pretty printer

#### 4.6: Testing
- [ ] Write `tests/test_ir.py`
- [ ] Test expression IR generation
- [ ] Test control flow IR
- [ ] Test function calls
- [ ] Verify correctness by inspection

### Example IR Output

```
// fn add(a: int, b: int) -> int { return a + b; }
FUNCTION add:
    t0 = a + b
    RETURN t0
END FUNCTION

// let x: int = (2 + 3) * 4;
t0 = 2 + 3
t1 = t0 * 4
x = t1
```

### Deliverables

✅ TAC instruction set
✅ IR generator from AST
✅ Human-readable IR output
✅ Can run: `python luna.py --ir examples/test.luna`

---

## Phase 5: Code Generation (Week 5)

**Goal:** Generate executable code from IR

**Choose ONE target:**
- Option A: Tree-walking interpreter (simplest)
- Option B: Python code generator (medium)
- Option C: C code generator (harder, but learn more)

### Option A: Tree-Walking Interpreter

#### 5A.1: Interpreter Implementation
- [ ] Create `src/codegen/interpreter.py`
- [ ] Implement environment (variable storage)
- [ ] Add evaluation for expressions
- [ ] Add execution for statements
- [ ] Implement function calls with stack
- [ ] Add built-in functions (print, input, len)

#### 5A.2: Runtime
- [ ] Implement call stack
- [ ] Add runtime type checking
- [ ] Handle runtime errors (division by zero, etc.)

#### 5A.3: Testing
- [ ] Test all language features
- [ ] Test recursion
- [ ] Test runtime errors

### Option B: Python Code Generator

#### 5B.1: Python Codegen
- [ ] Create `src/codegen/python_codegen.py`
- [ ] Generate Python code from AST or IR
- [ ] Map Luna types to Python types
- [ ] Generate function definitions
- [ ] Generate control flow
- [ ] Add main() wrapper

#### 5B.2: Testing
- [ ] Generate Python code
- [ ] Execute with `python generated.py`
- [ ] Verify output

### Option C: C Code Generator

#### 5C.1: C Codegen
- [ ] Create `src/codegen/c_codegen.py`
- [ ] Generate C code from IR
- [ ] Add standard library stubs
- [ ] Generate main() function
- [ ] Handle type conversions

#### 5C.2: Compilation
- [ ] Generate .c file
- [ ] Compile with gcc/clang
- [ ] Execute binary

### Deliverables

✅ Working code generator
✅ Can execute Luna programs
✅ All example programs work
✅ Can run: `python luna.py examples/hello.luna`

---

## Phase 6: Polish & Optimization (Week 6)

**Goal:** Make the compiler production-ready

### Tasks

#### 6.1: CLI Tool
- [ ] Create `luna.py` main entry point
- [ ] Add command-line argument parsing
- [ ] Add options: --tokens, --ast, --ir, --output
- [ ] Add version info, help text

#### 6.2: Error Messages
- [ ] Improve all error messages
- [ ] Add color-coded output
- [ ] Show source context for errors
- [ ] Add suggestions for common mistakes

#### 6.3: Optimizations
- [ ] Constant folding
- [ ] Dead code elimination
- [ ] Strength reduction (x * 2 → x + x)
- [ ] Common subexpression elimination

#### 6.4: Documentation
- [ ] Complete all docs/
- [ ] Add code comments
- [ ] Write tutorial
- [ ] Add more examples

#### 6.5: Testing
- [ ] Achieve >90% code coverage
- [ ] Add integration tests
- [ ] Test all example programs
- [ ] Add benchmarks

#### 6.6: Examples
- [ ] hello_world.luna
- [ ] fibonacci.luna
- [ ] factorial.luna
- [ ] fizzbuzz.luna
- [ ] calculator.luna
- [ ] guess_game.luna

### Deliverables

✅ Professional CLI tool
✅ Excellent error messages
✅ Comprehensive documentation
✅ 90%+ test coverage
✅ Multiple example programs

---

## Testing Strategy

### Unit Tests
- Test each phase independently
- Mock dependencies
- Aim for 100% coverage per module

### Integration Tests
- Test entire compiler pipeline
- Use real Luna programs
- Verify output correctness

### Example Programs as Tests
```python
def test_fibonacci_program():
    result = compile_and_run("examples/fibonacci.luna")
    assert result.exit_code == 0
    assert "55" in result.output  # fibonacci(10)
```

---

## Development Workflow

### For Each Phase:

1. **Read documentation** for that phase
2. **Write tests first** (TDD approach)
3. **Implement functionality** to pass tests
4. **Refactor** for clarity
5. **Document** your code
6. **Commit to Git** with clear message

### Example Git Workflow

```bash
# Starting Phase 1
git checkout -b phase-1-lexer

# Implement lexer
# ... write code, tests ...

# Commit
git add .
git commit -m "feat(lexer): implement token scanning and keyword recognition

- Added TokenType enum with all token types
- Implemented Lexer class with character stream
- Added keyword and identifier recognition
- Implemented number and string literal scanning
- Added comprehensive error messages
- Tests: 100% coverage for lexer module
"

# Merge to main when complete
git checkout main
git merge phase-1-lexer
git tag phase-1-complete
```

---

## Recommended Order

**Absolute beginners:**
1. Start with Phase 1 (Lexer)
2. Build Phase 2 (Parser) for expressions only first
3. Add statements to parser
4. Do Phase 3 (Semantic) for basic type checking
5. Choose Option A (Interpreter) for Phase 5
6. Skip Phase 4 (IR) initially

**Intermediate:**
Follow all phases in order, choose Option B or C for codegen

**Advanced:**
Implement all options for Phase 5, add optimizations

---

## Next Steps

**Ready to start?**

1. Read [LANGUAGE_SPEC.md](LANGUAGE_SPEC.md) to understand Luna
2. Read [LEXER_DESIGN.md](LEXER_DESIGN.md) for Phase 1 details
3. Create `src/lexer/token.py` and start implementing!

**Questions to answer while building:**
- How do operators work?
- How does scope work?
- How do function calls work?
- How do types work?
- How does code execute?

**You'll learn:**
- Pattern matching and tokenization
- Grammar and parsing algorithms
- Type systems and checking
- Code generation techniques
- Software architecture

**Good luck building your compiler!** 🚀
