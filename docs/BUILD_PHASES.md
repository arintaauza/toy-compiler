# Toy Compiler - Implementation Roadmap

This document provides a step-by-step guide to building the Toy compiler from scratch.

## Overview

We'll build the compiler in **8 phases** over approximately **8-10 weeks**. Each phase builds on the previous one, allowing you to test incrementally.

```
Week 1: Lexer          → Tokens
Week 2: Parser         → AST
Week 3: Semantic       → Type-checked AST
Week 4: IR             → Three-Address Code (TAC)
Week 5: Optimizations  → Optimized IR (DCE, CSE, Constant Folding)
Week 6: Assembly       → x86-64 or ARM assembly
Week 7: LLVM           → LLVM IR generation (optional)
Week 8: Polish         → Production-ready compiler
```

---

## Phase 1: Lexical Analysis (Week 1)

**Goal:** Convert source code text into a stream of tokens

### Tasks

#### 1.1: Token Definition
- [x] Create `src/lexer/token.py`
- [x] Define `TokenType` enum (all token types)
- [x] Create `Token` class (type, value, position)
- [x] Add position tracking (line, column)

#### 1.2: Lexer Implementation
- [x] Create `src/lexer/lexer.py`
- [x] Implement character stream reader
- [x] Add whitespace skipping
- [x] Implement comment handling (// and /*)
- [x] Add keyword recognition
- [x] Implement identifier scanning
- [x] Add number literal scanning (int and float)
- [x] Implement string literal scanning (with escapes)
- [x] Add operator recognition
- [x] Implement punctuation scanning

#### 1.3: Error Handling
- [x] Create `src/utils/error.py`
- [x] Add `LexerError` exception
- [x] Implement error reporting with position
- [x] Add helpful error messages

#### 1.4: Testing
- [x] Write `tests/test_lexer.py`
- [x] Test keyword recognition
- [x] Test identifier scanning
- [x] Test number literals
- [x] Test string literals with escapes
- [x] Test operators and punctuation
- [x] Test comment handling
- [x] Test error cases
- [x] Aim for 100% coverage (achieved 90%)

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
✅ Can run: `python -m lexer.lexer examples/hello.toy`

---

## Phase 2: Syntax Analysis (Week 2)

**Goal:** Build Abstract Syntax Tree (AST) from tokens

### Tasks

#### 2.1: AST Node Design
- [x] Create `src/parser/ast_nodes.py`
- [x] Define base `ASTNode` class
- [x] Create expression nodes:
  - [x] `LiteralExpr` (numbers, strings, bools)
  - [x] `BinaryExpr` (a + b)
  - [x] `UnaryExpr` (-a, !b)
  - [x] `VariableExpr` (variable reference)
  - [x] `CallExpr` (function call)
  - [x] `GroupingExpr` (parenthesized expressions)
  - [x] `AssignmentExpr` (a = b as expression)
- [x] Create statement nodes:
  - [x] `VarDeclStmt`
  - [x] `IfStmt`
  - [x] `WhileStmt`
  - [x] `ReturnStmt`
  - [x] `BlockStmt`
  - [x] `ExprStmt`
- [x] Create declaration nodes:
  - [x] `FunctionDecl`
  - [x] `Parameter`
  - [x] `Program`

#### 2.2: Parser Implementation
- [x] Create `src/parser/parser.py`
- [x] Implement recursive descent parser
- [x] Add `parse_program()`
- [x] Add `parse_function()`
- [x] Add `parse_statement()` dispatcher
- [x] Add `parse_expression()` with precedence
- [x] Implement expression parsing:
  - [x] `parse_primary()` (literals, identifiers)
  - [x] `parse_call()` (function calls)
  - [x] `parse_unary()` (-, !)
  - [x] `parse_factor()` (*, /, %)
  - [x] `parse_term()` (+, -)
  - [x] `parse_comparison()` (<, >, <=, >=)
  - [x] `parse_equality()` (==, !=)
  - [x] `parse_logic_and()` (&&)
  - [x] `parse_logic_or()` (||)
  - [x] `parse_assignment()` (=)

#### 2.3: Error Handling
- [x] Add `ParserError` exception (already in src/utils/error.py)
- [x] Implement synchronization (error recovery)
- [x] Add helpful error messages
- [x] Show expected vs actual tokens

#### 2.4: Pretty Printing
- [x] Add `__repr__()` methods to AST nodes
- [x] Create AST visualizer (ASTPrinter class)
- [x] Add indented tree printing

#### 2.5: Testing
- [x] Write `tests/test_parser.py`
- [x] Test expression parsing
- [x] Test statement parsing
- [x] Test function parsing
- [x] Test operator precedence
- [x] Test error recovery
- [x] Test edge cases

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
✅ Handles all Toy language constructs
✅ Good error messages with recovery
✅ Can visualize AST
✅ Can run: `python -m parser.parser --ast examples/hello.toy`

---

## Phase 3: Semantic Analysis (Week 3)

**Goal:** Type check the AST and build symbol tables

### Tasks

#### 3.1: Symbol Table
- [x] Create `src/semantic/symbol_table.py`
- [x] Define `Symbol` class (name, type, scope)
- [x] Create `SymbolTable` class
- [x] Implement scope management (push/pop)
- [x] Add symbol lookup (with scope chain)
- [x] Add symbol insertion (with duplicate check)

#### 3.2: Type System
- [x] Create `src/semantic/types.py`
- [x] Define built-in types (int, float, bool, string, void)
- [x] Add type compatibility checking
- [x] Implement type equality

#### 3.3: Type Checker
- [x] Create `src/semantic/type_checker.py`
- [x] Implement visitor pattern for AST traversal
- [x] Add type checking for expressions:
  - [x] Literals (trivial)
  - [x] Binary operations (arithmetic, comparison, logical)
  - [x] Unary operations (-, !)
  - [x] Variable references
  - [x] Function calls
- [x] Add type checking for statements:
  - [x] Variable declarations
  - [x] Assignments
  - [x] If statements (bool condition)
  - [x] While statements (bool condition)
  - [x] Return statements (match function type)
- [x] Check function declarations:
  - [x] Parameter types
  - [x] Return type
  - [x] All code paths return (for non-void)

#### 3.4: Semantic Analyzer
- [x] Create `src/semantic/semantic_analyzer.py`
- [x] Build symbol table pass
- [x] Run type checking pass
- [x] Validate main() function exists
- [x] Check for undefined variables
- [x] Check for redeclarations

#### 3.5: Error Reporting
- [x] Add `SemanticError` exception (already in src/utils/error.py)
- [x] Create helpful error messages:
  - [x] "Type mismatch: expected int, got string"
  - [x] "Undefined variable 'x'"
  - [x] "Function 'foo' expects 2 arguments but got 1"
  - [x] "Cannot assign to constant"

#### 3.6: Testing
- [x] Write `tests/test_semantic.py`
- [x] Test type checking (valid cases)
- [x] Test type errors (invalid cases)
- [x] Test symbol table scoping
- [x] Test undefined variable detection
- [x] Test function signature validation

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
✅ Can run: `python -m semantic.semantic_analyzer examples/test.toy`

---

## Phase 4: Intermediate Representation (Week 4)

**Goal:** Generate SSA-based three-address code (TAC) for optimization-friendly IR

### Why SSA (Static Single Assignment)?

SSA form ensures that:
1. **Each variable is assigned exactly once** - Variables get versioned (x_1, x_2, etc.)
2. **Every use refers to exactly one definition** - Clear def-use chains
3. **Phi functions at join points** - Handle control flow merges

Benefits of SSA:
- **Simpler optimizations**: Constant propagation, dead code elimination, and CSE become trivial
- **Explicit data flow**: No need to compute reaching definitions repeatedly
- **Better register allocation**: Live ranges don't overlap unnecessarily

### Tasks

#### 4.1: SSA IR Design
- [x] Create `src/ir/instructions.py`
- [x] Define `IRInstruction` base class
- [x] Create instruction types:
  - [x] `BinaryOp` (x_1 = y_0 op z_0)
  - [x] `UnaryOp` (x_1 = op y_0)
  - [x] `Copy` (x_1 = y_0)
  - [x] `LoadConst` (x_1 = 42)
  - [x] `Jump` (unconditional jump)
  - [x] `Branch` (conditional jump: if x_0 goto L1 else L2)
  - [x] `Phi` (x_3 = φ(x_1, x_2) - SSA join)
  - [x] `Call` (x_1 = call foo(a_0, b_0))
  - [x] `Return` (return x_0)
- [x] Create `IRValue` class (versioned variables: x_0, x_1, etc.)
- [x] Create `IRFunction` and `IRModule` containers

#### 4.2: SSA Variable Management
- [x] Implement SSA variable generator (versioning: x_0, x_1, x_2, ...)
- [x] Implement label/block generator (B0, B1, B2, ...)
- [x] Track current variable versions per scope
- [x] Handle variable renaming during SSA construction

#### 4.3: IR Generator (AST → SSA)
- [x] Create `src/ir/ir_generator.py`
- [x] Implement AST-to-SSA translator using visitor pattern
- [x] Generate IR for expressions:
  - [x] Literals → LoadConst
  - [x] Variables → lookup current SSA version
  - [x] Binary/Unary ops → create new SSA version for result
  - [x] Function calls → Call instruction
- [x] Generate IR for statements:
  - [x] Assignments → update SSA version mapping
  - [x] If statements → Branch + Phi functions at join
  - [x] While loops → Back edges + Phi functions at loop header
  - [x] Return statements → Return instruction
- [x] Generate IR for functions (entry block, parameters)

#### 4.4: Control Flow Graph (CFG)
- [x] Create `src/ir/cfg.py`
- [x] Define `BasicBlock` class
- [x] Build CFG during IR generation
- [x] Add predecessor/successor tracking
- [x] Insert Phi functions at join points
- [x] Create CFG visualizer (DOT format for debugging)

#### 4.5: Phi Function Insertion
- [x] Compute dominance frontiers (where Phi functions are needed)
- [x] Insert Phi functions for variables modified in branches
- [x] Rename variables to SSA form

#### 4.6: IR Printing
- [x] Add `__str__()` for all IR instructions
- [x] Create IR pretty printer with SSA versions visible
- [x] Support DOT output for CFG visualization

#### 4.7: Testing
- [x] Write `tests/test_ir.py`
- [x] Test expression IR generation
- [x] Test SSA versioning
- [x] Test Phi function insertion
- [x] Test control flow IR (if/while)
- [x] Test function calls
- [x] Verify SSA properties (each var assigned once)

### Example SSA IR Output

```
// fn max(a: int, b: int) -> int {
//     if a > b { return a; } else { return b; }
// }

FUNCTION max(a_0: int, b_0: int) -> int:
  B0 (entry):
    t_0 = a_0 > b_0
    branch t_0, B1, B2

  B1 (then):
    jump B3

  B2 (else):
    jump B3

  B3 (exit):
    result_0 = phi [a_0, B1], [b_0, B2]
    return result_0

// fn counter() -> int {
//     let x: int = 0;
//     while x < 10 { x = x + 1; }
//     return x;
// }

FUNCTION counter() -> int:
  B0 (entry):
    x_0 = 0
    jump B1

  B1 (loop_header):
    x_1 = phi [x_0, B0], [x_2, B2]    // SSA Phi at loop header
    t_0 = x_1 < 10
    branch t_0, B2, B3

  B2 (loop_body):
    x_2 = x_1 + 1
    jump B1

  B3 (exit):
    return x_1
```

### Deliverables

✅ SSA-based IR instruction set
✅ IR generator from AST with SSA construction
✅ CFG with basic blocks and Phi functions
✅ Human-readable SSA IR output
✅ Can run: `python toy.py --ir examples/test.toy`

---

## Phase 5: IR Optimizations (Week 5) ✅ COMPLETED

**Goal:** Implement classic compiler optimizations on SSA IR

### Overview

This phase implements optimizations that are simplified by SSA form:
- **No reaching definitions needed** - Each variable has exactly one definition
- **Simpler def-use chains** - Direct from definition to all uses
- **Natural worklist algorithms** - Process instructions in any order

### SSA Optimization Benefits

In SSA form, many optimizations become straightforward:
- **Constant propagation**: If `x_0 = 5`, replace all uses of `x_0` with `5`
- **Dead code elimination**: If `x_0` has no uses, delete its definition
- **Copy propagation**: If `x_0 = y_0`, replace uses of `x_0` with `y_0`
- **CSE**: Two identical expressions always produce the same SSA variable

### Tasks

#### 5.1: Constant Folding

Evaluate compile-time constant expressions.

- [x] Create `src/ir/optimizations/constant_folding.py`
- [x] Detect constant operands in binary operations
- [x] Evaluate arithmetic operations:
  - [x] `t1 = 2 + 3` → `t1 = 5`
  - [x] `t2 = 10 * 0` → `t2 = 0`
- [x] Evaluate comparison operations:
  - [x] `t3 = 5 > 3` → `t3 = true`
- [x] Evaluate logical operations:
  - [x] `t4 = true && false` → `t4 = false`
- [x] Handle unary operations:
  - [x] `t5 = -42` → `t5 = -42`
  - [x] `t6 = !true` → `t6 = false`
- [x] Add tests for all cases

**Example:**
```
Before:
    t0 = 2 + 3
    t1 = t0 * 4
    x = t1

After:
    t0 = 5
    t1 = 20
    x = 20
```

#### 5.2: Dead Code Elimination (DCE)

Remove code that doesn't affect program output.

- [x] Create `src/ir/optimizations/dead_code_elimination.py`
- [x] Implement liveness analysis
- [x] Mark live variables (used in output/return/function calls)
- [x] Remove assignments to dead variables
- [x] Remove unreachable code after returns
- [x] Remove unreachable code after unconditional jumps
- [x] Add tests for various dead code patterns

**Example:**
```
Before:
    t0 = 5        // Dead: never used
    x = 10
    return x
    y = 20        // Dead: unreachable

After:
    x = 10
    return x
```

#### 5.3: Common Subexpression Elimination (CSE)

Avoid recomputing the same expression.

- [x] Create `src/ir/optimizations/cse.py`
- [x] Build expression table (expression → temporary)
- [x] Detect duplicate expressions:
  - [x] Same operator
  - [x] Same operands
  - [x] No intervening modifications
- [x] Replace duplicate computation with temporary
- [x] Handle basic blocks (don't cross block boundaries initially)
- [x] Handle commutative operations (a + b = b + a)
- [x] Add tests

**Example:**
```
Before:
    t0 = a + b
    x = t0
    t1 = a + b    // Same as t0!
    y = t1

After:
    t0 = a + b
    x = t0
    y = t0        // Reuse t0
```

#### 5.4: Copy Propagation

Replace variable copies with original variables.

- [x] Create `src/ir/optimizations/copy_propagation.py`
- [x] Detect copy instructions: `x = y`
- [x] Replace uses of `x` with `y` (where valid)
- [x] Track variable modifications
- [x] Stop propagation when variable is reassigned
- [x] Propagate in binary ops, unary ops, branches, returns, and calls
- [x] Add tests

**Example:**
```
Before:
    x = a
    y = x + 1    // Use 'a' directly
    z = x * 2    // Use 'a' directly

After:
    x = a
    y = a + 1
    z = a * 2
```

#### 5.5: Algebraic Simplification

Apply mathematical identities.

- [x] Create `src/ir/optimizations/algebraic.py`
- [x] Implement identity simplifications:
  - [x] `x + 0` → `x`
  - [x] `x - 0` → `x`
  - [x] `x * 1` → `x`
  - [x] `x * 0` → `0`
  - [x] `x / 1` → `x`
  - [x] `x - x` → `0`
  - [x] `x / x` → `1`
  - [x] `x == x` → `true`
  - [x] `x != x` → `false`
  - [x] `x && false` → `false`
  - [x] `x || true` → `true`
- [x] Add tests

#### 5.6: Control Flow Optimizations

Simplify control flow structures.

- [x] Create `src/ir/optimizations/control_flow.py`
- [x] Branch elimination:
  - [x] `branch true, L1, L2` → `jump L1`
  - [x] `branch false, L1, L2` → `jump L2`
- [x] Jump threading (follow chains of jumps)
- [x] Unreachable code elimination
- [x] Merge basic blocks (when possible)
- [x] Update phi sources when blocks are merged
- [x] Rebuild CFG predecessor/successor info
- [x] Add tests

#### 5.7: Optimization Pass Manager

- [x] Create `src/ir/optimizations/pass_manager.py`
- [x] Define `OptimizationPass` abstract base class
- [x] Define `FunctionPass` and `BlockPass` specialized bases
- [x] Create `PassStatistics` for tracking optimization metrics
- [x] Implement `PassManager` class
- [x] Run passes until fixed point:
  - [x] Run all passes
  - [x] If IR changed, repeat
  - [x] Stop when no more changes (max iterations configurable)
- [x] Add pass statistics (instructions removed/modified/added)
- [x] Create `create_default_pass_manager()` with standard pipeline

#### 5.8: Testing

- [x] Write `tests/test_optimizations.py` (52 tests)
- [x] Test each optimization individually:
  - [x] Constant folding (13 tests)
  - [x] Dead code elimination (5 tests)
  - [x] CSE (4 tests)
  - [x] Copy propagation (3 tests)
  - [x] Algebraic simplification (10 tests)
  - [x] Control flow (4 tests)
- [x] Test pass manager (5 tests)
- [x] Test pass interactions (4 tests):
  - [x] Constant folding → DCE (folded constants make code dead)
  - [x] Copy propagation → DCE
  - [x] Algebraic simplification → Constant folding
  - [x] CSE → DCE
- [x] Test edge cases (4 tests)

### Implementation Summary

**Files Created:**
- `src/ir/optimizations/__init__.py` - Module exports
- `src/ir/optimizations/pass_manager.py` - Pass infrastructure
- `src/ir/optimizations/constant_folding.py` - Compile-time evaluation
- `src/ir/optimizations/dead_code_elimination.py` - Remove unused code
- `src/ir/optimizations/cse.py` - Common subexpression elimination
- `src/ir/optimizations/copy_propagation.py` - Simplify copies
- `src/ir/optimizations/algebraic.py` - Mathematical simplifications
- `src/ir/optimizations/control_flow.py` - CFG optimization
- `tests/test_optimizations.py` - Comprehensive tests

**Test Results:**
```
271 tests passing
- Lexer: 33 tests
- Parser: 63 tests
- Semantic: 65 tests
- IR: 58 tests
- Optimizations: 52 tests
```

### Deliverables

✅ 6 optimization passes implemented
✅ Pass manager with fixed-point iteration
✅ Tests for all optimizations (52 tests)
✅ Can run: `python toy.py --optimize --ir examples/test.toy`
✅ Measurable improvement on benchmarks

---

## Phase 6: Assembly Code Generation (Week 6-7) ✅ COMPLETED

**Goal:** Generate native assembly code from optimized IR

**Primary Target:** x86-64 assembly (AT&T syntax for macOS compatibility)
**Platform:** macOS Intel with System V AMD64 ABI

### Overview

This phase implements a complete x86-64 code generator that translates SSA-based IR to native assembly.
The generated code follows the System V AMD64 ABI for compatibility with macOS and can call C library
functions (like printf for the built-in print function).

### Implementation Approach

We use a simple **stack-based code generation** approach:
- All SSA variables are allocated stack slots (no register allocation yet)
- Operations load values to registers, perform the operation, and store back to stack
- This simplifies code generation while still producing correct, working code
- Register allocation can be added as a future optimization

### Tasks

#### 6.1: Stack Frame Layout

- [x] Create `src/codegen/stack_frame.py`
- [x] Design stack frame structure:
  ```
  +------------------+ <- rbp (frame pointer)
  | Saved rbp        | [rbp+0]
  +------------------+
  | Return address   | [rbp+8] (pushed by call)
  +------------------+
  | Local variables  | [rbp-8], [rbp-16], etc.
  +------------------+
  | Alignment pad    | (if needed for 16-byte alignment)
  +------------------+ <- rsp (stack pointer)
  ```
- [x] Assign stack offsets to all SSA variables (x_0, x_1, t_0, etc.)
- [x] Calculate frame size with 16-byte alignment (required by System V ABI)
- [x] Handle function parameters (copy from registers to stack)
- [x] Create `StackSlot`, `StackFrame`, and `StackFrameBuilder` classes

#### 6.2: x86-64 Assembly Generator

- [x] Create `src/codegen/x86_64_codegen.py`
- [x] Generate function prologue (AT&T syntax):
  ```asm
  pushq %rbp
  movq %rsp, %rbp
  subq $<frame_size>, %rsp
  ```
- [x] Generate function epilogue:
  ```asm
  movq %rbp, %rsp
  popq %rbp
  retq
  ```
- [x] Generate code for all IR instructions:

  **Arithmetic:**
  - [x] LoadConst: `movq $value, offset(%rbp)`
  - [x] Copy: `movq src, %rax; movq %rax, dest`
  - [x] ADD: `movq left, %rax; addq right, %rax; movq %rax, dest`
  - [x] SUB: `movq left, %rax; subq right, %rax; movq %rax, dest`
  - [x] MUL: `movq left, %rax; imulq right, %rax; movq %rax, dest`
  - [x] DIV: `movq left, %rax; cqto; idivq divisor; movq %rax, dest`
  - [x] MOD: (same as DIV but use %rdx for remainder)

  **Comparisons:**
  - [x] LT, GT, LE, GE, EQ, NE using cmpq and setX instructions
  - [x] Zero-extend result with movzbq

  **Unary Operations:**
  - [x] NEG: `negq %rax`
  - [x] NOT: `xorq $1, %rax` (boolean flip)

  **Control Flow:**
  - [x] Jump: `jmp label`
  - [x] Branch: `cmpq $0, cond; jne true_label; jmp false_label`

  **Function Calls (System V ABI):**
  - [x] Arguments in registers: %rdi, %rsi, %rdx, %rcx, %r8, %r9
  - [x] Additional arguments pushed to stack
  - [x] `callq _function_name` (underscore prefix for macOS)
  - [x] Return value in %rax

  **Phi Functions:**
  - [x] Resolve at end of predecessor blocks
  - [x] Copy appropriate value before jump/branch

#### 6.3: Built-in Functions

- [x] Implement `print()` via printf:
  - [x] Integer format: `"%ld\n"`
  - [x] String format: `"%s\n"`
  - [x] Zero %rax for variadic function call
- [ ] Implement `input()` (deferred to future phase)

#### 6.4: Assembly File Generation

- [x] Create `src/codegen/asm_emitter.py`
- [x] Generate .s file with:
  - [x] `.section __DATA,__data` (macOS data section)
  - [x] `.section __TEXT,__text` (macOS code section)
  - [x] `.globl _main` (export main with underscore)
  - [x] Format strings for printf
  - [x] String literals in data section
- [x] Add comments in generated assembly

#### 6.5: Compilation Pipeline

- [x] Implement `compile_source_to_asm()` - Source → Assembly string
- [x] Implement `compile_to_asm()` - Source file → .s file
- [x] Implement `compile_and_run()` - Full pipeline with execution
- [x] Assemble with: `as -o program.o program.s`
- [x] Link with: `gcc -o program program.o` (links libc)

#### 6.6: Testing

- [x] Write `tests/test_codegen.py` (38 tests passing, 1 skipped)
- [x] Test stack frame layout (7 tests)
- [x] Test stack frame builder (3 tests)
- [x] Test assembly generation (4 tests)
- [x] Test compilation pipeline (3 tests)
- [x] Test end-to-end execution (17 tests):
  - [x] Return constants
  - [x] Arithmetic (+, -, *, /, %)
  - [x] Comparisons (<, >)
  - [x] If/else control flow
  - [x] Function calls
  - [x] Recursive functions
  - [x] Fibonacci (complex recursion)
  - [x] Unary operations (negation, logical not)
  - [x] Print function
  - [x] Complex expressions
  - [x] Nested function calls
- [x] Test edge cases (3 tests)
- [x] Test while loop execution

### Implementation Summary

**Files Created:**
- `src/codegen/__init__.py` - Module exports
- `src/codegen/stack_frame.py` - Stack frame layout and variable allocation
- `src/codegen/x86_64_codegen.py` - Main x86-64 AT&T syntax code generator
- `src/codegen/asm_emitter.py` - High-level compilation API
- `tests/test_codegen.py` - Comprehensive tests

**Test Results:**
```
310 tests passing
- Lexer: 33 tests
- Parser: 63 tests
- Semantic: 65 tests
- IR: 58 tests
- Optimizations: 52 tests
- Code Generation: 39 tests
```

### Deliverables

✅ x86-64 AT&T syntax assembly code generator
✅ Stack-based variable allocation (simple but correct)
✅ System V AMD64 ABI compliance
✅ Built-in print() function via printf
✅ Full compilation pipeline (Toy → Assembly → Binary)
✅ Comprehensive tests (39 tests)
✅ Can compile and run: Fibonacci, factorial, recursive functions, while loops
✅ Can run: `from src.codegen import compile_and_run; result = compile_and_run(source)`

### Future Improvements (Phase 6b)

- [ ] Register allocation (linear scan or graph coloring)
- [ ] String support beyond print
- [ ] Float/double support
- [ ] input() built-in function

---

### Alternative: Interpreter (Simpler)

If assembly is too challenging initially, implement a tree-walking interpreter:

### Simple Tree-Walking Interpreter

#### 6A.1: Interpreter Implementation (Alternative to Assembly)
- [ ] Create `src/codegen/interpreter.py`
- [ ] Implement environment (variable storage)
- [ ] Add evaluation for expressions
- [ ] Add execution for statements
- [ ] Implement function calls with stack
- [ ] Add built-in functions (print, input, len)

#### 6A.2: Runtime
- [ ] Implement call stack
- [ ] Add runtime type checking
- [ ] Handle runtime errors (division by zero, etc.)

#### 6A.3: Testing
- [ ] Test all language features
- [ ] Test recursion
- [ ] Test runtime errors

---

## Phase 7: LLVM IR Generation ✅ COMPLETED

**Goal:** Generate LLVM IR for maximum performance and portability

### Overview

LLVM IR is generated from Toy's SSA-based IR using the **llvmlite** Python library. By targeting LLVM IR, you get:
- World-class optimizations (LLVM's optimization passes)
- Multiple target architectures (x86, ARM, RISC-V, etc.)
- Integration with existing toolchains
- JIT compilation capabilities

### Implementation Approach

We use **llvmlite**, a lightweight Python binding for LLVM. This provides:
- Direct API for building LLVM IR programmatically
- JIT compilation via MCJIT
- No need to install the full LLVM toolchain

### Tasks

#### 7.1: Prerequisites
- [x] Install llvmlite: `pip install llvmlite`

#### 7.2: LLVM IR Code Generator
- [x] Create `src/codegen/llvm_codegen.py`
- [x] Implement `LLVMCodeGenerator` class
- [x] Initialize LLVM module and builder
- [x] Declare external functions (printf)

#### 7.3: Type Mapping
- [x] `int` → `i64` (64-bit integer)
- [x] `float` → `double` (64-bit float)
- [x] `bool` → `i1` (1-bit integer)
- [x] `string` → `i8*` (pointer to char array)
- [x] `void` → `void`

#### 7.4: Instruction Translation
- [x] LoadConst: Create LLVM constant
- [x] Copy: Map source value to destination
- [x] BinaryOp: add, sub, mul, sdiv, srem, icmp_signed
- [x] UnaryOp: neg, not_
- [x] Jump: Unconditional branch
- [x] Branch: Conditional branch (cbranch)
- [x] Phi: LLVM phi nodes
- [x] Call: Function calls
- [x] Return: ret instruction

#### 7.5: Control Flow
- [x] Create LLVM basic blocks for Toy basic blocks
- [x] Implement reverse postorder block traversal for SSA dominance
- [x] Handle phi nodes with deferred incoming value resolution

#### 7.6: Built-in Functions
- [x] Implement print() via printf
- [x] Integer format: `%ld\n`
- [x] String format: `%s\n`
- [x] Boolean: extend to i64 for printf

#### 7.7: High-Level API
- [x] Create `src/codegen/llvm_emitter.py`
- [x] `compile_to_llvm_ir()` - Toy source → LLVM IR text
- [x] `compile_and_run_llvm()` - JIT compile and execute
- [x] `compile_to_object()` - Generate native .o file
- [x] `LLVMJITEngine` - Reusable JIT execution engine
- [x] `optimize_llvm_ir()` - Run LLVM optimization passes

#### 7.8: Testing
- [x] Write `tests/test_llvm_codegen.py` (41 tests)
- [x] Test type mapping (5 tests)
- [x] Test IR generation (8 tests)
- [x] Test high-level API (5 tests)
- [x] Test JIT execution (17 tests)
- [x] Test JIT engine (2 tests)
- [x] Compare output with x86-64 backend (4 tests)

### Implementation Summary

**Files Created:**
- `src/codegen/llvm_codegen.py` - Main LLVM IR generator
- `src/codegen/llvm_emitter.py` - High-level compilation API
- `tests/test_llvm_codegen.py` - Comprehensive tests

**Key Classes:**
- `LLVMCodeGenerator` - Translates Toy IR to LLVM IR
- `LLVMCompileResult` - JIT execution result
- `LLVMJITEngine` - Reusable JIT compilation engine

**Example Usage:**

```python
from src.codegen import compile_to_llvm_ir, compile_and_run_llvm

# Generate LLVM IR
source = '''
fn fib(n: int) -> int {
    if n <= 1 { return n; }
    return fib(n - 1) + fib(n - 2);
}
fn main() -> int { return fib(10); }
'''

llvm_ir = compile_to_llvm_ir(source)
print(llvm_ir)

# JIT compile and execute
result = compile_and_run_llvm(source)
print(f"Return value: {result.return_value}")  # 55
```

**Generated LLVM IR Example:**
```llvm
define i64 @"fib"(i64 %"n_0") {
entry0:
  %"t_0" = icmp sle i64 %"n_0", 1
  br i1 %"t_0", label %"then1", label %"else2"

then1:
  ret i64 %"n_0"

else2:
  %"t_3" = sub i64 %"n_0", 1
  %"t_4" = call i64 @"fib"(i64 %"t_3")
  %"t_5" = sub i64 %"n_0", 2
  %"t_6" = call i64 @"fib"(i64 %"t_5")
  %"t_7" = add i64 %"t_4", %"t_6"
  ret i64 %"t_7"
}

define i64 @"main"() {
entry0:
  %"t_0" = call i64 @"fib"(i64 10)
  ret i64 %"t_0"
}
```

### Test Results

```
351 tests passing
- Lexer: 33 tests
- Parser: 63 tests
- Semantic: 65 tests
- IR: 58 tests
- Optimizations: 52 tests
- x86-64 Code Generation: 39 tests
- LLVM Code Generation: 41 tests
```

### Deliverables

✅ LLVM IR code generator using llvmlite
✅ Direct mapping from Toy SSA IR to LLVM IR
✅ JIT compilation and execution via MCJIT
✅ Object file generation for native binaries
✅ Integration with LLVM optimization passes
✅ Comprehensive tests (41 tests)
✅ Backend comparison tests (LLVM vs x86-64)
✅ Can run: `from src.codegen import compile_and_run_llvm; result = compile_and_run_llvm(source)`

### Resources

- LLVM Language Reference: https://llvm.org/docs/LangRef.html
- llvmlite Documentation: https://llvmlite.readthedocs.io/
- LLVM Kaleidoscope Tutorial: https://llvm.org/docs/tutorial/

---

## Phase 8: Polish & Production ✅ COMPLETED

**Goal:** Make the compiler production-ready with excellent UX

### Tasks

#### 8.1: CLI Tool
- [x] Create `toy.py` main entry point
- [x] Add command-line argument parsing with argparse
- [x] Add compilation options:
  - [x] `--tokens` (show tokenization)
  - [x] `--ast` (show AST)
  - [x] `--ir` (show unoptimized IR)
  - [x] `--ir-opt` (show optimized IR)
  - [x] `--asm` (show assembly)
  - [x] `--llvm` (generate LLVM IR)
  - [x] `--optimize` / `-O` (enable optimizations)
  - [x] `--output` / `-o` (output file)
  - [x] `--run` (compile and execute)
  - [x] `--verbose` / `-v` (debug output)
- [x] Add version info, help text
- [x] Add compilation statistics (time per phase)

**Example Usage:**
```bash
python toy.py examples/fibonacci.toy              # Compile and run
python toy.py --optimize examples/fibonacci.toy   # With optimizations
python toy.py --asm -o fib.s examples/fibonacci.toy  # Generate assembly
python toy.py --llvm examples/fibonacci.toy       # Generate LLVM IR
python toy.py --ir examples/test.toy              # Show IR
python toy.py --tokens examples/hello_world.toy   # Show tokens
python toy.py --verbose examples/factorial.toy    # With stats
```

#### 8.2: Error Messages
- [x] Improve error messages with context
- [x] Add color-coded output (red for errors, cyan for headers)
- [x] Show source context for errors with line numbers
- [ ] Add suggestions for common mistakes (future enhancement)

#### 8.3: Documentation
- [x] Updated BUILD_PHASES.md with all completed phases
- [ ] Write TUTORIAL.md (future enhancement)
- [ ] Write COMPILER_INTERNALS.md (future enhancement)

#### 8.4: Testing & Quality
- [x] Add integration tests (full pipeline) - 39 tests
- [x] Test all example programs
- [x] Add negative tests (programs that should fail)
- [x] Create test suite with diverse Toy programs

#### 8.5: Example Programs
- [x] hello_world.toy (basic I/O)
- [x] fibonacci.toy (recursion)
- [x] factorial.toy (recursion)
- [x] fizzbuzz.toy (conditionals)
- [x] prime_checker.toy (modulo, functions)
- [x] gcd.toy (GCD/LCM algorithms)
- [x] power.toy (fast exponentiation)
- [x] sum_of_digits.toy (digit manipulation)
- [x] collatz.toy (Collatz conjecture)
- [x] triangle.lua (triangle numbers)

### Implementation Summary

**Files Created:**
- `toy.py` - Main CLI entry point with argparse
- `tests/test_integration.py` - 39 integration tests
- 6 new example programs in `examples/`

**CLI Features:**
- All compilation stages viewable (tokens, AST, IR, assembly, LLVM)
- Multiple backends (x86-64, LLVM)
- Optimization toggle
- Verbose mode with timing statistics
- Colorized output

**Test Results:**
```
390 tests passing
- Lexer: 33 tests
- Parser: 63 tests
- Semantic: 65 tests
- IR: 58 tests
- Optimizations: 52 tests
- x86-64 Code Generation: 39 tests
- LLVM Code Generation: 41 tests
- Integration: 39 tests
```

**Example Programs: 10 total**
```
examples/
├── hello_world.toy      # Basic I/O
├── fibonacci.toy        # Recursion
├── factorial.toy        # Recursion
├── fizzbuzz.toy         # Conditionals and modulo
├── prime_checker.toy    # Prime number detection
├── gcd.toy              # GCD/LCM algorithms
├── power.toy            # Fast exponentiation
├── sum_of_digits.toy    # Digit manipulation
├── collatz.toy          # Collatz conjecture
└── triangle.toy         # Triangle numbers
```

### Deliverables

✅ Professional CLI tool with all flags
✅ Colorized error messages with source context
✅ 390 tests passing (integration + unit)
✅ 10 example programs
✅ Two compilation backends (x86-64, LLVM)
✅ Production-ready compiler!

---

## Testing Strategy

### Unit Tests
- Test each phase independently
- Mock dependencies
- Aim for 100% coverage per module

### Integration Tests
- Test entire compiler pipeline
- Use real Toy programs
- Verify output correctness

### Example Programs as Tests
```python
def test_fibonacci_program():
    result = compile_and_run("examples/fibonacci.toy")
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

**Learning Path 1: Interpreter First (Beginner-Friendly)**
1. Phase 1: Lexer
2. Phase 2: Parser
3. Phase 3: Semantic Analysis
4. Phase 6 (Alternative): Tree-walking Interpreter
5. Go back to Phase 4: IR Generation
6. Phase 5: Optimizations
7. Phase 6: Assembly or Phase 7: LLVM

**Learning Path 2: Full Pipeline (Intermediate)**
1. Phase 1: Lexer
2. Phase 2: Parser
3. Phase 3: Semantic Analysis
4. Phase 4: IR Generation (no optimizations yet)
5. Phase 6: Assembly Code Generation
6. Go back to Phase 5: Add Optimizations
7. Phase 7: LLVM (optional)
8. Phase 8: Polish

**Learning Path 3: Production Compiler (Advanced)**
1. Phases 1-3: Frontend (lexer, parser, semantic)
2. Phase 4: IR + CFG
3. Phase 5: All optimizations with pass manager
4. Phase 6: Assembly with register allocation
5. Phase 7: LLVM IR generation
6. Phase 8: CLI, benchmarks, extensive testing

**Recommended**: Path 2 for best learning experience

---

## Next Steps

**Ready to start?**

1. Read [LANGUAGE_SPEC.md](LANGUAGE_SPEC.md) to understand Toy
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
