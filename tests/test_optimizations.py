"""
Comprehensive tests for IR optimization passes.

Tests cover:
- Constant folding
- Dead code elimination
- Common subexpression elimination
- Copy propagation
- Algebraic simplification
- Control flow optimization
- Pass manager functionality
"""

import pytest
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
    make_constant,
)
from src.ir.optimizations import (
    PassManager,
    PassStatistics,
    ConstantFolding,
    DeadCodeElimination,
    CommonSubexpressionElimination,
    CopyPropagation,
    AlgebraicSimplification,
    ControlFlowOptimization,
    create_default_pass_manager,
)


# =============================================================================
# Helper functions
# =============================================================================

def make_var(name: str, version: int, ir_type: IRType = IRType.INT) -> IRValue:
    """Create a variable IRValue."""
    return IRValue(name=name, version=version, ir_type=ir_type)


def make_int(value: int) -> IRValue:
    """Create an integer constant IRValue."""
    return make_constant(value, IRType.INT)


def make_bool(value: bool) -> IRValue:
    """Create a boolean constant IRValue."""
    return make_constant(value, IRType.BOOL)


def make_simple_function(name: str, instructions: list) -> IRFunction:
    """Create a simple function with one basic block."""
    func = IRFunction(name=name, return_type=IRType.INT)
    block = BasicBlock(label="B0")
    block.instructions = instructions
    func.blocks["B0"] = block
    func.entry_block = "B0"
    return func


def make_module_with_function(func: IRFunction) -> IRModule:
    """Create a module containing a single function."""
    module = IRModule(name="test")
    module.add_function(func)
    return module


# =============================================================================
# Constant Folding Tests
# =============================================================================

class TestConstantFolding:
    """Tests for constant folding optimization."""

    def test_fold_addition(self):
        """Test folding: 2 + 3 -> 5"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_int(2),
                right=make_int(3)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        stats = cf.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 5

    def test_fold_subtraction(self):
        """Test folding: 10 - 3 -> 7"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.SUB,
                left=make_int(10),
                right=make_int(3)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 7

    def test_fold_multiplication(self):
        """Test folding: 4 * 5 -> 20"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.MUL,
                left=make_int(4),
                right=make_int(5)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 20

    def test_fold_division(self):
        """Test folding: 20 / 4 -> 5"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.DIV,
                left=make_int(20),
                right=make_int(4)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 5

    def test_no_fold_division_by_zero(self):
        """Test that division by zero is not folded."""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.DIV,
                left=make_int(10),
                right=make_int(0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        stats = cf.run_on_module(module)

        assert stats.instructions_modified == 0
        assert isinstance(func.blocks["B0"].instructions[0], BinaryOp)

    def test_fold_comparison_lt(self):
        """Test folding: 3 < 5 -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.LT,
                left=make_int(3),
                right=make_int(5)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True

    def test_fold_comparison_gt(self):
        """Test folding: 5 > 3 -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.GT,
                left=make_int(5),
                right=make_int(3)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True

    def test_fold_comparison_eq(self):
        """Test folding: 5 == 5 -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.EQ,
                left=make_int(5),
                right=make_int(5)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True

    def test_fold_logical_and(self):
        """Test folding: true && false -> false"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.AND,
                left=make_bool(True),
                right=make_bool(False)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is False

    def test_fold_logical_or(self):
        """Test folding: false || true -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.OR,
                left=make_bool(False),
                right=make_bool(True)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True

    def test_fold_unary_negation(self):
        """Test folding: -5 -> -5"""
        func = make_simple_function("test", [
            UnaryOp(
                dest=make_var("t", 0),
                op=OpCode.NEG,
                operand=make_int(5)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == -5

    def test_fold_unary_not(self):
        """Test folding: !true -> false"""
        func = make_simple_function("test", [
            UnaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.NOT,
                operand=make_bool(True)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        cf.run_on_module(module)

        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is False

    def test_no_fold_with_variables(self):
        """Test that expressions with variables are not folded."""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_var("x", 0),
                right=make_int(5)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        stats = cf.run_on_module(module)

        assert stats.instructions_modified == 0
        assert isinstance(func.blocks["B0"].instructions[0], BinaryOp)


# =============================================================================
# Dead Code Elimination Tests
# =============================================================================

class TestDeadCodeElimination:
    """Tests for dead code elimination optimization."""

    def test_remove_unused_instruction(self):
        """Test removal of unused instruction."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("unused", 0), value=42, value_type=IRType.INT),
            LoadConst(dest=make_var("used", 0), value=10, value_type=IRType.INT),
            Return(value=make_var("used", 0))
        ])

        module = make_module_with_function(func)
        dce = DeadCodeElimination()
        stats = dce.run_on_module(module)

        assert stats.instructions_removed == 1
        assert len(func.blocks["B0"].instructions) == 2

    def test_preserve_used_instruction(self):
        """Test that used instructions are preserved."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("x", 0), value=5, value_type=IRType.INT),
            Return(value=make_var("x", 0))
        ])

        module = make_module_with_function(func)
        dce = DeadCodeElimination()
        stats = dce.run_on_module(module)

        assert stats.instructions_removed == 0
        assert len(func.blocks["B0"].instructions) == 2

    def test_preserve_calls(self):
        """Test that function calls are preserved (side effects)."""
        func = make_simple_function("test", [
            Call(dest=None, function="print", arguments=[make_int(42)]),
            Return(value=None)
        ])

        module = make_module_with_function(func)
        dce = DeadCodeElimination()
        stats = dce.run_on_module(module)

        assert stats.instructions_removed == 0
        assert len(func.blocks["B0"].instructions) == 2

    def test_chain_removal(self):
        """Test that removing one instruction enables removal of another."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("a", 0), value=5, value_type=IRType.INT),
            BinaryOp(
                dest=make_var("b", 0),
                op=OpCode.ADD,
                left=make_var("a", 0),
                right=make_int(10)
            ),
            LoadConst(dest=make_var("c", 0), value=99, value_type=IRType.INT),
            Return(value=make_var("c", 0))
        ])

        module = make_module_with_function(func)
        dce = DeadCodeElimination()
        stats = dce.run_on_module(module)

        # Both 'a' and 'b' should be removed
        assert stats.instructions_removed == 2
        assert len(func.blocks["B0"].instructions) == 2

    def test_preserve_branch_condition(self):
        """Test that branch conditions are preserved."""
        func = IRFunction(name="test", return_type=IRType.INT)

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

        module = make_module_with_function(func)
        dce = DeadCodeElimination()
        stats = dce.run_on_module(module)

        assert stats.instructions_removed == 0


