# Luna Compiler - Implementation Roadmap

This document provides a step-by-step guide to building the Luna compiler from scratch.

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

#### 4.4: Control Flow Graph (CFG)
- [ ] Create `src/ir/cfg.py`
- [ ] Build CFG from TAC (basic blocks + edges)
- [ ] Implement basic block creation
- [ ] Add predecessor/successor tracking
- [ ] Create CFG visualizer (for debugging)

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

## Phase 5: IR Optimizations (Week 5)

**Goal:** Implement classic compiler optimizations on TAC

### Overview

This phase implements the most important optimizations that make compiled code faster and smaller. Each optimization is a transformation pass over the IR.

### Tasks

#### 5.1: Constant Folding

Evaluate compile-time constant expressions.

- [ ] Create `src/ir/optimizations/constant_folding.py`
- [ ] Detect constant operands in binary operations
- [ ] Evaluate arithmetic operations:
  - [ ] `t1 = 2 + 3` → `t1 = 5`
  - [ ] `t2 = 10 * 0` → `t2 = 0`
- [ ] Evaluate comparison operations:
  - [ ] `t3 = 5 > 3` → `t3 = true`
- [ ] Evaluate logical operations:
  - [ ] `t4 = true && false` → `t4 = false`
- [ ] Handle unary operations:
  - [ ] `t5 = -42` → `t5 = -42`
  - [ ] `t6 = !true` → `t6 = false`
- [ ] Add tests for all cases

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

- [ ] Create `src/ir/optimizations/dead_code_elimination.py`
- [ ] Implement liveness analysis
- [ ] Mark live variables (used in output/return/function calls)
- [ ] Remove assignments to dead variables
- [ ] Remove unreachable code after returns
- [ ] Remove unreachable code after unconditional jumps
- [ ] Add tests for various dead code patterns

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

- [ ] Create `src/ir/optimizations/cse.py`
- [ ] Build expression table (expression → temporary)
- [ ] Detect duplicate expressions:
  - [ ] Same operator
  - [ ] Same operands
  - [ ] No intervening modifications
