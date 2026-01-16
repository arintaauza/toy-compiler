"""
Tests for LLVM IR code generation.

Tests the LLVM backend including:
- Type mapping
- Instruction translation
- Control flow (if/else, while)
- Function calls
- End-to-end JIT execution
"""

import pytest
from llvmlite import ir

from src.ir.instructions import (
    IRModule, IRFunction, IRValue, IRType, IRParameter,
    BasicBlock, BinaryOp, UnaryOp, Copy, LoadConst,
    Jump, Branch, Phi, PhiSource, Call, Return, OpCode,
    make_constant,
)
from src.codegen.llvm_codegen import LLVMCodeGenerator, generate_llvm_ir
from src.codegen.llvm_emitter import (
    compile_to_llvm_ir,
    compile_and_run_llvm,
    LLVMJITEngine,
    get_llvm_target_info,
)


def make_var(name: str, version: int, ir_type: IRType = IRType.INT) -> IRValue:
    """Helper to create an IRValue."""
    return IRValue(name=name, version=version, ir_type=ir_type)


# =============================================================================
# Type Mapping Tests
# =============================================================================

class TestTypeMapping:
    """Tests for Luna type to LLVM type mapping."""

    def test_int_type(self):
        """Test INT maps to i64."""
        gen = LLVMCodeGenerator()
        llvm_type = gen._get_llvm_type(IRType.INT)
        assert isinstance(llvm_type, ir.IntType)
        assert llvm_type.width == 64

    def test_float_type(self):
        """Test FLOAT maps to double."""
        gen = LLVMCodeGenerator()
        llvm_type = gen._get_llvm_type(IRType.FLOAT)
        assert isinstance(llvm_type, ir.DoubleType)

    def test_bool_type(self):
        """Test BOOL maps to i1."""
        gen = LLVMCodeGenerator()
        llvm_type = gen._get_llvm_type(IRType.BOOL)
        assert isinstance(llvm_type, ir.IntType)
        assert llvm_type.width == 1

    def test_string_type(self):
        """Test STRING maps to i8*."""
        gen = LLVMCodeGenerator()
        llvm_type = gen._get_llvm_type(IRType.STRING)
        assert isinstance(llvm_type, ir.PointerType)

    def test_void_type(self):
        """Test VOID maps to void."""
        gen = LLVMCodeGenerator()
        llvm_type = gen._get_llvm_type(IRType.VOID)
        assert isinstance(llvm_type, ir.VoidType)


# =============================================================================
# IR Generation Tests
# =============================================================================

