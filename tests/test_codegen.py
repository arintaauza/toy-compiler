"""
Tests for x86-64 code generation.

Tests cover:
- Stack frame allocation
- Instruction generation
- Full compilation pipeline
- End-to-end execution tests
"""

import pytest
import subprocess
import os
import tempfile

from src.ir.instructions import (
    IRModule,
    IRFunction,
    BasicBlock,
    IRParameter,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Jump,
    Branch,
    Phi,
    PhiSource,
    Call,
    Return,
    IRValue,
    IRType,
    OpCode,
)
from src.codegen.stack_frame import StackFrame, StackFrameBuilder, StackSlot
from src.codegen.x86_64_codegen import X86_64CodeGenerator, generate_assembly
from src.codegen.asm_emitter import (
    compile_source_to_asm,
    compile_and_run,
    CompileResult,
)


# =============================================================================
# Helper Functions
# =============================================================================

def make_var(name: str, version: int, ir_type: IRType = IRType.INT) -> IRValue:
    """Create a variable IRValue."""
    return IRValue(name=name, version=version, ir_type=ir_type)


def make_int(value: int) -> IRValue:
    """Create an integer constant IRValue."""
    return IRValue(
        name="", version=0, ir_type=IRType.INT,
        is_constant=True, constant_value=value
    )


