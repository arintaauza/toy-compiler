"""
Tests for the Toy semantic analyzer.

Tests cover:
- Type system
- Symbol table operations
- Type checking for expressions and statements
- Semantic error detection
- Full program validation
"""

import pytest
from src.semantic.types import (
    ToyType,
    PrimitiveType,
    FunctionType,
    INT, FLOAT, BOOL, STRING, VOID,
    type_from_annotation,
    type_from_name,
    is_assignable,
    get_binary_result_type,
    get_unary_result_type,
)
from src.semantic.symbol_table import (
    SymbolKind,
    Symbol,
    Scope,
    SymbolTable,
    create_symbol_table_with_builtins,
)
from src.semantic.type_checker import TypeChecker
from src.semantic.semantic_analyzer import (
    SemanticAnalyzer,
    analyze,
    analyze_source,
)
from src.parser.ast_nodes import TypeAnnotation
from src.utils.error import SemanticError


# =============================================================================
# Type System Tests
# =============================================================================

class TestPrimitiveTypes:
    """Test primitive type operations."""

    def test_type_equality(self):
        assert INT == INT
        assert INT != FLOAT
        assert INT != BOOL
        assert STRING != VOID

    def test_type_hashing(self):
        types_set = {INT, FLOAT, BOOL, STRING, VOID}
        assert len(types_set) == 5
        assert INT in types_set

    def test_type_string_representation(self):
        assert str(INT) == "int"
        assert str(FLOAT) == "float"
        assert str(BOOL) == "bool"
        assert str(STRING) == "string"
        assert str(VOID) == "void"

    def test_numeric_types(self):
        assert INT.is_numeric()
        assert FLOAT.is_numeric()
        assert not BOOL.is_numeric()
        assert not STRING.is_numeric()
        assert not VOID.is_numeric()


class TestFunctionTypes:
    """Test function type operations."""

    def test_function_type_creation(self):
        func_type = FunctionType(
            parameter_types=[INT, INT],
            return_type=INT
        )
        assert len(func_type.parameter_types) == 2
        assert func_type.return_type == INT

    def test_function_type_equality(self):
        func1 = FunctionType([INT, INT], INT)
        func2 = FunctionType([INT, INT], INT)
        func3 = FunctionType([INT], INT)
        func4 = FunctionType([INT, INT], FLOAT)

        assert func1 == func2
        assert func1 != func3  # Different param count
        assert func1 != func4  # Different return type

    def test_function_type_string(self):
        func_type = FunctionType([INT, FLOAT], BOOL)
        assert str(func_type) == "fn(int, float) -> bool"


class TestTypeConversion:
    """Test type conversion utilities."""

    def test_type_from_annotation(self):
        assert type_from_annotation(TypeAnnotation.INT) == INT
        assert type_from_annotation(TypeAnnotation.FLOAT) == FLOAT
        assert type_from_annotation(TypeAnnotation.BOOL) == BOOL
        assert type_from_annotation(TypeAnnotation.STRING) == STRING
        assert type_from_annotation(TypeAnnotation.VOID) == VOID

    def test_type_from_name(self):
        assert type_from_name("int") == INT
        assert type_from_name("float") == FLOAT
        assert type_from_name("bool") == BOOL
        assert type_from_name("string") == STRING
        assert type_from_name("void") == VOID
        assert type_from_name("unknown") is None


