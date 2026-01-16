# Luna Compiler Design Document

## Architecture Overview

The Luna compiler follows the classic **multi-pass compiler** architecture with clear separation between phases.

```
Source Code
    ↓
┌─────────────┐
│   Lexer     │ → Tokens
└─────────────┘
    ↓
┌─────────────┐
│   Parser    │ → AST
└─────────────┘
    ↓
┌─────────────┐
│  Semantic   │ → Typed AST + Symbol Table
└─────────────┘
    ↓
┌─────────────┐
│  IR Gen     │ → Three-Address Code
└─────────────┘
    ↓
┌─────────────┐
│  Code Gen   │ → Executable
└─────────────┘
```

## Phase 1: Lexical Analysis

### Purpose
Convert source code (string of characters) into a stream of tokens.

### Components

**Token (token.py)**
- Represents a single lexical unit
- Fields: type, value, line, column
- Example: `Token(TokenType.NUMBER, 42, 1, 5)`

**Lexer (lexer.py)**
- Scans source code character by character
- Groups characters into meaningful tokens
- Handles whitespace and comments
- Reports lexical errors

### Algorithm
```python
def tokenize(source):
    tokens = []
    position = 0

    while position < len(source):
        char = source[position]

        if char.isspace():
            skip_whitespace()
        elif char == '/':
            if peek() == '/':
                skip_line_comment()
            elif peek() == '*':
                skip_block_comment()
            else:
                tokens.append(Token(DIV, '/'))
        elif char.isdigit():
            tokens.append(scan_number())
        elif char == '"':
            tokens.append(scan_string())
        elif char.isalpha() or char == '_':
            tokens.append(scan_identifier_or_keyword())
        elif char in operators:
            tokens.append(scan_operator())
        else:
            error("Unexpected character")

        position += 1

    return tokens
```

### Error Handling
- Unexpected characters
- Unterminated strings
- Invalid escape sequences

## Phase 2: Syntax Analysis

### Purpose
Build an Abstract Syntax Tree (AST) from tokens, checking grammar rules.

### Components

**AST Nodes (ast_nodes.py)**
- Represent program structure
- Expression nodes: literals, binary ops, function calls
- Statement nodes: if, while, return, variable declarations
- Declaration nodes: functions

**Parser (parser.py)**
- Recursive descent parser
- Each grammar rule → parsing function
- Produces AST as output

### Parsing Strategy

**Recursive Descent**
- Top-down parsing
- Each non-terminal → function
- Easy to implement and debug
- Follows grammar structure directly

**Precedence Climbing for Expressions**
```
expression  → assignment
assignment  → logic_or ("=" assignment)?
logic_or    → logic_and ("||" logic_and)*
logic_and   → equality ("&&" equality)*
equality    → comparison (("==" | "!=") comparison)*
comparison  → term (("<" | ">" | "<=" | ">=") term)*
term        → factor (("+" | "-") factor)*
factor      → unary (("*" | "/" | "%") unary)*
unary       → ("!" | "-") unary | call
call        → primary ("(" arguments? ")")*
primary     → literal | identifier | "(" expression ")"
```

### BNF Grammar to Parser Method Mapping

The parser implements each BNF grammar rule as a corresponding method. This table provides traceability from the formal grammar specification to the implementation.

| BNF Rule | Parser Method | Description |
|----------|---------------|-------------|
| `program → declaration* EOF` | `parse()` | Entry point, collects all declarations |
| `declaration → funcDecl \| varDecl \| constDecl` | `_parse_declaration()` | Routes to appropriate declaration parser |
| `funcDecl → "func" IDENTIFIER "(" params? ")" ":" type block` | `_parse_function_declaration()` | Parses function signature and body |
| `varDecl → "let" IDENTIFIER ":" type ("=" expression)? ";"` | `_parse_variable_declaration()` | Parses mutable variable declaration |
| `constDecl → "const" IDENTIFIER ":" type "=" expression ";"` | `_parse_variable_declaration()` | Parses constant declaration (is_const=True) |
| `params → param ("," param)*` | `_parse_parameters()` | Parses parameter list |
| `param → IDENTIFIER ":" type` | `_parse_parameter()` | Parses single parameter |
| `type → "int" \| "float" \| "bool" \| "string" \| "void"` | `_parse_type()` | Parses type annotation |
| `block → "{" statement* "}"` | `_parse_block()` | Parses block of statements |
| `statement → exprStmt \| varDecl \| constDecl \| ifStmt \| whileStmt \| returnStmt \| block` | `_parse_statement()` | Routes to appropriate statement parser |
| `ifStmt → "if" expression block ("else" (ifStmt \| block))?` | `_parse_if_statement()` | Parses if/else chains |
| `whileStmt → "while" expression block` | `_parse_while_statement()` | Parses while loop |
| `returnStmt → "return" expression? ";"` | `_parse_return_statement()` | Parses return statement |
| `exprStmt → expression ";"` | `_parse_expression_statement()` | Expression as statement |
| `expression → assignment` | `_parse_expression()` | Entry to expression parsing |
| `assignment → IDENTIFIER "=" assignment \| logic_or` | `_parse_assignment()` | Right-associative assignment |
| `logic_or → logic_and ("or" logic_and)*` | `_parse_or()` | Logical OR |
| `logic_and → equality ("and" equality)*` | `_parse_and()` | Logical AND |
| `equality → comparison (("==" \| "!=") comparison)*` | `_parse_equality()` | Equality operators |
| `comparison → term (("<" \| ">" \| "<=" \| ">=") term)*` | `_parse_comparison()` | Relational operators |
| `term → factor (("+" \| "-") factor)*` | `_parse_term()` | Addition/subtraction |
| `factor → unary (("*" \| "/" \| "%") unary)*` | `_parse_factor()` | Multiplication/division/modulo |
| `unary → ("!" \| "-") unary \| call` | `_parse_unary()` | Unary operators |
| `call → primary ("(" arguments? ")")*` | `_parse_call()` | Function call |
| `arguments → expression ("," expression)*` | (inline in `_parse_call()`) | Argument list |
| `primary → literal \| IDENTIFIER \| "(" expression ")"` | `_parse_primary()` | Atoms: literals, variables, grouping |