def can_run_native_code() -> bool:
    """Check if we can compile and run native code (macOS Intel or Linux x86-64)."""
    import platform
    system = platform.system()
    machine = platform.machine()

    # Check for x86-64 architecture
    if machine not in ('x86_64', 'AMD64'):
        return False

    # Check for required tools
    try:
        subprocess.run(['as', '--version'], capture_output=True)
        subprocess.run(['gcc', '--version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False


# Skip marker for tests that require native execution
requires_native = pytest.mark.skipif(
    not can_run_native_code(),
    reason="Requires x86-64 and assembler/linker tools"
)


# =============================================================================
# Stack Frame Tests
# =============================================================================

class TestStackFrame:
    """Tests for stack frame allocation."""

    def test_allocate_variable(self):
        """Test allocating a single variable."""
        frame = StackFrame(function_name="test")
        slot = frame.allocate("x", 0)

        assert slot.offset == -8
        assert slot.size == 8

    def test_allocate_multiple_variables(self):
        """Test allocating multiple variables."""
        frame = StackFrame(function_name="test")
        slot1 = frame.allocate("x", 0)
        slot2 = frame.allocate("y", 0)
        slot3 = frame.allocate("z", 0)

        assert slot1.offset == -8
        assert slot2.offset == -16
        assert slot3.offset == -24

    def test_allocate_same_variable_returns_same_slot(self):
        """Test that allocating the same variable returns the same slot."""
        frame = StackFrame(function_name="test")
        slot1 = frame.allocate("x", 0)
        slot2 = frame.allocate("x", 0)

        assert slot1 is slot2

    def test_ssa_versions_get_different_slots(self):
        """Test that different SSA versions get different slots."""
        frame = StackFrame(function_name="test")
        slot1 = frame.allocate("x", 0)
        slot2 = frame.allocate("x", 1)
        slot3 = frame.allocate("x", 2)

        assert slot1.offset != slot2.offset
        assert slot2.offset != slot3.offset

    def test_frame_size_alignment(self):
        """Test that frame size is aligned to 16 bytes."""
        frame = StackFrame(function_name="test")
        frame.allocate("x", 0)  # -8 bytes

        # Should round up to 16
        assert frame.frame_size == 16

        frame.allocate("y", 0)  # -16 bytes
        assert frame.frame_size == 16

        frame.allocate("z", 0)  # -24 bytes
        assert frame.frame_size == 32

    def test_get_slot_for_constant_returns_none(self):
        """Test that get_slot returns None for constants."""
        frame = StackFrame(function_name="test")
        const = make_int(42)

        assert frame.get_slot(const) is None

    def test_get_or_allocate(self):
        """Test get_or_allocate creates new slot if needed."""
        frame = StackFrame(function_name="test")
        var = make_var("x", 0)

        # First call should allocate
        slot1 = frame.get_or_allocate(var)
        assert slot1 is not None

        # Second call should return same slot
        slot2 = frame.get_or_allocate(var)
        assert slot1 is slot2


class TestStackFrameBuilder:
    """Tests for stack frame builder."""

    def test_build_simple_function(self):
        """Test building frame for a simple function."""
        func = IRFunction(name="test", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("x", 0), value=42, value_type=IRType.INT),
            Return(value=make_var("x", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"

        builder = StackFrameBuilder()
        frame = builder.build(func)

        # Should have slot for x_0
        assert frame.get_slot(make_var("x", 0)) is not None

    def test_build_function_with_parameters(self):
        """Test building frame for function with parameters."""
        func = IRFunction(
            name="add",
            parameters=[
                IRParameter(name="a", ir_type=IRType.INT),
                IRParameter(name="b", ir_type=IRType.INT),
            ],
            return_type=IRType.INT
        )
        block = BasicBlock(label="B0")
        block.instructions = [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_var("a", 0),
                right=make_var("b", 0)
            ),
            Return(value=make_var("t", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"

        builder = StackFrameBuilder()
        frame = builder.build(func)

        # Should have slots for a_0, b_0, and t_0
        assert frame.get_slot(make_var("a", 0)) is not None
        assert frame.get_slot(make_var("b", 0)) is not None
        assert frame.get_slot(make_var("t", 0)) is not None

    def test_param_registers(self):
        """Test getting parameter registers."""
        builder = StackFrameBuilder()

        assert builder.get_param_register(0) == "rdi"
        assert builder.get_param_register(1) == "rsi"
        assert builder.get_param_register(5) == "r9"
        assert builder.get_param_register(6) is None  # On stack


# =============================================================================
# Assembly Generation Tests
# =============================================================================

class TestAssemblyGeneration:
    """Tests for assembly code generation."""

    def test_generate_simple_function(self):
        """Test generating assembly for a simple function."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("x", 0), value=42, value_type=IRType.INT),
            Return(value=make_var("x", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        asm = generate_assembly(module)

        assert "_main:" in asm
        assert "pushq %rbp" in asm
        assert "movq %rsp, %rbp" in asm
        assert "retq" in asm

    def test_generate_arithmetic(self):
        """Test generating assembly for arithmetic operations."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("a", 0), value=10, value_type=IRType.INT),
            LoadConst(dest=make_var("b", 0), value=5, value_type=IRType.INT),
            BinaryOp(
                dest=make_var("sum", 0),
                op=OpCode.ADD,
                left=make_var("a", 0),
                right=make_var("b", 0)
            ),
            Return(value=make_var("sum", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        asm = generate_assembly(module)

        assert "addq" in asm
        assert "%rax" in asm

    def test_generate_comparison(self):
        """Test generating assembly for comparison operations."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("a", 0), value=10, value_type=IRType.INT),
            LoadConst(dest=make_var("b", 0), value=5, value_type=IRType.INT),
            BinaryOp(
                dest=make_var("cmp", 0, IRType.BOOL),
                op=OpCode.LT,
                left=make_var("a", 0),
                right=make_var("b", 0)
            ),
            Return(value=make_var("cmp", 0, IRType.BOOL))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        asm = generate_assembly(module)

        assert "cmpq" in asm
        assert "setl %al" in asm

    def test_generate_branch(self):
        """Test generating assembly for branch instructions."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [
            LoadConst(dest=make_var("cond", 0, IRType.BOOL), value=True, value_type=IRType.BOOL),
            Branch(
                condition=make_var("cond", 0, IRType.BOOL),
                true_target="B1",
                false_target="B2"
            )
        ]

        b1 = BasicBlock(label="B1")
        b1.instructions = [Return(value=make_int(1))]

        b2 = BasicBlock(label="B2")
        b2.instructions = [Return(value=make_int(0))]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2}
        func.entry_block = "B0"
        module.add_function(func)

        asm = generate_assembly(module)

        assert "jne" in asm
        assert "jmp" in asm
        assert "_main_B0:" in asm
        assert "_main_B1:" in asm
        assert "_main_B2:" in asm


# =============================================================================
# Compilation Pipeline Tests
# =============================================================================

class TestCompilationPipeline:
    """Tests for the full compilation pipeline."""

    def test_compile_source_to_asm(self):
        """Test compiling Toy source to assembly."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        asm = compile_source_to_asm(source)

        assert ".section __TEXT,__text" in asm
        assert "_main:" in asm
        assert "ret" in asm

    def test_compile_with_arithmetic(self):
        """Test compiling source with arithmetic."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let y: int = 5;
            let z: int = x + y;
            return z;
        }
        """
        asm = compile_source_to_asm(source)

        assert "addq" in asm

    def test_compile_with_function_call(self):
        """Test compiling source with function call."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            let result: int = add(3, 4);
            return result;
        }
        """
        asm = compile_source_to_asm(source)

        assert "_add:" in asm
        assert "callq _add" in asm


# =============================================================================
# End-to-End Execution Tests
# =============================================================================

@requires_native
class TestEndToEndExecution:
    """End-to-end tests that compile and run programs."""

    def test_return_constant(self):
        """Test program that returns a constant."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_arithmetic_addition(self):
        """Test addition."""
        source = """
        fn main() -> int {
            let x: int = 30;
            let y: int = 12;
            return x + y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_arithmetic_subtraction(self):
        """Test subtraction."""
        source = """
        fn main() -> int {
            let x: int = 50;
            let y: int = 8;
            return x - y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_arithmetic_multiplication(self):
        """Test multiplication."""
        source = """
        fn main() -> int {
            let x: int = 6;
            let y: int = 7;
            return x * y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_arithmetic_division(self):
        """Test division."""
        source = """
        fn main() -> int {
            let x: int = 84;
            let y: int = 2;
            return x / y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_arithmetic_modulo(self):
        """Test modulo."""
        source = """
        fn main() -> int {
            let x: int = 47;
            let y: int = 5;
            return x % y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 2  # 47 % 5 = 2

    def test_comparison_less_than_true(self):
        """Test less than comparison (true case)."""
        source = """
        fn main() -> int {
            let x: int = 5;
            let y: int = 10;
            if x < y {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 1

    def test_comparison_less_than_false(self):
        """Test less than comparison (false case)."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let y: int = 5;
            if x < y {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 0

    def test_if_else(self):
        """Test if-else statement."""
        source = """
        fn main() -> int {
            let x: int = 10;
            if x > 5 {
                return 42;
            } else {
                return 0;
            }
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_while_loop(self):
        """Test while loop."""
        source = """
        fn main() -> int {
            let x: int = 0;
            while x < 10 {
                x = x + 1;
            }
            return x;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 10

    def test_function_call(self):
        """Test function call."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(20, 22);
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_recursive_function(self):
        """Test recursive function (factorial)."""
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
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 120  # 5! = 120

    def test_fibonacci(self):
        """Test fibonacci function."""
        source = """
        fn fib(n: int) -> int {
            if n <= 1 {
                return n;
            }
            return fib(n - 1) + fib(n - 2);
        }

        fn main() -> int {
            return fib(10);
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 55  # fib(10) = 55

    def test_negation(self):
        """Test unary negation."""
        source = """
        fn main() -> int {
            let x: int = 42;
            let y: int = -x;
            return -y;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42

    def test_logical_not(self):
        """Test logical not."""
        source = """
        fn main() -> int {
            let x: bool = true;
            if !x {
                return 0;
            }
            return 1;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 1

    def test_print_integer(self):
        """Test print function with integer."""
        source = """
        fn main() -> int {
            print(42);
            return 0;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert "42" in result.stdout

    def test_multiple_prints(self):
        """Test multiple print calls."""
        source = """
        fn main() -> int {
            print(1);
            print(2);
            print(3);
            return 0;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert "1" in result.stdout
        assert "2" in result.stdout
        assert "3" in result.stdout

    def test_complex_expression(self):
        """Test complex arithmetic expression."""
        source = """
        fn main() -> int {
            let a: int = 10;
            let b: int = 5;
            let c: int = 2;
            return (a + b) * c - 8;
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 22  # (10 + 5) * 2 - 8 = 22

    def test_nested_function_calls(self):
        """Test nested function calls."""
        source = """
        fn double(x: int) -> int {
            return x * 2;
        }

        fn add_one(x: int) -> int {
            return x + 1;
        }

        fn main() -> int {
            return double(add_one(20));
        }
        """
        result = compile_and_run(source)

        assert result.success, f"Compilation failed: {result.error_message}"
        assert result.return_code == 42  # double(21) = 42


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and corner cases."""

    def test_empty_function_generates_valid_asm(self):
        """Test that empty function generates valid assembly."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [Return(value=make_int(0))]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        asm = generate_assembly(module)

        assert "_main:" in asm
        assert "ret" in asm

    def test_many_local_variables(self):
        """Test function with many local variables."""
        source = """
        fn main() -> int {
            let a: int = 1;
            let b: int = 2;
            let c: int = 3;
            let d: int = 4;
            let e: int = 5;
            let f: int = 6;
            let g: int = 7;
            let h: int = 8;
            let i: int = 9;
            let j: int = 10;
            return a + b + c + d + e + f + g + h + i + j;
        }
        """
        asm = compile_source_to_asm(source)

        # Should successfully generate assembly
        assert "_main:" in asm

    def test_deeply_nested_if(self):
        """Test deeply nested if statements."""
        source = """
        fn main() -> int {
            let x: int = 5;
            if x > 0 {
                if x > 1 {
                    if x > 2 {
                        return 42;
                    }
                }
            }
            return 0;
        }
        """
        asm = compile_source_to_asm(source)

        # Should have multiple branch labels (then/merge blocks)
        assert "_main_" in asm
        assert "jne" in asm
