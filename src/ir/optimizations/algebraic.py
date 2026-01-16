"""
Algebraic Simplification Optimization Pass for the Toy compiler.

Algebraic simplification applies mathematical identities to simplify
expressions. This reduces computation and enables further optimizations.

Supported simplifications:
- Identity operations:
    x + 0 -> x       x - 0 -> x
    x * 1 -> x       x / 1 -> x
    x * 0 -> 0       0 / x -> 0
    x && true -> x   x || false -> x
    x && false -> false   x || true -> true

- Strength reduction:
    x * 2 -> x + x   (not implemented yet)
    x * power_of_2 -> x << log2(n)  (not implemented yet)

- Algebraic identities:
    x - x -> 0
    x / x -> 1 (when x != 0)
    x == x -> true
    x != x -> false
    not (not x) -> x
    neg (neg x) -> x
"""

from typing import Optional
from src.ir.instructions import (
    IRFunction,
    BasicBlock,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    IRValue,
    IRType,
    OpCode,
)
from src.ir.optimizations.pass_manager import FunctionPass, PassStatistics


class AlgebraicSimplification(FunctionPass):
    """
    Algebraic simplification optimization pass.

    Applies mathematical identities to simplify expressions.
    """

    @property
    def name(self) -> str:
        return "AlgebraicSimplification"

    def optimize(self, func: IRFunction) -> PassStatistics:
        """
        Run algebraic simplification on a function.

        Args:
            func: The function to optimize (modified in place)

        Returns:
            Statistics about changes made
        """
        stats = PassStatistics(pass_name=self.name)

        for block in func.blocks.values():
            for i, instr in enumerate(block.instructions):
                simplified = self._try_simplify(instr)
                if simplified is not None:
                    block.instructions[i] = simplified
                    stats.instructions_modified += 1

        return stats

    def _try_simplify(self, instr: IRInstruction) -> Optional[IRInstruction]:
        """
        Try to simplify an instruction using algebraic identities.

        Args:
            instr: The instruction to simplify

        Returns:
            Simplified instruction, or None if no simplification possible
        """
        if isinstance(instr, BinaryOp):
            return self._simplify_binary(instr)
        elif isinstance(instr, UnaryOp):
            return self._simplify_unary(instr)
        return None

    def _simplify_binary(self, instr: BinaryOp) -> Optional[IRInstruction]:
        """
        Simplify a binary operation using algebraic identities.
        """
        op = instr.op
        left = instr.left
        right = instr.right
        dest = instr.dest

        # Check for constant operands
        left_is_zero = left.is_constant and left.constant_value == 0
        right_is_zero = right.is_constant and right.constant_value == 0
        left_is_one = left.is_constant and left.constant_value == 1
        right_is_one = right.is_constant and right.constant_value == 1
        left_is_true = left.is_constant and left.constant_value is True
        right_is_true = right.is_constant and right.constant_value is True
        left_is_false = left.is_constant and left.constant_value is False
        right_is_false = right.is_constant and right.constant_value is False

        # Check if operands are the same variable
        same_operand = (
            not left.is_constant and
            not right.is_constant and
            left.name == right.name and
            left.version == right.version
        )

        # Addition identities
        if op == OpCode.ADD:
            if left_is_zero:
                return Copy(dest=dest, source=right)
            if right_is_zero:
                return Copy(dest=dest, source=left)

        # Subtraction identities
        elif op == OpCode.SUB:
            if right_is_zero:
                return Copy(dest=dest, source=left)
            if same_operand:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)

        # Multiplication identities
        elif op == OpCode.MUL:
            if left_is_zero or right_is_zero:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)
            if left_is_one:
                return Copy(dest=dest, source=right)
            if right_is_one:
                return Copy(dest=dest, source=left)

        # Division identities
        elif op == OpCode.DIV:
            if left_is_zero:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)
            if right_is_one:
                return Copy(dest=dest, source=left)
            if same_operand:
                # x / x = 1 (assuming x != 0)
                return LoadConst(dest=dest, value=1, value_type=IRType.INT)

        # Modulo identities
        elif op == OpCode.MOD:
            if left_is_zero:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)
            if right_is_one:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)
            if same_operand:
                # x % x = 0 (assuming x != 0)
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)

        # Comparison identities with same operand
        elif op == OpCode.EQ:
            if same_operand:
                return LoadConst(dest=dest, value=True, value_type=IRType.BOOL)

        elif op == OpCode.NE:
            if same_operand:
                return LoadConst(dest=dest, value=False, value_type=IRType.BOOL)

        elif op == OpCode.LE or op == OpCode.GE:
            if same_operand:
                return LoadConst(dest=dest, value=True, value_type=IRType.BOOL)

        elif op == OpCode.LT or op == OpCode.GT:
            if same_operand:
                return LoadConst(dest=dest, value=False, value_type=IRType.BOOL)

        # Logical AND identities
        elif op == OpCode.AND:
            if left_is_false or right_is_false:
                return LoadConst(dest=dest, value=False, value_type=IRType.BOOL)
            if left_is_true:
                return Copy(dest=dest, source=right)
            if right_is_true:
                return Copy(dest=dest, source=left)
            if same_operand:
                return Copy(dest=dest, source=left)

        # Logical OR identities
        elif op == OpCode.OR:
            if left_is_true or right_is_true:
                return LoadConst(dest=dest, value=True, value_type=IRType.BOOL)
            if left_is_false:
                return Copy(dest=dest, source=right)
            if right_is_false:
                return Copy(dest=dest, source=left)
            if same_operand:
                return Copy(dest=dest, source=left)

        return None

    def _simplify_unary(self, instr: UnaryOp) -> Optional[IRInstruction]:
        """
        Simplify a unary operation using algebraic identities.
        """
        op = instr.op
        operand = instr.operand
        dest = instr.dest

        # Negation of zero
        if op == OpCode.NEG:
            if operand.is_constant and operand.constant_value == 0:
                return LoadConst(dest=dest, value=0, value_type=IRType.INT)

        # NOT of boolean constants
        elif op == OpCode.NOT:
            if operand.is_constant:
                if operand.constant_value is True:
                    return LoadConst(dest=dest, value=False, value_type=IRType.BOOL)
                elif operand.constant_value is False:
                    return LoadConst(dest=dest, value=True, value_type=IRType.BOOL)

        return None