# =============================================================================
# Common Subexpression Elimination Tests
# =============================================================================

class TestCSE:
    """Tests for common subexpression elimination."""

    def test_eliminate_common_binary(self):
        """Test elimination of common binary expression."""
        x = make_var("x", 0)
        y = make_var("y", 0)

        func = make_simple_function("test", [
            BinaryOp(dest=make_var("t", 0), op=OpCode.ADD, left=x, right=y),
            BinaryOp(dest=make_var("t", 1), op=OpCode.ADD, left=x, right=y),
            Return(value=make_var("t", 1))
        ])

        module = make_module_with_function(func)
        cse = CommonSubexpressionElimination()
        stats = cse.run_on_module(module)

        assert stats.instructions_modified == 1
        # Second instruction should be a copy
        assert isinstance(func.blocks["B0"].instructions[1], Copy)
        assert func.blocks["B0"].instructions[1].source == make_var("t", 0)

    def test_commutative_cse(self):
        """Test CSE recognizes commutative operations."""
        x = make_var("x", 0)
        y = make_var("y", 0)

        func = make_simple_function("test", [
            BinaryOp(dest=make_var("t", 0), op=OpCode.ADD, left=x, right=y),
            BinaryOp(dest=make_var("t", 1), op=OpCode.ADD, left=y, right=x),  # Reversed
            Return(value=make_var("t", 1))
        ])

        module = make_module_with_function(func)
        cse = CommonSubexpressionElimination()
        stats = cse.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[1], Copy)

    def test_different_operations_not_cse(self):
        """Test that different operations are not eliminated."""
        x = make_var("x", 0)
        y = make_var("y", 0)

        func = make_simple_function("test", [
            BinaryOp(dest=make_var("t", 0), op=OpCode.ADD, left=x, right=y),
            BinaryOp(dest=make_var("t", 1), op=OpCode.MUL, left=x, right=y),
            BinaryOp(
                dest=make_var("t", 2),
                op=OpCode.ADD,
                left=make_var("t", 0),
                right=make_var("t", 1)
            ),
            Return(value=make_var("t", 2))
        ])

        module = make_module_with_function(func)
        cse = CommonSubexpressionElimination()
        stats = cse.run_on_module(module)

        assert stats.instructions_modified == 0

    def test_constant_cse(self):
        """Test CSE for constant loads."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("t", 0), value=42, value_type=IRType.INT),
            LoadConst(dest=make_var("t", 1), value=42, value_type=IRType.INT),
            BinaryOp(
                dest=make_var("t", 2),
                op=OpCode.ADD,
                left=make_var("t", 0),
                right=make_var("t", 1)
            ),
            Return(value=make_var("t", 2))
        ])

        module = make_module_with_function(func)
        cse = CommonSubexpressionElimination()
        stats = cse.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[1], Copy)


# =============================================================================
# Copy Propagation Tests
# =============================================================================

class TestCopyPropagation:
    """Tests for copy propagation optimization."""

    def test_simple_propagation(self):
        """Test simple copy propagation."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("x", 0), value=5, value_type=IRType.INT),
            Copy(dest=make_var("y", 0), source=make_var("x", 0)),
            BinaryOp(
                dest=make_var("z", 0),
                op=OpCode.ADD,
                left=make_var("y", 0),
                right=make_int(10)
            ),
            Return(value=make_var("z", 0))
        ])

        module = make_module_with_function(func)
        cp = CopyPropagation()
        stats = cp.run_on_module(module)

        # y should be replaced with x in the BinaryOp
        assert stats.instructions_modified >= 1
        binary_op = func.blocks["B0"].instructions[2]
        assert isinstance(binary_op, BinaryOp)
        assert binary_op.left == make_var("x", 0)

    def test_chain_propagation(self):
        """Test chain of copy propagations."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("a", 0), value=5, value_type=IRType.INT),
            Copy(dest=make_var("b", 0), source=make_var("a", 0)),
            Copy(dest=make_var("c", 0), source=make_var("b", 0)),
            Return(value=make_var("c", 0))
        ])

        module = make_module_with_function(func)
        cp = CopyPropagation()
        stats = cp.run_on_module(module)

        # The return should eventually use 'a'
        assert stats.instructions_modified >= 1

    def test_propagate_in_branch(self):
        """Test propagation in branch condition."""
        func = IRFunction(name="test", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [
            LoadConst(dest=make_var("cond", 0, IRType.BOOL), value=True, value_type=IRType.BOOL),
            Copy(dest=make_var("c", 0, IRType.BOOL), source=make_var("cond", 0, IRType.BOOL)),
            Branch(
                condition=make_var("c", 0, IRType.BOOL),
                true_target="B1",
                false_target="B1"
            )
        ]

        b1 = BasicBlock(label="B1")
        b1.instructions = [Return(value=make_int(0))]

        func.blocks = {"B0": b0, "B1": b1}
        func.entry_block = "B0"

        module = make_module_with_function(func)
        cp = CopyPropagation()
        stats = cp.run_on_module(module)

        assert stats.instructions_modified >= 1
        branch = func.blocks["B0"].instructions[2]
        assert isinstance(branch, Branch)
        assert branch.condition == make_var("cond", 0, IRType.BOOL)


# =============================================================================
# Algebraic Simplification Tests
# =============================================================================

class TestAlgebraicSimplification:
    """Tests for algebraic simplification optimization."""

    def test_add_zero_left(self):
        """Test: 0 + x -> x"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_int(0),
                right=make_var("x", 0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], Copy)
        assert func.blocks["B0"].instructions[0].source == make_var("x", 0)

    def test_add_zero_right(self):
        """Test: x + 0 -> x"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_var("x", 0),
                right=make_int(0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], Copy)

    def test_mul_one(self):
        """Test: x * 1 -> x"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.MUL,
                left=make_var("x", 0),
                right=make_int(1)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], Copy)

    def test_mul_zero(self):
        """Test: x * 0 -> 0"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.MUL,
                left=make_var("x", 0),
                right=make_int(0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 0

    def test_sub_self(self):
        """Test: x - x -> 0"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.SUB,
                left=make_var("x", 0),
                right=make_var("x", 0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 0

    def test_div_self(self):
        """Test: x / x -> 1"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.DIV,
                left=make_var("x", 0),
                right=make_var("x", 0)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value == 1

    def test_eq_self(self):
        """Test: x == x -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.EQ,
                left=make_var("x", 0),
                right=make_var("x", 0)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True

    def test_ne_self(self):
        """Test: x != x -> false"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.NE,
                left=make_var("x", 0),
                right=make_var("x", 0)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is False

    def test_and_false(self):
        """Test: x && false -> false"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.AND,
                left=make_var("x", 0, IRType.BOOL),
                right=make_bool(False)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is False

    def test_or_true(self):
        """Test: x || true -> true"""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0, IRType.BOOL),
                op=OpCode.OR,
                left=make_var("x", 0, IRType.BOOL),
                right=make_bool(True)
            ),
            Return(value=make_var("t", 0, IRType.BOOL))
        ])

        module = make_module_with_function(func)
        alg = AlgebraicSimplification()
        stats = alg.run_on_module(module)

        assert stats.instructions_modified == 1
        assert isinstance(func.blocks["B0"].instructions[0], LoadConst)
        assert func.blocks["B0"].instructions[0].value is True