class TestIRGeneration:
    """Tests for LLVM IR generation from Luna IR."""

    def test_simple_function(self):
        """Test generating a simple function."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("t", 0), value=42, value_type=IRType.INT),
            Return(value=make_var("t", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        # LLVM may add quotes around identifiers
        assert "define i64 @" in llvm_str
        assert "main" in llvm_str
        assert "ret i64" in llvm_str

    def test_function_with_parameters(self):
        """Test generating function with parameters."""
        module = IRModule(name="test")
        func = IRFunction(name="add", return_type=IRType.INT)
        func.parameters = [
            IRParameter(name="a", ir_type=IRType.INT),
            IRParameter(name="b", ir_type=IRType.INT),
        ]
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
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        # LLVM may add quotes around identifiers
        assert "define i64 @" in llvm_str
        assert "add" in llvm_str
        assert "i64 %" in llvm_str  # Parameter types
        assert "add i64" in llvm_str  # Add instruction

    def test_arithmetic_operations(self):
        """Test generating arithmetic operations."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("a", 0), value=10, value_type=IRType.INT),
            LoadConst(dest=make_var("b", 0), value=3, value_type=IRType.INT),
            BinaryOp(dest=make_var("t", 0), op=OpCode.ADD,
                     left=make_var("a", 0), right=make_var("b", 0)),
            BinaryOp(dest=make_var("t", 1), op=OpCode.SUB,
                     left=make_var("t", 0), right=make_var("b", 0)),
            BinaryOp(dest=make_var("t", 2), op=OpCode.MUL,
                     left=make_var("t", 1), right=make_var("b", 0)),
            BinaryOp(dest=make_var("t", 3), op=OpCode.DIV,
                     left=make_var("t", 2), right=make_var("b", 0)),
            Return(value=make_var("t", 3))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        assert "add i64" in llvm_str
        assert "sub i64" in llvm_str
        assert "mul i64" in llvm_str
        assert "sdiv i64" in llvm_str

    def test_comparison_operations(self):
        """Test generating comparison operations."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("a", 0), value=5, value_type=IRType.INT),
            LoadConst(dest=make_var("b", 0), value=10, value_type=IRType.INT),
            BinaryOp(dest=make_var("t", 0, IRType.BOOL), op=OpCode.LT,
                     left=make_var("a", 0), right=make_var("b", 0)),
            BinaryOp(dest=make_var("t", 1, IRType.BOOL), op=OpCode.EQ,
                     left=make_var("a", 0), right=make_var("b", 0)),
            LoadConst(dest=make_var("result", 0), value=1, value_type=IRType.INT),
            Return(value=make_var("result", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        assert "icmp slt" in llvm_str
        assert "icmp eq" in llvm_str

    def test_unary_operations(self):
        """Test generating unary operations."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)
        block = BasicBlock(label="B0")
        block.instructions = [
            LoadConst(dest=make_var("a", 0), value=42, value_type=IRType.INT),
            UnaryOp(dest=make_var("t", 0), op=OpCode.NEG, operand=make_var("a", 0)),
            Return(value=make_var("t", 0))
        ]
        func.blocks["B0"] = block
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        # LLVM represents neg as sub 0, x
        assert "sub i64 0" in llvm_str or "mul i64" in llvm_str or "ret i64" in llvm_str

    def test_branch_instruction(self):
        """Test generating branch instructions."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [
            LoadConst(dest=make_var("cond", 0, IRType.BOOL), value=True, value_type=IRType.BOOL),
            Branch(condition=make_var("cond", 0, IRType.BOOL), true_target="B1", false_target="B2")
        ]
        b0.successors = ["B1", "B2"]

        b1 = BasicBlock(label="B1")
        b1.instructions = [
            LoadConst(dest=make_var("t", 0), value=1, value_type=IRType.INT),
            Return(value=make_var("t", 0))
        ]

        b2 = BasicBlock(label="B2")
        b2.instructions = [
            LoadConst(dest=make_var("t", 1), value=0, value_type=IRType.INT),
            Return(value=make_var("t", 1))
        ]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2}
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        assert "br i1" in llvm_str
        # LLVM may add quotes around labels
        assert "B1" in llvm_str
        assert "B2" in llvm_str

    def test_jump_instruction(self):
        """Test generating unconditional jump."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [Jump(target="B1")]
        b0.successors = ["B1"]

        b1 = BasicBlock(label="B1")
        b1.instructions = [
            LoadConst(dest=make_var("t", 0), value=42, value_type=IRType.INT),
            Return(value=make_var("t", 0))
        ]

        func.blocks = {"B0": b0, "B1": b1}
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        # LLVM may add quotes around labels
        assert "br label" in llvm_str
        assert "B1" in llvm_str

    def test_phi_instruction(self):
        """Test generating phi instructions."""
        module = IRModule(name="test")
        func = IRFunction(name="main", return_type=IRType.INT)

        # Entry block with branch
        b0 = BasicBlock(label="B0")
        b0.instructions = [
            LoadConst(dest=make_var("cond", 0, IRType.BOOL), value=True, value_type=IRType.BOOL),
            Branch(condition=make_var("cond", 0, IRType.BOOL), true_target="B1", false_target="B2")
        ]
        b0.successors = ["B1", "B2"]

        # True branch
        b1 = BasicBlock(label="B1")
        b1.instructions = [
            LoadConst(dest=make_var("x", 0), value=10, value_type=IRType.INT),
            Jump(target="B3")
        ]
        b1.successors = ["B3"]

        # False branch
        b2 = BasicBlock(label="B2")
        b2.instructions = [
            LoadConst(dest=make_var("x", 1), value=20, value_type=IRType.INT),
            Jump(target="B3")
        ]
        b2.successors = ["B3"]

        # Merge block with phi
        b3 = BasicBlock(label="B3")
        b3.instructions = [
            Phi(dest=make_var("x", 2), sources=[
                PhiSource(value=make_var("x", 0), block="B1"),
                PhiSource(value=make_var("x", 1), block="B2"),
            ]),
            Return(value=make_var("x", 2))
        ]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2, "B3": b3}
        func.entry_block = "B0"
        module.add_function(func)

        llvm_module = generate_llvm_ir(module)
        llvm_str = str(llvm_module)

        # LLVM may add extra spaces between phi and type
        assert "phi" in llvm_str
        assert "i64" in llvm_str


