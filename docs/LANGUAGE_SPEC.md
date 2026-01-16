# Toy Language Specification

**Version:** 1.0
**Status:** Draft

## Overview

Toy is a statically-typed, imperative programming language with C-like syntax. It's designed to be simple enough to implement in a compiler course while being expressive enough to write interesting programs.

## Lexical Structure

### Keywords

```
fn      let     const   if      else    while
return  true    false   int     bool    string
float   void    print   input   len     break
continue
```

### Identifiers

- Must start with a letter or underscore
- Can contain letters, digits, and underscores
- Case-sensitive
- Cannot be a keyword

**Examples:**
```
valid_name
_privateVar
counter123
myFunction
```

### Literals

#### Integer Literals
```
0
42
-17
1000000
```

#### Float Literals
```
3.14
-0.5
2.0
0.001
```

#### Boolean Literals
```
true
false
```

#### String Literals
```
"Hello, World!"
"Toy is awesome"
""  // empty string
"Line 1\nLine 2"  // with escape sequences
```

**Escape Sequences:**
- `\n` - newline
- `\t` - tab
- `\"` - double quote
- `\\` - backslash

### Comments

#### Single-line Comments
```toy
// This is a single-line comment
let x: int = 42;  // Comments can appear after code
```

#### Multi-line Comments
```toy
/*
This is a
multi-line comment
*/
```

### Operators

#### Arithmetic Operators
```
+   Addition
-   Subtraction
*   Multiplication
/   Division
%   Modulo
```

#### Comparison Operators
```
==  Equal to
!=  Not equal to
<   Less than
>   Greater than
<=  Less than or equal
>=  Greater than or equal
```

#### Logical Operators
```
&&  Logical AND
||  Logical OR
!   Logical NOT
```

#### Assignment Operator
```
=   Assignment
```

### Punctuation
```
;   Statement terminator
,   Separator
:   Type annotation
->  Function return type
()  Parentheses (grouping, function calls)
{}  Braces (blocks)
[]  Brackets (arrays - future)
```

## Types

### Primitive Types

#### `int`
- 32-bit signed integer
- Range: -2,147,483,648 to 2,147,483,647
- Default value: 0

#### `float`
- 64-bit floating-point number
- Default value: 0.0

#### `bool`
- Boolean value: `true` or `false`
- Default value: `false`

#### `string`
- Sequence of characters
- Immutable
- Default value: `""`

#### `void`
- Represents absence of a value
- Only valid as function return type
- Cannot declare variables of type `void`

### Type Conversion

Implicit conversions are **NOT** allowed. All type conversions must be explicit.

```toy
let x: int = 42;
let y: float = float(x);  // Explicit conversion (future feature)
```

## Variables

### Variable Declaration

Variables must be declared with their type before use.

```toy
let x: int;           // Declaration (initialized to 0)
let y: int = 42;      // Declaration with initialization
let name: string = "Alice";
```

### Constants

Constants are immutable and must be initialized at declaration.

```toy
const PI: float = 3.14159;
const MAX_SIZE: int = 100;
```

### Scope Rules

- Block scope: Variables declared in a block are only visible within that block
- Function scope: Function parameters are visible within the function body
- Global scope: Variables declared outside functions are global

```toy
let global: int = 10;  // Global variable

fn example() -> void {
    let local: int = 20;  // Local to function

    if true {
        let block: int = 30;  // Local to if block
        // Can access: global, local, block
    }
    // Can access: global, local
    // Cannot access: block
}
```

## Expressions

### Operator Precedence (highest to lowest)

1. `()` - Parentheses (grouping)
2. `!` - Logical NOT
3. `*`, `/`, `%` - Multiplication, Division, Modulo
4. `+`, `-` - Addition, Subtraction
5. `<`, `>`, `<=`, `>=` - Comparison
6. `==`, `!=` - Equality
7. `&&` - Logical AND
8. `||` - Logical OR

### Arithmetic Expressions

```toy
let a: int = 10 + 5 * 2;        // 20 (multiplication first)
let b: int = (10 + 5) * 2;      // 30 (parentheses override)
let c: float = 10.0 / 3.0;      // 3.333...
let d: int = 17 % 5;            // 2 (modulo)
```

### Boolean Expressions

```toy
let x: bool = true && false;      // false
let y: bool = true || false;      // true
let z: bool = !true;              // false
let w: bool = (5 > 3) && (2 < 4); // true
```

### Comparison Expressions

```toy
let a: bool = 10 == 10;  // true
let b: bool = 5 != 3;    // true
let c: bool = 7 < 10;    // true
let d: bool = 5 >= 5;    // true
```

## Statements

### Expression Statement

Any expression followed by a semicolon.

```toy
x = 42;
print("Hello");
fibonacci(10);
```

### Variable Declaration Statement

```toy
let x: int = 10;
const MAX: int = 100;
```

### Assignment Statement

```toy
x = 42;
y = x + 10;
```

### Block Statement

Group of statements enclosed in braces.

```toy
{
    let x: int = 10;
    print(x);
    x = x + 1;
}
```

### If Statement

```toy
if condition {
    // statements
}

if condition {
    // statements
} else {
    // statements
}

if condition1 {
    // statements
} else if condition2 {
    // statements
} else {
    // statements
}
```

### While Loop

```toy
while condition {
    // statements
}

// Example: print numbers 1 to 10
let i: int = 1;
while i <= 10 {
    print(i);
    i = i + 1;
}
```

### Return Statement

```toy
return;           // Return from void function
return 42;        // Return value from function
return x + y;     // Return expression result
```

### Break Statement (future)

```toy
while true {
    if condition {
        break;  // Exit loop
    }
}
```