class TestBinaryOperatorTypes:
    """Test binary operator type checking."""

    def test_arithmetic_operators(self):
        # int + int = int
        assert get_binary_result_type("+", INT, INT) == INT
        # float + float = float
        assert get_binary_result_type("+", FLOAT, FLOAT) == FLOAT
        # int + float = None (no implicit conversion)
        assert get_binary_result_type("+", INT, FLOAT) is None

    def test_comparison_operators(self):
        # int < int = bool
        assert get_binary_result_type("<", INT, INT) == BOOL
        assert get_binary_result_type(">", INT, INT) == BOOL
        assert get_binary_result_type("<=", FLOAT, FLOAT) == BOOL
        assert get_binary_result_type(">=", FLOAT, FLOAT) == BOOL
        # string < string is not allowed (not numeric)
        assert get_binary_result_type("<", STRING, STRING) is None

    def test_equality_operators(self):
        # Same types can be compared
        assert get_binary_result_type("==", INT, INT) == BOOL
        assert get_binary_result_type("!=", STRING, STRING) == BOOL
        # Different types cannot be compared
        assert get_binary_result_type("==", INT, STRING) is None

    def test_logical_operators(self):
        # bool && bool = bool
        assert get_binary_result_type("&&", BOOL, BOOL) == BOOL
        assert get_binary_result_type("||", BOOL, BOOL) == BOOL
        # int && int is not allowed
        assert get_binary_result_type("&&", INT, INT) is None

    def test_modulo_operator(self):
        # int % int = int
        assert get_binary_result_type("%", INT, INT) == INT
        # float % float is not allowed
        assert get_binary_result_type("%", FLOAT, FLOAT) is None


class TestUnaryOperatorTypes:
    """Test unary operator type checking."""

    def test_negation(self):
        assert get_unary_result_type("-", INT) == INT
        assert get_unary_result_type("-", FLOAT) == FLOAT
        assert get_unary_result_type("-", BOOL) is None
        assert get_unary_result_type("-", STRING) is None

    def test_logical_not(self):
        assert get_unary_result_type("!", BOOL) == BOOL
        assert get_unary_result_type("!", INT) is None


# =============================================================================
# Symbol Table Tests
# =============================================================================

class TestScope:
    """Test scope operations."""

    def test_define_and_lookup(self):
        scope = Scope("test")
        symbol = Symbol("x", INT, SymbolKind.VARIABLE)

        assert scope.define(symbol)
        assert scope.lookup("x") == symbol
        assert scope.lookup("y") is None

    def test_duplicate_definition(self):
        scope = Scope("test")
        symbol1 = Symbol("x", INT, SymbolKind.VARIABLE)
        symbol2 = Symbol("x", FLOAT, SymbolKind.VARIABLE)

        assert scope.define(symbol1)
        assert not scope.define(symbol2)  # Should fail

    def test_lookup_with_parent(self):
        parent = Scope("parent")
        child = Scope("child", parent=parent)

        parent_symbol = Symbol("x", INT, SymbolKind.VARIABLE)
        child_symbol = Symbol("y", FLOAT, SymbolKind.VARIABLE)

        parent.define(parent_symbol)
        child.define(child_symbol)

        # Child can see both
        assert child.lookup("x") == parent_symbol
        assert child.lookup("y") == child_symbol
        # Parent cannot see child's symbols
        assert parent.lookup("y") is None


class TestSymbolTable:
    """Test symbol table operations."""

    def test_initial_state(self):
        table = SymbolTable()
        assert table.scope_depth == 0
        assert table.is_global_scope()

    def test_enter_exit_scope(self):
        table = SymbolTable()

        table.enter_scope("block1")
        assert table.scope_depth == 1
        assert not table.is_global_scope()

        table.enter_scope("block2")
        assert table.scope_depth == 2

        table.exit_scope()
        assert table.scope_depth == 1

        table.exit_scope()
        assert table.scope_depth == 0

    def test_cannot_exit_global_scope(self):
        table = SymbolTable()
        with pytest.raises(RuntimeError):
            table.exit_scope()

    def test_define_and_lookup(self):
        table = SymbolTable()
        symbol = Symbol("x", INT, SymbolKind.VARIABLE)

        assert table.define(symbol)
        assert table.lookup("x") == symbol

    def test_scope_shadowing(self):
        table = SymbolTable()

        # Define in global scope
        global_x = Symbol("x", INT, SymbolKind.VARIABLE)
        table.define(global_x)

        # Enter new scope and shadow
        table.enter_scope("block")
        local_x = Symbol("x", STRING, SymbolKind.VARIABLE)
        table.define(local_x)

        # Local shadows global
        assert table.lookup("x") == local_x
        assert table.lookup_global("x") == global_x

        # Exit scope, global visible again
        table.exit_scope()
        assert table.lookup("x") == global_x

    def test_builtin_functions(self):
        table = create_symbol_table_with_builtins()

        print_sym = table.lookup("print")
        assert print_sym is not None
        assert print_sym.is_function

        input_sym = table.lookup("input")
        assert input_sym is not None

        len_sym = table.lookup("len")
        assert len_sym is not None