- [ ] Replace duplicate computation with temporary
- [ ] Handle basic blocks (don't cross block boundaries initially)
- [ ] Add tests

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

- [ ] Create `src/ir/optimizations/copy_propagation.py`
- [ ] Detect copy instructions: `x = y`
- [ ] Replace uses of `x` with `y` (where valid)
- [ ] Track variable modifications
- [ ] Stop propagation when variable is reassigned
- [ ] Add tests

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

- [ ] Create `src/ir/optimizations/algebraic.py`
- [ ] Implement identity simplifications:
  - [ ] `x + 0` → `x`
  - [ ] `x - 0` → `x`
  - [ ] `x * 1` → `x`
  - [ ] `x * 0` → `0`
  - [ ] `x / 1` → `x`
- [ ] Implement strength reduction:
  - [ ] `x * 2` → `x + x`
  - [ ] `x * 4` → `x << 2` (if targeting assembly)
- [ ] Implement constant hoisting
- [ ] Add tests

#### 5.6: Control Flow Optimizations

Simplify control flow structures.

- [ ] Create `src/ir/optimizations/control_flow.py`
- [ ] Branch elimination:
  - [ ] `if true goto L1` → `goto L1`
  - [ ] `if false goto L1` → remove instruction
- [ ] Unreachable code after unconditional jumps
- [ ] Merge basic blocks (when possible)
- [ ] Remove empty blocks
- [ ] Add tests

#### 5.7: Optimization Pass Manager

- [ ] Create `src/ir/optimizations/pass_manager.py`
- [ ] Define optimization pass interface
- [ ] Implement pass ordering (some passes enable others)
- [ ] Run passes until fixed point:
  - [ ] Run all passes
  - [ ] If IR changed, repeat
  - [ ] Stop when no more changes
- [ ] Add pass statistics (how many optimizations applied)
- [ ] Add `--optimize` flag to CLI

#### 5.8: Testing

- [ ] Write `tests/test_optimizations.py`
- [ ] Test each optimization individually
- [ ] Test pass interactions:
  - [ ] Constant folding → DCE (folded constants make code dead)
  - [ ] Copy propagation → CSE (more opportunities)
- [ ] Test fixed-point iteration
- [ ] Benchmark: measure speedup on example programs

### Deliverables

✅ 6 optimization passes implemented
✅ Pass manager with fixed-point iteration
✅ Tests for all optimizations
✅ Can run: `python luna.py --optimize --ir examples/test.luna`
✅ Measurable improvement on benchmarks

---

## Phase 6: Assembly Code Generation (Week 6-7)

**Goal:** Generate native assembly code from optimized IR

**Primary Target:** x86-64 assembly (AT&T or Intel syntax)
**Alternative:** ARM64 assembly (if on Apple Silicon)

### Overview

This is the most educational backend - you'll learn how high-level code maps to actual machine instructions.

### Tasks

#### 6.1: Register Allocation

- [ ] Create `src/codegen/register_allocator.py`
- [ ] Implement linear scan register allocation
- [ ] Available registers (x86-64):
  - [ ] General purpose: rax, rbx, rcx, rdx, rsi, rdi, r8-r15
  - [ ] Reserved: rbp (frame pointer), rsp (stack pointer)
- [ ] Spill to stack when out of registers
- [ ] Track register usage per basic block
- [ ] Add tests

#### 6.2: Stack Frame Layout

- [ ] Design stack frame structure:
  ```
  +------------------+ <- rbp (frame pointer)
  | Local variables  |
  +------------------+
  | Spilled temps    |
  +------------------+
  | Saved registers  |
  +------------------+
  | Return address   | <- pushed by call
  +------------------+ <- rsp (stack pointer)
  ```
- [ ] Calculate offsets for locals
- [ ] Calculate frame size

#### 6.3: x86-64 Assembly Generator

- [ ] Create `src/codegen/x86_64_codegen.py`
- [ ] Generate function prologue:
  ```asm
  push rbp
  mov rbp, rsp
  sub rsp, <frame_size>
  ```
- [ ] Generate function epilogue:
  ```asm
  mov rsp, rbp
  pop rbp
  ret
  ```
- [ ] Generate code for TAC instructions:

  **Arithmetic:**
  - [ ] `x = y + z` → `mov rax, [y]; add rax, [z]; mov [x], rax`
  - [ ] `x = y - z` → `mov rax, [y]; sub rax, [z]; mov [x], rax`
  - [ ] `x = y * z` → `mov rax, [y]; imul rax, [z]; mov [x], rax`
  - [ ] `x = y / z` → `mov rax, [y]; cqo; idiv [z]; mov [x], rax`

  **Comparisons:**
  - [ ] `x = y < z` → `mov rax, [y]; cmp rax, [z]; setl al; movzx rax, al; mov [x], rax`
  - [ ] Similar for `>`, `<=`, `>=`, `==`, `!=`

  **Control Flow:**
  - [ ] `goto L` → `jmp L`
  - [ ] `if x goto L` → `cmp [x], 0; jne L`
  - [ ] `label L:` → `L:`

  **Function Calls (System V ABI):**
  - [ ] Arguments in registers: rdi, rsi, rdx, rcx, r8, r9
  - [ ] Additional arguments on stack
  - [ ] `call function_name`
  - [ ] Return value in rax

#### 6.4: Built-in Functions

- [ ] Implement `print()` (call printf/puts)
- [ ] Implement `input()` (call scanf)
- [ ] Link with C standard library

#### 6.5: Assembly File Generation

- [ ] Create `src/codegen/asm_emitter.py`
- [ ] Generate .s file with:
  - [ ] `.section .text` (code section)
  - [ ] `.section .data` (data section for strings)
  - [ ] `.globl main` (export main)
  - [ ] Proper labels and formatting
- [ ] Add comments in generated assembly

#### 6.6: Compilation & Linking

- [ ] Create compilation script
- [ ] Generate .s file from IR
- [ ] Assemble with: `as -o program.o program.s`
- [ ] Link with: `gcc -o program program.o` (links libc)
- [ ] Execute: `./program`

#### 6.7: Testing

- [ ] Write `tests/test_codegen.py`
- [ ] Test instruction generation
- [ ] Test register allocation
- [ ] Test full pipeline:
  - [ ] Compile Luna → Assembly → Binary
  - [ ] Run binary
  - [ ] Verify output
- [ ] Test all example programs

### Deliverables

✅ x86-64 assembly code generator
✅ Register allocator
✅ Can compile Luna to native executable
✅ All example programs produce correct output
✅ Can run: `python luna.py -o program examples/fibonacci.luna && ./program`

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

## Phase 7: LLVM IR Generation (Week 7-8, Optional)

**Goal:** Generate LLVM IR for maximum performance and portability

### Overview

LLVM IR is a low-level intermediate representation used by the LLVM compiler infrastructure. By targeting LLVM IR, you get:
- World-class optimizations (LLVM's optimization passes)
- Multiple target architectures (x86, ARM, RISC-V, etc.)
- Integration with existing toolchains
- JIT compilation capabilities

### Prerequisites

- [ ] Install LLVM: `brew install llvm` (macOS) or `apt install llvm` (Linux)
- [ ] Install Python bindings: `pip install llvmlite`

### Tasks

#### 7.1: LLVM IR Basics

Learn LLVM IR syntax and structure:
- [ ] Study LLVM IR format (SSA form)
- [ ] Understand LLVM types (i32, i64, float, etc.)
- [ ] Learn LLVM instructions (add, sub, mul, load, store, etc.)
- [ ] Understand function declarations and basic blocks

**Example LLVM IR:**
```llvm
define i32 @add(i32 %a, i32 %b) {
entry:
  %result = add i32 %a, %b
  ret i32 %result
}
```

#### 7.2: LLVM IR Generator

- [ ] Create `src/codegen/llvm_codegen.py`
- [ ] Initialize LLVM module
- [ ] Create LLVM builder

#### 7.3: Type Mapping

Map Luna types to LLVM types:
- [ ] `int` → `i64` (64-bit integer)
- [ ] `float` → `double` (64-bit float)
- [ ] `bool` → `i1` (1-bit integer)
- [ ] `string` → `i8*` (pointer to char array)
- [ ] `void` → `void`

#### 7.4: Function Generation

- [ ] Create LLVM function signature from Luna function
- [ ] Generate function parameters
- [ ] Create entry basic block
- [ ] Generate function body
- [ ] Generate return instruction

#### 7.5: Expression Codegen

Generate LLVM IR for expressions:

**Arithmetic:**
- [ ] Addition: `builder.add(left, right)`
- [ ] Subtraction: `builder.sub(left, right)`
- [ ] Multiplication: `builder.mul(left, right)`
- [ ] Division: `builder.sdiv(left, right)` (signed) or `builder.udiv()`
- [ ] Modulo: `builder.srem(left, right)`

**Comparisons:**
- [ ] `<`: `builder.icmp_signed('<', left, right)`
- [ ] `>`: `builder.icmp_signed('>', left, right)`
- [ ] `==`: `builder.icmp_signed('==', left, right)`
- [ ] `!=`: `builder.icmp_signed('!=', left, right)`

**Logical:**
- [ ] `&&`: `builder.and_(left, right)`
- [ ] `||`: `builder.or_(left, right)`
- [ ] `!`: `builder.not_(value)`

#### 7.6: Statement Codegen

**Variables:**
- [ ] Allocate local variables: `builder.alloca(type)`
- [ ] Store values: `builder.store(value, pointer)`
- [ ] Load values: `builder.load(pointer)`

**Control Flow:**
- [ ] If statements:
  ```python
  then_block = function.append_basic_block('then')
  else_block = function.append_basic_block('else')
  merge_block = function.append_basic_block('merge')

  builder.cbranch(condition, then_block, else_block)
  # Generate then/else branches
  builder.branch(merge_block)
  ```

- [ ] While loops:
  ```python
  loop_header = function.append_basic_block('loop_header')
  loop_body = function.append_basic_block('loop_body')
  loop_exit = function.append_basic_block('loop_exit')

  builder.branch(loop_header)
  # Generate condition check
  builder.cbranch(condition, loop_body, loop_exit)
  ```

#### 7.7: Function Calls

- [ ] Generate function call: `builder.call(function, args)`
- [ ] Handle built-in functions:
  - [ ] Declare external printf: `Function(...)`
  - [ ] Create print() wrapper
  - [ ] Create input() wrapper

#### 7.8: Module Finalization

- [ ] Verify LLVM module: `llvm.verify_module(module)`
- [ ] Optimize module with LLVM passes:
  - [ ] Function inlining
  - [ ] Dead code elimination
  - [ ] Constant propagation
  - [ ] Instruction combining
- [ ] Emit LLVM IR to file: `module.print_module()`

#### 7.9: Compilation Pipeline

Create complete LLVM compilation pipeline:

**Option A: Generate LLVM IR file (.ll)**
```bash
python luna.py --llvm -o program.ll examples/fibonacci.luna
lli program.ll  # Execute with LLVM interpreter
```

**Option B: Generate bitcode (.bc)**
```bash
python luna.py --llvm-bc -o program.bc examples/fibonacci.luna
llc program.bc -o program.s  # Compile to assembly
as program.s -o program.o
gcc program.o -o program
./program
```

**Option C: Optimize with LLVM**
```bash
python luna.py --llvm -o program.ll examples/fibonacci.luna
opt -O3 program.ll -o program-opt.ll  # LLVM optimizations
llc program-opt.ll -o program.s
as program.s -o program.o
gcc program.o -o program
./program
```

#### 7.10: Testing

- [ ] Write `tests/test_llvm_codegen.py`
- [ ] Test type mapping
- [ ] Test expression generation
- [ ] Test control flow
- [ ] Test function calls
- [ ] Verify LLVM IR is valid
- [ ] Compare output with interpreter/assembly backend
- [ ] Benchmark: LLVM -O3 vs unoptimized

### Deliverables

✅ LLVM IR code generator
✅ Can generate valid LLVM IR from Luna
✅ Can compile via LLVM toolchain
✅ Integration with LLVM optimizer
✅ Can run: `python luna.py --llvm examples/fibonacci.luna | lli`

### Resources

- LLVM Language Reference: https://llvm.org/docs/LangRef.html
- llvmlite Tutorial: https://llvmlite.readthedocs.io/
- LLVM Kaleidoscope Tutorial: https://llvm.org/docs/tutorial/

---

## Phase 8: Polish & Production (Week 8-10)

**Goal:** Make the compiler production-ready with excellent UX

### Tasks

#### 8.1: CLI Tool
- [ ] Create `luna.py` main entry point
- [ ] Add command-line argument parsing with argparse
- [ ] Add compilation options:
  - [ ] `--tokens` (show tokenization)
  - [ ] `--ast` (show AST)
  - [ ] `--ir` (show unoptimized IR)
  - [ ] `--ir-opt` (show optimized IR)
  - [ ] `--asm` (show assembly)
  - [ ] `--llvm` (generate LLVM IR)
  - [ ] `--optimize` / `-O` (enable optimizations)
  - [ ] `--output` / `-o` (output file)
  - [ ] `--run` (compile and execute)
  - [ ] `--verbose` / `-v` (debug output)
- [ ] Add version info, help text
- [ ] Add compilation statistics (time per phase)

**Example Usage:**
```bash
luna examples/fibonacci.luna                    # Compile and run
luna --optimize examples/fibonacci.luna         # With optimizations
luna --asm -o fib.s examples/fibonacci.luna     # Generate assembly
luna --llvm examples/fibonacci.luna | lli       # LLVM IR
luna --ir --ir-opt examples/test.luna           # Compare IR before/after optimization
```

#### 8.2: Error Messages
- [ ] Improve all error messages
- [ ] Add color-coded output (red for errors, yellow for warnings)
- [ ] Show source context for errors:
  ```
  Error: Type mismatch at line 5, column 18

      let x: int = "hello";
                   ^~~~~~~

  Expected type 'int' but got 'string'
  Help: You cannot assign a string value to an integer variable
  ```
- [ ] Add suggestions for common mistakes:
  - [ ] Typo detection for identifiers
  - [ ] Missing semicolons
  - [ ] Unmatched braces
  - [ ] Type conversion hints

#### 8.3: Documentation
- [ ] Complete all docs/
- [ ] Add comprehensive code comments
- [ ] Write TUTORIAL.md (step-by-step Luna programming guide)
- [ ] Write COMPILER_INTERNALS.md (how the compiler works)
- [ ] Add architecture diagrams
- [ ] Document all CLI flags
- [ ] Create Luna language reference card

#### 8.4: Testing & Quality
- [ ] Achieve >90% code coverage
- [ ] Add integration tests (full pipeline)
- [ ] Test all example programs
- [ ] Add negative tests (programs that should fail)
- [ ] Create test suite with diverse Luna programs
- [ ] Add benchmarks:
  - [ ] Compilation speed
  - [ ] Generated code performance
  - [ ] Optimization effectiveness

#### 8.5: More Example Programs
- [ ] hello_world.luna (basic I/O)
- [ ] fibonacci.luna (recursion)
- [ ] factorial.luna (recursion)
- [ ] fizzbuzz.luna (conditionals)
- [ ] calculator.luna (user input, operators)
- [ ] guess_game.luna (while loops, random)
- [ ] prime_checker.luna (modulo, functions)
- [ ] array_sum.luna (when arrays are added)
- [ ] string_reverse.luna (string manipulation)
- [ ] tower_of_hanoi.luna (complex recursion)

#### 8.6: Performance & Benchmarks

Create benchmark suite:
- [ ] Measure compilation time per phase
- [ ] Compare interpreter vs assembly vs LLVM performance
- [ ] Compare optimized vs unoptimized code
- [ ] Create performance graphs
- [ ] Document optimization impact

**Example Benchmark:**
```
Program: fibonacci(35)

Compilation Times:
- Lexer:    2ms
- Parser:   5ms
- Semantic: 3ms
- IR Gen:   4ms
- Optimize: 8ms (5 passes)
- Codegen:  12ms
Total:      34ms

Execution Times:
- Interpreter:      8,500ms
- Assembly (-O0):   2,100ms
- Assembly (-O):      850ms
- LLVM (-O0):       1,900ms
- LLVM (-O3):        620ms

Optimization Impact:
- DCE removed: 23 dead instructions
- CSE reduced: 15 duplicate expressions
- Constant folding: 8 expressions evaluated
Code size: 145 instructions → 87 instructions (40% reduction)
```

### Deliverables

✅ Professional CLI tool with all flags
✅ Excellent error messages with colors and context
✅ Comprehensive documentation (tutorials, references, internals)
✅ 90%+ test coverage with integration tests
✅ 10+ example programs
✅ Performance benchmarks and analysis
✅ Production-ready compiler!

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