### Continue Statement (future)

```toy
while i < 10 {
    i = i + 1;
    if i % 2 == 0 {
        continue;  // Skip to next iteration
    }
    print(i);  // Only prints odd numbers
}
```

## Functions

### Function Declaration

```toy
fn functionName(param1: type1, param2: type2) -> returnType {
    // statements
    return value;
}
```

### Examples

```toy
// Function with no parameters, returns int
fn getFortyTwo() -> int {
    return 42;
}

// Function with parameters, returns int
fn add(a: int, b: int) -> int {
    return a + b;
}

// Function with no return value (void)
fn greet(name: string) -> void {
    print("Hello, " + name);
}

// Main function (entry point)
fn main() -> int {
    print("Program started");
    return 0;
}
```

### Function Calls

```toy
let result: int = add(10, 20);
greet("Alice");
let value: int = getFortyTwo();
```

### Recursion

Toy supports recursive function calls.

```toy
fn factorial(n: int) -> int {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
```

## Built-in Functions

### `print(value: any) -> void`

Prints a value to stdout followed by a newline.

```toy
print("Hello, World!");
print(42);
print(true);
```

### `input(prompt: string) -> string`

Reads a line of input from stdin.

```toy
let name: string = input("Enter your name: ");
print("Hello, " + name);
```

### `len(str: string) -> int`

Returns the length of a string.

```toy
let text: string = "Hello";
let length: int = len(text);  // 5
```

## Programs

### Program Structure

A Toy program consists of:
1. Optional global variable declarations
2. One or more function definitions
3. A `main()` function as the entry point

```toy
// Global constants
const VERSION: string = "1.0";

// Helper function
fn greet() -> void {
    print("Toy Compiler v" + VERSION);
}

// Entry point
fn main() -> int {
    greet();
    print("Program complete");
    return 0;
}
```

### Entry Point

Every Toy program must have a `main()` function:
- Must return `int` (exit code)
- Can have no parameters
- Return value of 0 indicates success
- Non-zero return indicates error

## Example Programs

### Hello World

```toy
fn main() -> int {
    print("Hello, World!");
    return 0;
}
```

### Factorial Calculator

```toy
fn factorial(n: int) -> int {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

fn main() -> int {
    let num: int = 5;
    let result: int = factorial(num);
    print(result);  // Prints: 120
    return 0;
}
```

### FizzBuzz

```toy
fn main() -> int {
    let i: int = 1;
    while i <= 100 {
        if i % 15 == 0 {
            print("FizzBuzz");
        } else if i % 3 == 0 {
            print("Fizz");
        } else if i % 5 == 0 {
            print("Buzz");
        } else {
            print(i);
        }
        i = i + 1;
    }
    return 0;
}
```

## Grammar (BNF)

```bnf
program        → declaration* EOF

declaration    → funcDecl | varDecl | constDecl

funcDecl       → "fn" IDENTIFIER "(" parameters? ")" "->" type block
parameters     → IDENTIFIER ":" type ("," IDENTIFIER ":" type)*

varDecl        → "let" IDENTIFIER ":" type ("=" expression)? ";"
constDecl      → "const" IDENTIFIER ":" type "=" expression ";"

statement      → exprStmt | block | ifStmt | whileStmt | returnStmt
exprStmt       → expression ";"
block          → "{" declaration* "}"
ifStmt         → "if" expression block ("else" (ifStmt | block))?
whileStmt      → "while" expression block
returnStmt     → "return" expression? ";"

expression     → assignment
assignment     → IDENTIFIER "=" assignment | logicOr
logicOr        → logicAnd ("||" logicAnd)*
logicAnd       → equality ("&&" equality)*
equality       → comparison (("==" | "!=") comparison)*
comparison     → term (("<" | ">" | "<=" | ">=") term)*
term           → factor (("+" | "-") factor)*
factor         → unary (("*" | "/" | "%") unary)*
unary          → ("!" | "-") unary | call
call           → primary ("(" arguments? ")")*
arguments      → expression ("," expression)*
primary        → NUMBER | STRING | "true" | "false" | IDENTIFIER | "(" expression ")"

type           → "int" | "float" | "bool" | "string" | "void"
```

## Semantic Rules

### Type Checking

1. **Assignment Compatibility**: Right-hand side must be compatible with left-hand side type
2. **Arithmetic Operations**: Both operands must be numeric (int or float)
3. **Comparison Operations**: Both operands must be the same type
4. **Logical Operations**: Operands must be bool
5. **Function Calls**: Arguments must match parameter types
6. **Return Statements**: Return type must match function return type

### Symbol Table

1. **No Redeclaration**: Cannot declare the same variable twice in the same scope
2. **Declaration Before Use**: Variables must be declared before use
3. **Function Uniqueness**: Function names must be unique

### Control Flow

1. **If Condition**: Condition expression must be of type bool
2. **While Condition**: Condition expression must be of type bool
3. **Return Required**: Non-void functions must have return statement
4. **Unreachable Code**: Warn about code after return statement (future)

## Error Messages

The compiler should provide helpful error messages:

```
Error at line 5, column 10: Expected ';' after variable declaration
Error at line 12: Type mismatch: cannot assign 'string' to 'int'
Error at line 20: Undefined variable 'x'
Error at line 8: Function 'foo' expects 2 arguments but got 1
```

## Future Features

Features to potentially add:
- Arrays and array indexing
- Structs/records
- Type inference (var keyword)
- For loops
- Switch statements
- String interpolation
- Import/modules
- Enums
- Pattern matching

---

**Next:** See [COMPILER_DESIGN.md](COMPILER_DESIGN.md) for implementation architecture.
