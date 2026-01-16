# Toy Compiler Internals

This document provides detailed documentation of the Toy compiler's internal implementation, including the type system, symbol table, IR generation, and optimization passes.

## Table of Contents

1. [Type System](#type-system)
2. [Symbol Table](#symbol-table)
3. [Type Checker](#type-checker)
4. [IR Generation](#ir-generation)
5. [Optimization Passes](#optimization-passes)
6. [Code Generation](#code-generation)

---

## Type System

**File:** `src/semantic/types.py`

### Overview

Toy uses a **static, strong type system** with no implicit type conversions. All types are determined at compile time, and type mismatches result in compilation errors.

### Type Hierarchy

```
ToyType (abstract base)
├── PrimitiveType
│   ├── INT      (64-bit signed integer)
│   ├── FLOAT    (64-bit floating point)
│   ├── BOOL     (boolean: true/false)
│   ├── STRING   (string literal)
│   └── VOID     (no value)
└── FunctionType
    ├── parameter_types: List[ToyType]
    └── return_type: ToyType
```

### Built-in Types

| Type | Description | Example Values |
|------|-------------|----------------|
| `int` | 64-bit signed integer | `42`, `-7`, `0` |
| `float` | 64-bit floating point | `3.14`, `-0.5` |
| `bool` | Boolean | `true`, `false` |
| `string` | String literal | `"hello"`, `""` |
| `void` | No return value | (functions only) |

### Type Operations

#### Binary Operations

| Operator | Left Type | Right Type | Result Type |
|----------|-----------|------------|-------------|
| `+`, `-`, `*`, `/` | `int` | `int` | `int` |
| `+`, `-`, `*`, `/` | `float` | `float` | `float` |
| `%` | `int` | `int` | `int` |
| `<`, `>`, `<=`, `>=` | numeric | numeric (same) | `bool` |
| `==`, `!=` | any | any (same) | `bool` |
| `&&`, `\|\|` | `bool` | `bool` | `bool` |

#### Unary Operations

| Operator | Operand Type | Result Type |
|----------|--------------|-------------|
| `-` (negation) | `int` or `float` | same as operand |
| `!` (logical not) | `bool` | `bool` |

### Key Functions

```python
# Get result type of binary operation
get_binary_result_type(op: str, left: ToyType, right: ToyType) -> Optional[ToyType]

# Get result type of unary operation
get_unary_result_type(op: str, operand: ToyType) -> Optional[ToyType]

# Check if assignment is valid
is_assignable(target_type: ToyType, value_type: ToyType) -> bool

# Convert AST TypeAnnotation to ToyType
type_from_annotation(annotation: TypeAnnotation) -> ToyType
```

### Design Decisions

1. **No implicit conversions**: `int` and `float` cannot be mixed in arithmetic
2. **Strict equality**: Only same types can be compared with `==`/`!=`
3. **Boolean conditions**: `if` and `while` require `bool`, not truthy values
4. **Void restrictions**: Cannot use `void` in expressions or assignments

---

## Symbol Table

**File:** `src/semantic/symbol_table.py`

### Overview

The symbol table manages all named entities (variables, functions, parameters) and their associated information. It implements lexical scoping with a scope chain.

### Symbol Structure

```python
@dataclass
class Symbol:
    name: str           # Identifier name
    type: ToyType      # Type of the symbol
    kind: SymbolKind    # VARIABLE, CONSTANT, FUNCTION, PARAMETER
    line: int           # Declaration line number
    column: int         # Declaration column number
    is_initialized: bool = False
    is_const: bool = False
    is_function: bool = False
```

### Symbol Kinds

| Kind | Description | Example |
|------|-------------|---------|
| `VARIABLE` | Mutable variable | `let x: int = 5;` |
| `CONSTANT` | Immutable variable | `const PI: float = 3.14;` |
| `FUNCTION` | Function declaration | `fn add(a: int, b: int) -> int` |
| `PARAMETER` | Function parameter | `a` and `b` in above |

### Scope Management

```python
class SymbolTable:
    def enter_scope(self, name: str) -> None:
        """Push a new scope onto the scope stack."""

    def exit_scope(self) -> None:
        """Pop the current scope from the stack."""

    def define(self, symbol: Symbol) -> bool:
        """Add a symbol to the current scope. Returns False if duplicate."""

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol, searching from innermost to outermost scope."""

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in the current scope."""
```

### Scope Chain Example

```toy
fn foo(x: int) -> int {     // Global scope + function scope
    let y: int = 10;        // y in function scope
    if x > 0 {              // Block scope
        let z: int = 20;    // z in block scope
        return z;           // Can access z, y, x
    }
    return y;               // Can access y, x (not z)
}
```

Scope chain during `if` block:
```
[Global] -> [foo function] -> [if block]
   ↑              ↑              ↑
 foo()           x, y            z
```

### Built-in Functions

The symbol table is pre-populated with built-in functions:

```python
# print() - accepts any single argument
Symbol(
    name="print",
    type=FunctionType(parameter_types=[INT], return_type=VOID),
    kind=SymbolKind.FUNCTION,
    is_function=True
)
```

---

## Type Checker

**File:** `src/semantic/type_checker.py`

### Overview

The type checker implements the visitor pattern to traverse the AST and validate type correctness. It produces semantic errors for type violations.

### Checking Process

1. **Visit Program**: Check all function declarations
2. **Visit Function**: Enter scope, add parameters, check body
3. **Visit Statements**: Validate each statement type
4. **Visit Expressions**: Compute and validate expression types

### What Gets Checked

#### Variable Declarations

```toy
let x: int = "hello";  // Error: Cannot initialize 'int' with 'string'
```

Checks:
- Initializer type matches declared type
- No duplicate declarations in same scope

#### Assignments

```toy
let x: int = 5;
x = true;  // Error: Cannot assign 'bool' to 'int'
```

Checks:
- Variable exists
- Variable is not a constant
- Value type matches variable type

#### Binary Expressions

```toy
let x: int = 5 + "hello";  // Error: Invalid operand types for '+': 'int' and 'string'
```

Checks:
- Both operands have compatible types for the operator
- Result type is determined by operands and operator

#### Function Calls

```toy
fn add(a: int, b: int) -> int { return a + b; }
add(1, "two");  // Error: Argument 2 has wrong type: expected 'int', got 'string'
```

Checks:
- Function exists
- Correct number of arguments
- Each argument type matches parameter type

#### Return Statements

```toy
fn foo() -> int {
    return "hello";  // Error: Return type mismatch: expected 'int', got 'string'
}
```

Checks:
- Return value type matches function return type
- Void functions don't return values
- Non-void functions return values

#### Control Flow Conditions

```toy
if 42 { ... }  // Error: If condition must be a boolean, got 'int'
while "loop" { ... }  // Error: While condition must be a boolean, got 'string'
```

Checks:
- `if` condition is `bool`
- `while` condition is `bool`

### Error Collection

The type checker collects all errors rather than stopping at the first one:

```python
def check(self, program: Program) -> List[SemanticError]:
    self.errors = []
    program.accept(self)
    return self.errors
```

---

## IR Generation

**Files:** `src/ir/instructions.py`, `src/ir/ir_generator.py`, `src/ir/cfg.py`

### SSA Form

Toy's IR uses **Static Single Assignment (SSA)** form where:
- Each variable is assigned exactly once
- Variables are versioned (e.g., `x_0`, `x_1`, `x_2`)
- Phi functions merge values at control flow join points

### IR Instructions

| Instruction | Format | Description |
|-------------|--------|-------------|
| `LoadConst` | `dest = value` | Load constant value |
| `Copy` | `dest = src` | Copy value |
| `BinaryOp` | `dest = left op right` | Binary operation |
| `UnaryOp` | `dest = op operand` | Unary operation |
| `Jump` | `jump label` | Unconditional jump |
| `Branch` | `branch cond, true_label, false_label` | Conditional branch |
| `Phi` | `dest = phi [v1, b1], [v2, b2]` | SSA merge |
| `Call` | `dest = call func(args)` | Function call |
| `Return` | `return value` | Return from function |

### Control Flow Graph

Each function is represented as a CFG with basic blocks:

```python
class BasicBlock:
    name: str                      # Block label (e.g., "B0", "then1")
    instructions: List[IRInstruction]
    predecessors: List[BasicBlock]
    successors: List[BasicBlock]
    terminator: IRInstruction      # Jump, Branch, or Return
```

### Example IR

Toy source:
```toy
fn max(a: int, b: int) -> int {
    if a > b {
        return a;
    } else {
        return b;
    }
}
```

Generated SSA IR:
```
FUNCTION max(a_0: int, b_0: int) -> int:
  entry0:
    t_0 = a_0 > b_0
    branch t_0, then1, else2

  then1:
    ret a_0

  else2:
    ret b_0
```

---

## Optimization Passes

**Files:** `src/ir/optimizations/*.py`

### Pass Manager

The pass manager runs optimization passes until a fixed point (no more changes):

```python
class PassManager:
    def run_until_fixed_point(self, module: IRModule, max_iterations: int = 10):
        for _ in range(max_iterations):
            changed = False
            for pass_ in self.passes:
                if pass_.run(module):
                    changed = True
            if not changed:
                break
```

### Available Optimizations

#### 1. Constant Folding (`constant_folding.py`)

Evaluates constant expressions at compile time.

```
Before: t0 = 2 + 3
After:  t0 = 5
```

#### 2. Dead Code Elimination (`dead_code_elimination.py`)

Removes unused variables and unreachable code.

```
Before: t0 = 5          // Never used
        x = 10
        return x
        y = 20          // Unreachable

After:  x = 10
        return x
```

#### 3. Common Subexpression Elimination (`cse.py`)

Reuses previously computed expressions.

```
Before: t0 = a + b
        x = t0
        t1 = a + b      // Same as t0
        y = t1

After:  t0 = a + b
        x = t0
        y = t0          // Reuse t0
```

#### 4. Copy Propagation (`copy_propagation.py`)

Replaces copies with original values.

```
Before: x = a
        y = x + 1       // Use 'a' directly

After:  x = a
        y = a + 1
```

#### 5. Algebraic Simplification (`algebraic.py`)

Applies mathematical identities.

| Expression | Simplified |
|------------|------------|
| `x + 0` | `x` |
| `x * 1` | `x` |
| `x * 0` | `0` |
| `x - x` | `0` |
| `x / x` | `1` |
| `x && false` | `false` |
| `x \|\| true` | `true` |

#### 6. Control Flow Optimization (`control_flow.py`)

Simplifies control flow structures.

```
Before: branch true, L1, L2    // Constant condition
After:  jump L1
```

Also: jump threading, unreachable block elimination, block merging.

### Default Pass Order

```python
def create_default_pass_manager() -> PassManager:
    return PassManager([
        ConstantFoldingPass(),
        AlgebraicSimplificationPass(),
        CopyPropagationPass(),
        CommonSubexpressionEliminationPass(),
        DeadCodeEliminationPass(),
        ControlFlowOptimizationPass(),
    ])
```

---

## Code Generation

### x86-64 Backend

**Files:** `src/codegen/x86_64_codegen.py`, `src/codegen/stack_frame.py`

#### Stack Frame Layout

```
+------------------+ <- rbp
| Saved rbp        | [rbp+0]
+------------------+
| Return address   | [rbp+8]
+------------------+
| Local var 1      | [rbp-8]
+------------------+
| Local var 2      | [rbp-16]
+------------------+
| ...              |
+------------------+ <- rsp (16-byte aligned)
```

#### Calling Convention (System V AMD64 ABI)

- Arguments: `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` (first 6)
- Additional arguments: pushed to stack
- Return value: `rax`
- Callee-saved: `rbx`, `rbp`, `r12-r15`
- Caller-saved: `rax`, `rcx`, `rdx`, `rsi`, `rdi`, `r8-r11`

#### Generated Assembly Example

```asm
_add:
    pushq %rbp
    movq %rsp, %rbp
    subq $16, %rsp

    movq %rdi, -8(%rbp)     # a
    movq %rsi, -16(%rbp)    # b

    movq -8(%rbp), %rax     # load a
    addq -16(%rbp), %rax    # add b

    movq %rbp, %rsp
    popq %rbp
    retq
```

### LLVM Backend

**Files:** `src/codegen/llvm_codegen.py`, `src/codegen/llvm_emitter.py`

#### Type Mapping

| Toy Type | LLVM Type |
|-----------|-----------|
| `int` | `i64` |
| `float` | `double` |
| `bool` | `i1` |
| `string` | `i8*` |
| `void` | `void` |

#### JIT Compilation

```python
from src.codegen import compile_and_run_llvm

result = compile_and_run_llvm("""
    fn main() -> int {
        return 42;
    }
""")
print(result.return_value)  # 42
```

#### Generated LLVM IR Example

```llvm
define i64 @add(i64 %a_0, i64 %b_0) {
entry0:
  %t_0 = add i64 %a_0, %b_0
  ret i64 %t_0
}
```

---

## Testing

### Test Structure

```
tests/
├── test_lexer.py          # 33 tests
├── test_parser.py         # 63 tests
├── test_semantic.py       # 65 tests
├── test_ir.py             # 58 tests
├── test_optimizations.py  # 52 tests
├── test_codegen.py        # 39 tests
├── test_llvm_codegen.py   # 41 tests
└── test_integration.py    # 39 tests
                           # Total: 390 tests
```

### Running Tests

```bash
# All tests
python -m pytest

# Specific phase
python -m pytest tests/test_semantic.py -v

# With coverage
python -m pytest --cov=src
```

---

## Error Messages

### Format

```
Error at line X, column Y: <error type>

    <source line>
    <pointer to error location>

<detailed explanation>
```

### Example

```
Error at line 5, column 18: Type mismatch

    let x: int = "hello";
                 ^------^

Cannot initialize variable 'x' of type 'int' with value of type 'string'
```

---

## Future Enhancements

### Type System
- [ ] Array types: `int[]`
- [ ] Struct types: `struct Point { x: int, y: int }`
- [ ] Generic types: `fn max<T>(a: T, b: T) -> T`
- [ ] Type inference: `let x = 42;` (infer `int`)

### Optimizations
- [ ] Inlining
- [ ] Loop-invariant code motion
- [ ] Register allocation (linear scan or graph coloring)
- [ ] Tail call optimization

### Code Generation
- [ ] ARM64 backend
- [ ] WebAssembly backend
- [ ] Debug info generation (DWARF)