**Grammar-to-Code Pattern:**

Each grammar rule follows a predictable implementation pattern:

```python
# For rule: A → B (("op1" | "op2") B)*
def _parse_A(self):
    left = self._parse_B()                    # Parse first operand
    while self._match("op1", "op2"):          # While we see operators
        operator = self._previous().value      # Get the operator
        right = self._parse_B()               # Parse next operand
        left = BinaryExpr(left, operator, right)  # Build AST node
    return left

# For rule: A → "keyword" ... | "other" ...
def _parse_A(self):
    if self._match("keyword"):
        return self._parse_keyword_variant()
    elif self._match("other"):
        return self._parse_other_variant()
    else:
        self._error("Expected 'keyword' or 'other'")
```

### Error Recovery
- Panic mode: skip tokens until synchronization point
- Synchronization points: semicolons, statement keywords
- Continue parsing after error to find more errors

## Phase 3: Semantic Analysis

### Purpose
Check program correctness beyond syntax: types, scopes, declarations.

### Components

**Symbol Table (symbol_table.py)**
- Maps names to symbols (variables, functions)
- Maintains scope chain
- Operations: enter_scope, exit_scope, define, lookup

**Type Checker (type_checker.py)**
- Validates type compatibility
- Checks operator operands
- Validates function calls
- Ensures return types match

**Semantic Analyzer (semantic_analyzer.py)**
- Orchestrates semantic analysis
- Multiple passes over AST
- Pass 1: Build symbol table
- Pass 2: Type check

### Type Checking Rules

**Binary Operations**
```python
def check_binary(left, op, right):
    if op in ['+', '-', '*', '/', '%']:
        # Arithmetic: both must be numeric
        if not (is_numeric(left) and is_numeric(right)):
            error("Arithmetic requires numeric types")
        return left  # Result type same as operands

    elif op in ['<', '>', '<=', '>=']:
        # Comparison: both must be same type
        if left != right:
            error("Comparison requires same types")
        return BoolType()

    elif op in ['&&', '||']:
        # Logical: both must be bool
        if left != BoolType() or right != BoolType():
            error("Logical operators require bool")
        return BoolType()
```

**Function Calls**
```python
def check_call(name, arguments):
    # Lookup function in symbol table
    func = symbol_table.lookup(name)
    if not func:
        error(f"Undefined function '{name}'")

    # Check argument count
    if len(arguments) != len(func.params):
        error("Argument count mismatch")

    # Check argument types
    for arg, param in zip(arguments, func.params):
        if type_of(arg) != param.type:
            error("Argument type mismatch")

    return func.return_type
```

### Scope Management

**Scopes**
- Global scope: global variables, functions
- Function scope: parameters, local variables
- Block scope: variables in { }

**Scope Chain**
```python
class ScopeManager:
    def __init__(self):
        self.scopes = [{}]  # Start with global scope

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def define(self, name, symbol):
        if name in self.scopes[-1]:
            error(f"Redeclaration of '{name}'")
        self.scopes[-1][name] = symbol

    def lookup(self, name):
        # Search from innermost to outermost
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        error(f"Undefined variable '{name}'")
```

## Phase 4: Intermediate Representation

### Purpose
Generate platform-independent intermediate code (three-address code).

### Why IR?
- Separates front-end (parsing) from back-end (code generation)
- Makes optimization easier
- Enables multiple target backends

### Three-Address Code (TAC)

**Format:** Each instruction has at most 3 addresses (operands)

```
x = y op z    // Binary operation
x = op y      // Unary operation
x = y         // Copy
goto L        // Unconditional jump
if x goto L   // Conditional jump
L:            // Label
param x       // Function parameter
call f, n     // Call function f with n parameters
return x      // Return value
```

**Example Translation**

Luna code:
```luna
let x: int = (a + b) * (c - d);
```

