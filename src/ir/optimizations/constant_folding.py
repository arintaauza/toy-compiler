"""
Constant Folding Optimization Pass for the Toy compiler.

Constant folding evaluates expressions with constant operands at compile time,
replacing them with the computed result. This reduces runtime computation.

Examples:
    x = 2 + 3        -> x = 5
    y = 10 * 4       -> y = 40
    z = true && false -> z = false
    w = 5 > 3        -> w = true

The pass handles:
- Arithmetic operations (+, -, *, /, %)
- Comparison operations (<, >, <=, >=, ==, !=)
- Logical operations (and, or, not)
- Unary operations (negation)
"""

from typing import Optional, Any
from src.ir.instructions import (
    IRFunction,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    LoadConst,
    IRValue,
    IRType,
    OpCode,
    make_constant,
)
from src.ir.optimizations.pass_manager import FunctionPass, PassStatistics


class ConstantFolding(FunctionPass):
    """
    Constant folding optimization pass.

    Evaluates operations with constant operands at compile time.
    """

    @property
    def name(self) -> str:
        return "ConstantFolding"

    def optimize(self, func: IRFunction) -> PassStatistics:
        """
        Run constant folding on a function.

        Args:
            func: The function to optimize (modified in place)

        Returns:
            Statistics about changes made
        """
        stats = PassStatistics(pass_name=self.name)

        for block in func.blocks.values():
            i = 0
            while i < len(block.instructions):
                instr = block.instructions[i]
                folded = self._try_fold(instr)

                if folded is not None:
                    # Replace with LoadConst
                    block.instructions[i] = folded
                    stats.instructions_modified += 1

                i += 1

        return stats

    def _try_fold(self, instr: IRInstruction) -> Optional[LoadConst]:
        """
        Try to fold a constant expression.

        Args:
            instr: The instruction to potentially fold

        Returns:
            A LoadConst instruction if folding succeeded, None otherwise
        """
        if isinstance(instr, BinaryOp):
            return self._fold_binary(instr)
        elif isinstance(instr, UnaryOp):
            return self._fold_unary(instr)
        return None

    def _fold_binary(self, instr: BinaryOp) -> Optional[LoadConst]:
        """
        Fold a binary operation with constant operands.

        Args:
            instr: The binary operation to fold

        Returns:
            LoadConst if both operands are constants, None otherwise
        """
        left = instr.left
        right = instr.right

        # Both operands must be constants
        if not (left.is_constant and right.is_constant):
            return None

        left_val = left.constant_value
        right_val = right.constant_value
        op = instr.op

        result = None
        result_type = IRType.INT

        try:
            # Arithmetic operations
            if op == OpCode.ADD:
                result = left_val + right_val
                result_type = self._result_type(left.ir_type, right.ir_type)
            elif op == OpCode.SUB:
                result = left_val - right_val
                result_type = self._result_type(left.ir_type, right.ir_type)
            elif op == OpCode.MUL:
                result = left_val * right_val
                result_type = self._result_type(left.ir_type, right.ir_type)
            elif op == OpCode.DIV:
                if right_val == 0:
                    return None  # Don't fold division by zero
                if left.ir_type == IRType.INT and right.ir_type == IRType.INT:
                    result = left_val // right_val  # Integer division
                else:
                    result = left_val / right_val
                result_type = self._result_type(left.ir_type, right.ir_type)
            elif op == OpCode.MOD:
                if right_val == 0:
                    return None  # Don't fold modulo by zero
                result = left_val % right_val
                result_type = IRType.INT

            # Comparison operations (result is always bool)
            elif op == OpCode.LT:
                result = left_val < right_val
                result_type = IRType.BOOL
            elif op == OpCode.GT:
                result = left_val > right_val
                result_type = IRType.BOOL
            elif op == OpCode.LE:
                result = left_val <= right_val
                result_type = IRType.BOOL
            elif op == OpCode.GE:
                result = left_val >= right_val
                result_type = IRType.BOOL
            elif op == OpCode.EQ:
                result = left_val == right_val
                result_type = IRType.BOOL
            elif op == OpCode.NE:
                result = left_val != right_val
                result_type = IRType.BOOL

            # Logical operations (for booleans)
            elif op == OpCode.AND:
                result = left_val and right_val
                result_type = IRType.BOOL
            elif op == OpCode.OR:
                result = left_val or right_val
                result_type = IRType.BOOL

        except (TypeError, ValueError, ZeroDivisionError):
            return None

        if result is not None:
            return LoadConst(
                dest=instr.dest,
                value=result,
                value_type=result_type
            )

        return None

    def _fold_unary(self, instr: UnaryOp) -> Optional[LoadConst]:
        """
        Fold a unary operation with constant operand.

        Args:
            instr: The unary operation to fold

        Returns:
            LoadConst if operand is constant, None otherwise
        """
        operand = instr.operand

        if not operand.is_constant:
            return None

        val = operand.constant_value
        op = instr.op

        result = None
        result_type = operand.ir_type

        try:
            if op == OpCode.NEG:
                result = -val
            elif op == OpCode.NOT:
                result = not val
                result_type = IRType.BOOL
        except (TypeError, ValueError):
            return None

        if result is not None:
            return LoadConst(
                dest=instr.dest,
                value=result,
                value_type=result_type
            )

        return None

    def _result_type(self, left_type: IRType, right_type: IRType) -> IRType:
        """
        Determine the result type of a binary operation.

        Float + anything = Float
        Otherwise INT
        """
        if left_type == IRType.FLOAT or right_type == IRType.FLOAT:
            return IRType.FLOAT
        return IRType.INT