class TestSymbol:
    """Test symbol properties."""

    def test_variable_symbol(self):
        symbol = Symbol("x", INT, SymbolKind.VARIABLE)
        assert not symbol.is_const
        assert not symbol.is_function

    def test_constant_symbol(self):
        symbol = Symbol("PI", FLOAT, SymbolKind.CONSTANT)
        assert symbol.is_const
        assert not symbol.is_function

    def test_function_symbol(self):
        func_type = FunctionType([INT], INT)
        symbol = Symbol("foo", func_type, SymbolKind.FUNCTION)
        assert symbol.is_function
        assert not symbol.is_const


# =============================================================================
# Semantic Analysis Tests - Valid Programs
# =============================================================================

class TestValidPrograms:
    """Test that valid programs pass semantic analysis."""

    def test_minimal_program(self):
        source = "fn main() -> int { return 0; }"
        symbol_table = analyze_source(source)
        assert symbol_table.lookup("main") is not None

    def test_variable_declaration(self):
        source = """
        fn main() -> int {
            let x: int = 42;
            return x;
        }
        """
        analyze_source(source)

    def test_constant_declaration(self):
        source = """
        fn main() -> int {
            const PI: float = 3.14;
            return 0;
        }
        """
        analyze_source(source)

    def test_arithmetic_operations(self):
        source = """
        fn main() -> int {
            let a: int = 1 + 2;
            let b: int = 3 - 1;
            let c: int = 2 * 3;
            let d: int = 10 / 2;
            let e: int = 10 % 3;
            return a + b + c + d + e;
        }
        """
        analyze_source(source)

    def test_comparison_operations(self):
        source = """
        fn main() -> int {
            let a: bool = 1 < 2;
            let b: bool = 2 > 1;
            let c: bool = 1 <= 1;
            let d: bool = 2 >= 2;
            let e: bool = 1 == 1;
            let f: bool = 1 != 2;
            return 0;
        }
        """
        analyze_source(source)

    def test_logical_operations(self):
        source = """
        fn main() -> int {
            let a: bool = true && false;
            let b: bool = true || false;
            let c: bool = !true;
            return 0;
        }
        """
        analyze_source(source)

    def test_function_with_parameters(self):
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(1, 2);
        }
        """
        analyze_source(source)

    def test_recursive_function(self):
        source = """
        fn factorial(n: int) -> int {
            if n <= 1 {
                return 1;
            }
            return n * factorial(n - 1);
        }

        fn main() -> int {
            return factorial(5);
        }
        """
        analyze_source(source)

    def test_if_else_statement(self):
        source = """
        fn main() -> int {
            let x: int = 10;
            if x > 0 {
                return 1;
            } else {
                return -1;
            }
        }
        """
        analyze_source(source)

    def test_while_loop(self):
        source = """
        fn main() -> int {
            let i: int = 0;
            while i < 10 {
                i = i + 1;
            }
            return i;
        }
        """
        analyze_source(source)

    def test_nested_scopes(self):
        source = """
        fn main() -> int {
            let x: int = 1;
            if true {
                let y: int = 2;
                x = x + y;
            }
            return x;
        }
        """
        analyze_source(source)

    def test_variable_shadowing(self):
        source = """
        fn main() -> int {
            let x: int = 1;
            if true {
                let x: int = 2;
            }
            return x;
        }
        """
        analyze_source(source)

    def test_print_function(self):
        source = """
        fn main() -> int {
            print(42);
            print(3.14);
            print("hello");
            print(true);
            return 0;
        }
        """
        analyze_source(source)


# =============================================================================
# Semantic Analysis Tests - Error Detection
# =============================================================================

class TestTypeErrors:
    """Test type error detection."""

    def test_type_mismatch_in_variable(self):
        source = """
        fn main() -> int {
            let x: int = "hello";
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "int" in str(exc.value) and "string" in str(exc.value)

    def test_type_mismatch_in_assignment(self):
        source = """
        fn main() -> int {
            let x: int = 42;
            x = "hello";
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Cannot assign" in str(exc.value)

    def test_invalid_arithmetic_operands(self):
        source = """
        fn main() -> int {
            let x: int = true + false;
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Invalid operand" in str(exc.value)

    def test_invalid_comparison_operands(self):
        source = """
        fn main() -> int {
            let x: bool = 1 < "hello";
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Invalid operand" in str(exc.value)

    def test_invalid_logical_operands(self):
        source = """
        fn main() -> int {
            let x: bool = 1 && 2;
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Invalid operand" in str(exc.value)

    def test_invalid_unary_minus(self):
        source = """
        fn main() -> int {
            let x: int = -"hello";
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Invalid operand" in str(exc.value)

    def test_invalid_logical_not(self):
        source = """
        fn main() -> int {
            let x: bool = !42;
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Invalid operand" in str(exc.value)


class TestUndefinedSymbolErrors:
    """Test undefined symbol detection."""

    def test_undefined_variable(self):
        source = """
        fn main() -> int {
            return x;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Undefined variable 'x'" in str(exc.value)

    def test_undefined_function(self):
        source = """
        fn main() -> int {
            return foo();
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Undefined function 'foo'" in str(exc.value)


class TestDuplicateDeclarationErrors:
    """Test duplicate declaration detection."""

    def test_duplicate_variable(self):
        source = """
        fn main() -> int {
            let x: int = 1;
            let x: int = 2;
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "already declared" in str(exc.value)

    def test_duplicate_function(self):
        source = """
        fn foo() -> int { return 1; }
        fn foo() -> int { return 2; }
        fn main() -> int { return 0; }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "already defined" in str(exc.value)


class TestConstantErrors:
    """Test constant-related error detection."""

    def test_assign_to_constant(self):
        source = """
        fn main() -> int {
            const PI: float = 3.14;
            PI = 3.0;
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Cannot assign to constant" in str(exc.value)


class TestFunctionCallErrors:
    """Test function call error detection."""

    def test_wrong_argument_count(self):
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(1);
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "expects 2 argument(s) but got 1" in str(exc.value)

    def test_wrong_argument_type(self):
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(1, "two");
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "wrong type" in str(exc.value)


class TestControlFlowErrors:
    """Test control flow error detection."""

    def test_if_condition_not_boolean(self):
        source = """
        fn main() -> int {
            if 42 {
                return 1;
            }
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "must be a boolean" in str(exc.value)

    def test_while_condition_not_boolean(self):
        source = """
        fn main() -> int {
            while "forever" {
                return 1;
            }
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "must be a boolean" in str(exc.value)


class TestReturnErrors:
    """Test return statement error detection."""

    def test_return_type_mismatch(self):
        source = """
        fn main() -> int {
            return "hello";
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Return type mismatch" in str(exc.value)

    def test_return_value_from_void(self):
        source = """
        fn foo() -> void {
            return 42;
        }

        fn main() -> int {
            return 0;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "Cannot return a value from void" in str(exc.value)


class TestMainFunctionErrors:
    """Test main function validation."""

    def test_missing_main(self):
        source = """
        fn foo() -> int {
            return 42;
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "must have a 'main' function" in str(exc.value)

    def test_main_wrong_return_type(self):
        source = """
        fn main() -> void {
            print(42);
        }
        """
        with pytest.raises(SemanticError) as exc:
            analyze_source(source)
        assert "must return 'int'" in str(exc.value)


# =============================================================================
# Integration Tests
# =============================================================================

class TestExamplePrograms:
    """Test the example programs pass semantic analysis."""

    def test_hello_world(self):
        with open("examples/hello_world.toy") as f:
            analyze_source(f.read())

    def test_fibonacci(self):
        with open("examples/fibonacci.toy") as f:
            analyze_source(f.read())

    def test_factorial(self):
        with open("examples/factorial.toy") as f:
            analyze_source(f.read())

    def test_fizzbuzz(self):
        with open("examples/fizzbuzz.toy") as f:
            analyze_source(f.read())