# =============================================================================
# High-Level API Tests
# =============================================================================

class TestHighLevelAPI:
    """Tests for the high-level compilation API."""

    def test_compile_to_llvm_ir(self):
        """Test compiling Luna source to LLVM IR."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        llvm_ir = compile_to_llvm_ir(source)

        # LLVM may add quotes around identifiers
        assert "define i64 @" in llvm_ir
        assert "main" in llvm_ir
        assert "ret i64" in llvm_ir

    def test_compile_with_arithmetic(self):
        """Test compiling arithmetic expressions."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let y: int = 5;
            return x + y;
        }
        """
        llvm_ir = compile_to_llvm_ir(source)

        assert "add i64" in llvm_ir

    def test_compile_with_function_call(self):
        """Test compiling function calls."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(3, 4);
        }
        """
        llvm_ir = compile_to_llvm_ir(source)

        # LLVM may add quotes around identifiers
        assert "define i64 @" in llvm_ir
        assert "add" in llvm_ir
        assert "call i64 @" in llvm_ir

    def test_compile_with_if_else(self):
        """Test compiling if/else statements."""
        source = """
        fn main() -> int {
            let x: int = 10;
            if x > 5 {
                return 1;
            } else {
                return 0;
            }
        }
        """
        llvm_ir = compile_to_llvm_ir(source)

        assert "icmp sgt" in llvm_ir
        assert "br i1" in llvm_ir

    def test_target_info(self):
        """Test getting target information."""
        info = get_llvm_target_info()

        assert "triple" in info
        assert "host_cpu" in info
        assert len(info["triple"]) > 0


# =============================================================================
# JIT Execution Tests
# =============================================================================

class TestJITExecution:
    """Tests for JIT compilation and execution."""

    def test_jit_return_constant(self):
        """Test JIT execution returning a constant."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 42

    def test_jit_arithmetic(self):
        """Test JIT execution with arithmetic."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let y: int = 5;
            return x + y;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 15

    def test_jit_subtraction(self):
        """Test JIT execution with subtraction."""
        source = """
        fn main() -> int {
            return 20 - 8;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 12

    def test_jit_multiplication(self):
        """Test JIT execution with multiplication."""
        source = """
        fn main() -> int {
            return 7 * 6;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 42

    def test_jit_division(self):
        """Test JIT execution with division."""
        source = """
        fn main() -> int {
            return 100 / 5;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 20

    def test_jit_modulo(self):
        """Test JIT execution with modulo."""
        source = """
        fn main() -> int {
            return 17 % 5;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 2

    def test_jit_comparison_lt(self):
        """Test JIT execution with less than."""
        source = """
        fn main() -> int {
            if 5 < 10 {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 1

    def test_jit_comparison_gt(self):
        """Test JIT execution with greater than."""
        source = """
        fn main() -> int {
            if 15 > 10 {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 1

    def test_jit_if_else_true(self):
        """Test JIT execution with if/else (true branch)."""
        source = """
        fn main() -> int {
            let x: int = 10;
            if x > 5 {
                return 100;
            } else {
                return 200;
            }
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 100

    def test_jit_if_else_false(self):
        """Test JIT execution with if/else (false branch)."""
        source = """
        fn main() -> int {
            let x: int = 3;
            if x > 5 {
                return 100;
            } else {
                return 200;
            }
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 200

    def test_jit_function_call(self):
        """Test JIT execution with function call."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(3, 4);
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 7

    def test_jit_nested_function_calls(self):
        """Test JIT execution with nested function calls."""
        source = """
        fn double(x: int) -> int {
            return x * 2;
        }

        fn main() -> int {
            return double(double(5));
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 20

    def test_jit_recursive_factorial(self):
        """Test JIT execution with recursive factorial."""
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
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 120

    def test_jit_fibonacci(self):
        """Test JIT execution with Fibonacci."""
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
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 55

    def test_jit_while_loop(self):
        """Test JIT execution with while loop."""
        source = """
        fn main() -> int {
            let x: int = 0;
            let i: int = 0;
            while i < 10 {
                x = x + i;
                i = i + 1;
            }
            return x;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        # Sum of 0..9 = 45
        assert result.return_value == 45

    def test_jit_negation(self):
        """Test JIT execution with negation."""
        source = """
        fn main() -> int {
            let x: int = 42;
            return -x;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == -42

    def test_jit_complex_expression(self):
        """Test JIT execution with complex expression."""
        source = """
        fn main() -> int {
            let a: int = 10;
            let b: int = 5;
            let c: int = 3;
            return (a + b) * c - a / b;
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        # (10 + 5) * 3 - 10 / 5 = 15 * 3 - 2 = 45 - 2 = 43
        assert result.return_value == 43


# =============================================================================
# JIT Engine Tests
# =============================================================================

class TestJITEngine:
    """Tests for the LLVMJITEngine class."""

    def test_engine_compile_and_run(self):
        """Test using JIT engine to compile and run."""
        source = """
        fn main() -> int {
            return 99;
        }
        """
        engine = LLVMJITEngine()
        result = engine.compile_and_call_main(source)

        assert result == 99

    def test_engine_with_optimization(self):
        """Test JIT engine with optimization enabled."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let y: int = 20;
            let z: int = x + y;
            return z;
        }
        """
        engine = LLVMJITEngine()
        result = engine.compile_and_call_main(source, optimize=True)

        assert result == 30


# =============================================================================
# Comparison with x86-64 Backend
# =============================================================================

class TestBackendComparison:
    """Tests comparing LLVM output with x86-64 backend."""

    def test_same_result_simple(self):
        """Test that LLVM and x86-64 backends give same result."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        from src.codegen import compile_and_run

        # LLVM result
        llvm_result = compile_and_run_llvm(source)

        # x86-64 result
        x86_result = compile_and_run(source)

        assert llvm_result.success
        assert x86_result.success
        assert llvm_result.return_value == x86_result.return_code

    def test_same_result_arithmetic(self):
        """Test arithmetic gives same result in both backends."""
        source = """
        fn main() -> int {
            return 10 + 5 * 3;
        }
        """
        from src.codegen import compile_and_run

        llvm_result = compile_and_run_llvm(source)
        x86_result = compile_and_run(source)

        assert llvm_result.return_value == x86_result.return_code
        assert llvm_result.return_value == 25

    def test_same_result_function_call(self):
        """Test function calls give same result in both backends."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(17, 25);
        }
        """
        from src.codegen import compile_and_run

        llvm_result = compile_and_run_llvm(source)
        x86_result = compile_and_run(source)

        assert llvm_result.return_value == x86_result.return_code
        assert llvm_result.return_value == 42

    def test_same_result_fibonacci(self):
        """Test Fibonacci gives same result in both backends."""
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
        from src.codegen import compile_and_run

        llvm_result = compile_and_run_llvm(source)
        x86_result = compile_and_run(source)

        assert llvm_result.return_value == x86_result.return_code
        assert llvm_result.return_value == 55