TAC:
```
t1 = a + b
t2 = c - d
t3 = t1 * t2
x = t3
```

### Control Flow Translation

**If Statement**

Luna:
```luna
if x > 0 {
    y = 1;
} else {
    y = -1;
}
```

TAC:
```
    t1 = x > 0
    if_false t1 goto L1
    y = 1
    goto L2
L1: y = -1
L2: // continue
```

**While Loop**

Luna:
```luna
while i < 10 {
    i = i + 1;
}
```

TAC:
```
L1: t1 = i < 10
    if_false t1 goto L2
    t2 = i + 1
    i = t2
    goto L1
L2: // continue
```

## Phase 5: Code Generation

### Target Options

**Option A: Interpreter**
- Walk the AST directly
- Easiest to implement
- Good for learning

**Option B: Python Code Generator**
- Generate Python source code
- Can leverage Python features
- Medium difficulty

**Option C: C Code Generator**
- Generate C source code
- Compile with gcc/clang
- Most educational
- Most challenging

### Interpreter Design

```python
class Interpreter:
    def __init__(self):
        self.environment = {}
        self.call_stack = []

    def eval(self, node):
        if isinstance(node, LiteralExpr):
            return node.value

        elif isinstance(node, BinaryExpr):
            left = self.eval(node.left)
            right = self.eval(node.right)
            return self.apply_op(node.op, left, right)

        elif isinstance(node, VariableExpr):
            return self.environment[node.name]

        elif isinstance(node, CallExpr):
            return self.call_function(node.name, node.args)

    def execute(self, stmt):
        if isinstance(stmt, AssignmentStmt):
            value = self.eval(stmt.expression)
            self.environment[stmt.name] = value

        elif isinstance(stmt, IfStmt):
            condition = self.eval(stmt.condition)
            if condition:
                self.execute(stmt.then_branch)
            elif stmt.else_branch:
                self.execute(stmt.else_branch)

        elif isinstance(stmt, WhileStmt):
            while self.eval(stmt.condition):
                self.execute(stmt.body)

        elif isinstance(stmt, ReturnStmt):
            value = self.eval(stmt.expression)
            raise ReturnException(value)
```

## Error Handling Strategy

### Error Types

**Lexical Errors**
- Unexpected character
- Unterminated string
- Invalid number format

**Syntax Errors**
- Missing semicolon
- Unmatched parentheses
- Invalid token sequence

**Semantic Errors**
- Type mismatch
- Undefined variable
- Redeclaration
- Function signature mismatch

**Runtime Errors** (interpreter only)
- Division by zero
- Stack overflow (recursion)
- Null dereference

### Error Reporting

**Good error messages include:**
1. Error type
2. Source location (line, column)
3. Context (show the problematic code)
4. Explanation of what's wrong
5. Suggestion for fix (when possible)

**Example:**

```
Error at line 5, column 10: Type mismatch

    let x: int = "hello";
                 ^------^

Expected type 'int' but got 'string'
Help: Cannot assign string value to int variable
```

## Optimization Opportunities

### Constant Folding

Transform compile-time constant expressions:
```
2 + 3 * 4  →  14
true && false  →  false
```

### Dead Code Elimination

Remove unreachable code:
```luna
if false {
    print("never runs");  // Remove this
}
```

### Common Subexpression Elimination

```luna
let a: int = x + y;
let b: int = x + y;  // Reuse first computation
```

Becomes:
```
t1 = x + y
a = t1
b = t1  // Don't recalculate
```

## Testing Strategy

### Unit Tests
- Test each phase independently
- Mock inputs from previous phases
- Verify outputs for next phase

### Integration Tests
- Test full pipeline
- Use real Luna programs
- Verify correct output

### Test Pyramid
```
    ┌─────────────┐
    │   E2E Tests │  ← Few: Full programs
    └─────────────┘
       ┌─────────────────┐
       │ Integration Tests│  ← Some: Multiple phases
       └─────────────────┘
           ┌───────────────────┐
           │    Unit Tests      │  ← Many: Individual functions
           └───────────────────┘
```

## Performance Considerations

### Lexer
- Use string builder instead of concatenation
- Avoid backtracking
- Cache keyword lookups

### Parser
- Avoid deep recursion (iterative where possible)
- Minimize AST node allocations

### Semantic Analysis
- Use hash tables for symbol lookups
- Cache type checking results

### IR Generation
- Reuse temporary variables
- Minimize label generation

## Future Enhancements

### Language Features
- Arrays
- Structs
- For loops
- String methods
- Standard library

### Compiler Features
- Incremental compilation
- Better error recovery
- IDE integration (LSP)
- Debugger support
- Profiling

### Optimizations
- Register allocation
- Inline functions
- Loop unrolling
- Tail call optimization

---

**Next Steps:**
1. Read [BUILD_PHASES.md](BUILD_PHASES.md) for implementation plan
2. Start with Phase 1: Lexer
3. Build incrementally, test continuously
4. Learn by doing!