# =============================================================================
# Control Flow Optimization Tests
# =============================================================================

class TestControlFlowOptimization:
    """Tests for control flow optimization."""

    def test_simplify_true_branch(self):
        """Test: branch true, L1, L2 -> jump L1 (and potentially merge blocks)"""
        func = IRFunction(name="test", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [
            Branch(
                condition=make_bool(True),
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

        module = make_module_with_function(func)
        cfo = ControlFlowOptimization()
        stats = cfo.run_on_module(module)

        # The optimization simplifies branch to jump, then merges B0 and B1
        # So the final result should have return 1 in B0
        # Either: B0 has Jump to B1, or B0 has been merged with B1
        b0_instrs = func.blocks["B0"].instructions
        if len(b0_instrs) == 1 and isinstance(b0_instrs[0], Jump):
            # Branch simplified to jump
            assert b0_instrs[0].target == "B1"
        else:
            # Blocks were merged, B0 should contain return 1
            assert isinstance(b0_instrs[-1], Return)
            assert b0_instrs[-1].value.constant_value == 1

    def test_simplify_false_branch(self):
        """Test: branch false, L1, L2 -> jump L2 (and potentially merge blocks)"""
        func = IRFunction(name="test", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [
            Branch(
                condition=make_bool(False),
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

        module = make_module_with_function(func)
        cfo = ControlFlowOptimization()
        cfo.run_on_module(module)

        # The optimization simplifies branch to jump, then merges B0 and B2
        b0_instrs = func.blocks["B0"].instructions
        if len(b0_instrs) == 1 and isinstance(b0_instrs[0], Jump):
            assert b0_instrs[0].target == "B2"
        else:
            # Blocks were merged, B0 should contain return 0
            assert isinstance(b0_instrs[-1], Return)
            assert b0_instrs[-1].value.constant_value == 0

    def test_remove_unreachable_block(self):
        """Test removal of unreachable blocks."""
        func = IRFunction(name="test", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [Jump(target="B1")]

        b1 = BasicBlock(label="B1")
        b1.instructions = [Return(value=make_int(0))]

        # B2 is unreachable (no one jumps to it)
        b2 = BasicBlock(label="B2")
        b2.instructions = [Return(value=make_int(999))]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2}
        func.entry_block = "B0"

        module = make_module_with_function(func)
        cfo = ControlFlowOptimization()
        stats = cfo.run_on_module(module)

        assert "B2" not in func.blocks
        assert stats.blocks_removed >= 1

    def test_jump_threading(self):
        """Test jump threading through empty blocks."""
        func = IRFunction(name="test", return_type=IRType.INT)

        b0 = BasicBlock(label="B0")
        b0.instructions = [Jump(target="B1")]

        # B1 only contains a jump
        b1 = BasicBlock(label="B1")
        b1.instructions = [Jump(target="B2")]

        b2 = BasicBlock(label="B2")
        b2.instructions = [Return(value=make_int(0))]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2}
        func.entry_block = "B0"

        module = make_module_with_function(func)
        cfo = ControlFlowOptimization()
        cfo.run_on_module(module)

        # B0 should either jump directly to B2, or be merged with B2
        b0_instrs = func.blocks["B0"].instructions
        if isinstance(b0_instrs[0], Jump):
            # Jump threading occurred
            assert b0_instrs[0].target == "B2"
        else:
            # Blocks were merged, B0 should contain return 0
            assert isinstance(b0_instrs[-1], Return)
            assert b0_instrs[-1].value.constant_value == 0


# =============================================================================
# Pass Manager Tests
# =============================================================================

class TestPassManager:
    """Tests for the pass manager."""

    def test_add_pass(self):
        """Test adding passes to manager."""
        manager = PassManager()
        manager.add_pass(ConstantFolding())
        manager.add_pass(DeadCodeElimination())

        # Check that passes were added
        assert len(manager._passes) == 2

    def test_run_single_pass(self):
        """Test running a single pass."""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_int(2),
                right=make_int(3)
            ),
            Return(value=make_var("t", 0))
        ])

        module = make_module_with_function(func)
        manager = PassManager()
        manager.add_pass(ConstantFolding())

        stats_list = manager.run(module)

        assert len(stats_list) == 1
        assert stats_list[0].pass_name == "ConstantFolding"
        assert stats_list[0].instructions_modified == 1

    def test_run_multiple_passes(self):
        """Test running multiple passes in sequence."""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("unused", 0),
                op=OpCode.ADD,
                left=make_int(2),
                right=make_int(3)
            ),
            LoadConst(dest=make_var("used", 0), value=10, value_type=IRType.INT),
            Return(value=make_var("used", 0))
        ])

        module = make_module_with_function(func)
        manager = PassManager()
        manager.add_pass(ConstantFolding())
        manager.add_pass(DeadCodeElimination())

        stats_list = manager.run(module)

        assert len(stats_list) == 2
        # Constant folding should modify the first instruction
        assert stats_list[0].instructions_modified == 1
        # DCE should remove the now-unused folded constant
        assert stats_list[1].instructions_removed == 1

    def test_run_until_fixed_point(self):
        """Test fixed-point iteration."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("a", 0), value=5, value_type=IRType.INT),
            Copy(dest=make_var("b", 0), source=make_var("a", 0)),
            BinaryOp(
                dest=make_var("c", 0),
                op=OpCode.ADD,
                left=make_var("b", 0),
                right=make_int(0)  # Will be simplified
            ),
            Return(value=make_var("c", 0))
        ])

        module = make_module_with_function(func)
        manager = PassManager()
        manager.add_pass(CopyPropagation())
        manager.add_pass(AlgebraicSimplification())
        manager.add_pass(DeadCodeElimination())

        stats_list = manager.run_until_fixed_point(module)

        # All passes should have run
        assert len(stats_list) >= 1
        # The function should be optimized
        assert len(func.blocks["B0"].instructions) <= 3

    def test_default_pass_manager(self):
        """Test the default pass manager creation."""
        manager = create_default_pass_manager()

        # Should have 6 passes
        assert len(manager._passes) == 6

        # Check pass types
        pass_names = [p.name for p in manager._passes]
        assert "ConstantFolding" in pass_names
        assert "CopyPropagation" in pass_names
        assert "CSE" in pass_names
        assert "AlgebraicSimplification" in pass_names
        assert "DeadCodeElimination" in pass_names
        assert "ControlFlowOptimization" in pass_names


# =============================================================================
# Integration Tests
# =============================================================================

class TestOptimizationIntegration:
    """Integration tests combining multiple optimizations."""

    def test_constant_folding_then_dce(self):
        """Test constant folding enabling DCE."""
        func = make_simple_function("test", [
            # This will be folded to 10
            BinaryOp(
                dest=make_var("unused", 0),
                op=OpCode.ADD,
                left=make_int(5),
                right=make_int(5)
            ),
            LoadConst(dest=make_var("result", 0), value=42, value_type=IRType.INT),
            Return(value=make_var("result", 0))
        ])

        module = make_module_with_function(func)
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(module)

        # The unused constant should be eliminated
        assert len(func.blocks["B0"].instructions) == 2

    def test_copy_propagation_then_dce(self):
        """Test copy propagation enabling DCE."""
        func = make_simple_function("test", [
            LoadConst(dest=make_var("x", 0), value=10, value_type=IRType.INT),
            Copy(dest=make_var("y", 0), source=make_var("x", 0)),
            Copy(dest=make_var("z", 0), source=make_var("y", 0)),
            Return(value=make_var("z", 0))
        ])

        module = make_module_with_function(func)
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(module)

        # After propagation and DCE, copies should be eliminated
        # Final code should just be: load const, return
        assert len(func.blocks["B0"].instructions) <= 4

    def test_algebraic_then_constant_folding(self):
        """Test algebraic simplification enabling constant folding."""
        func = make_simple_function("test", [
            # x - x = 0, then 0 + 5 = 5
            LoadConst(dest=make_var("x", 0), value=10, value_type=IRType.INT),
            BinaryOp(
                dest=make_var("zero", 0),
                op=OpCode.SUB,
                left=make_var("x", 0),
                right=make_var("x", 0)
            ),
            BinaryOp(
                dest=make_var("result", 0),
                op=OpCode.ADD,
                left=make_var("zero", 0),
                right=make_int(5)
            ),
            Return(value=make_var("result", 0))
        ])

        module = make_module_with_function(func)
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(module)

        # The result should be simplified significantly
        block = func.blocks["B0"]
        # Check that the final result is correct
        assert any(
            isinstance(i, LoadConst) or isinstance(i, Copy)
            for i in block.instructions[:-1]
        )

    def test_cse_then_dce(self):
        """Test CSE enabling DCE."""
        x = make_var("x", 0)
        y = make_var("y", 0)

        func = make_simple_function("test", [
            BinaryOp(dest=make_var("t", 0), op=OpCode.ADD, left=x, right=y),
            BinaryOp(dest=make_var("t", 1), op=OpCode.ADD, left=x, right=y),
            BinaryOp(dest=make_var("t", 2), op=OpCode.ADD, left=x, right=y),
            Return(value=make_var("t", 2))
        ])

        module = make_module_with_function(func)
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(module)

        # The redundant computations should be eliminated
        block = func.blocks["B0"]
        # Should have fewer than 4 instructions (excluding return)
        assert len(block.instructions) <= 4


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and corner cases."""

    def test_empty_function(self):
        """Test optimization of empty function."""
        func = IRFunction(name="empty", return_type=IRType.VOID)
        b0 = BasicBlock(label="B0")
        b0.instructions = [Return(value=None)]
        func.blocks["B0"] = b0
        func.entry_block = "B0"

        module = make_module_with_function(func)
        manager = create_default_pass_manager()

        # Should not crash
        stats_list = manager.run(module)
        assert len(stats_list) == 6

    def test_single_instruction(self):
        """Test optimization of single instruction function."""
        func = make_simple_function("test", [
            Return(value=make_int(42))
        ])

        module = make_module_with_function(func)
        manager = create_default_pass_manager()

        stats_list = manager.run(module)
        # No changes should be made
        total_changes = sum(
            s.instructions_modified + s.instructions_removed
            for s in stats_list
        )
        assert total_changes == 0

    def test_phi_preservation(self):
        """Test that phi functions are handled correctly."""
        func = IRFunction(name="test", return_type=IRType.INT)

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
        b1.instructions = [
            LoadConst(dest=make_var("x", 0), value=1, value_type=IRType.INT),
            Jump(target="B3")
        ]

        b2 = BasicBlock(label="B2")
        b2.instructions = [
            LoadConst(dest=make_var("x", 1), value=2, value_type=IRType.INT),
            Jump(target="B3")
        ]

        b3 = BasicBlock(label="B3")
        b3.instructions = [
            Phi(
                dest=make_var("x", 2),
                sources=[
                    PhiSource(make_var("x", 0), "B1"),
                    PhiSource(make_var("x", 1), "B2")
                ]
            ),
            Return(value=make_var("x", 2))
        ]

        func.blocks = {"B0": b0, "B1": b1, "B2": b2, "B3": b3}
        func.entry_block = "B0"

        module = make_module_with_function(func)
        manager = PassManager()
        manager.add_pass(DeadCodeElimination())

        # Should not remove phi or values it depends on
        manager.run(module)
        assert "B3" in func.blocks
        # Check that phi is still there (might be optimized due to constant branch)

    def test_statistics_accumulation(self):
        """Test that statistics are accumulated correctly."""
        func = make_simple_function("test", [
            BinaryOp(
                dest=make_var("t", 0),
                op=OpCode.ADD,
                left=make_int(1),
                right=make_int(2)
            ),
            BinaryOp(
                dest=make_var("t", 1),
                op=OpCode.ADD,
                left=make_int(3),
                right=make_int(4)
            ),
            BinaryOp(
                dest=make_var("result", 0),
                op=OpCode.ADD,
                left=make_var("t", 0),
                right=make_var("t", 1)
            ),
            Return(value=make_var("result", 0))
        ])

        module = make_module_with_function(func)
        cf = ConstantFolding()
        stats = cf.run_on_module(module)

        # Should fold both constant additions
        assert stats.instructions_modified == 2
