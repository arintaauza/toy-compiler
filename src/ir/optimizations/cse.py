"""
Common Subexpression Elimination (CSE) Optimization Pass for the Toy compiler.

CSE identifies expressions that compute the same value and replaces redundant
computations with the previously computed result.

Examples:
    t1 = a + b       t1 = a + b
    t2 = a + b   ->  t2 = t1       ; reuse t1 instead of recomputing
    t3 = t1 * t2     t3 = t1 * t1

The algorithm:
1. For each instruction, compute a "hash" of the expression
2. If we've seen the same expression before, replace with a copy
3. Otherwise, record this expression for future use

This is a local CSE (within a basic block). Global CSE would require
additional data flow analysis.

Note: We only CSE pure operations (no side effects).
"""

from typing import Dict, Tuple, Optional
from src.ir.instructions import (
    IRFunction,
    BasicBlock,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    IRValue,
    OpCode,
)
from src.ir.optimizations.pass_manager import FunctionPass, PassStatistics


# Expression key: (operation, operand1, operand2) or (operation, operand)
ExpressionKey = Tuple


class CommonSubexpressionElimination(FunctionPass):
    """
    Common subexpression elimination optimization pass.

    Replaces redundant expressions with copies of previously computed values.
    """

    @property
    def name(self) -> str:
        return "CSE"

    def optimize(self, func: IRFunction) -> PassStatistics:
        """
        Run CSE on a function.

        Performs local CSE on each basic block independently.

        Args:
            func: The function to optimize (modified in place)

        Returns:
            Statistics about changes made
        """
        stats = PassStatistics(pass_name=self.name)

        for block in func.blocks.values():
            block_stats = self._optimize_block(block)
            stats.instructions_modified += block_stats.instructions_modified

        return stats

    def _optimize_block(self, block: BasicBlock) -> PassStatistics:
        """
        Run CSE on a single basic block.

        Args:
            block: The block to optimize

        Returns:
            Statistics about changes made
        """
        stats = PassStatistics(pass_name=self.name)

        # Maps expression keys to the value that computed them
        available: Dict[ExpressionKey, IRValue] = {}

        for i, instr in enumerate(block.instructions):
            key = self._get_expression_key(instr)

            if key is not None:
                if key in available:
                    # We've seen this expression before!
                    # Replace with a copy
                    original_value = available[key]
                    block.instructions[i] = Copy(
                        dest=instr.get_def(),
                        source=original_value
                    )
                    stats.instructions_modified += 1
                else:
                    # Record this expression
                    defined = instr.get_def()
                    if defined is not None:
                        available[key] = defined

        return stats

    def _get_expression_key(self, instr: IRInstruction) -> Optional[ExpressionKey]:
        """
        Get a hashable key representing the expression computed by an instruction.

        Args:
            instr: The instruction to get a key for

        Returns:
            A tuple representing the expression, or None if not applicable
        """
        if isinstance(instr, BinaryOp):
            return self._binary_key(instr)
        elif isinstance(instr, UnaryOp):
            return self._unary_key(instr)
        elif isinstance(instr, LoadConst):
            return self._const_key(instr)

        return None

    def _binary_key(self, instr: BinaryOp) -> ExpressionKey:
        """
        Get expression key for a binary operation.

        For commutative operations (add, mul, etc.), we normalize
        the operand order to increase CSE opportunities.
        """
        op = instr.op
        left = self._value_key(instr.left)
        right = self._value_key(instr.right)

        # For commutative operations, sort operands for consistent key
        if self._is_commutative(op):
            if left > right:
                left, right = right, left

        return ("binary", op, left, right)

    def _unary_key(self, instr: UnaryOp) -> ExpressionKey:
        """Get expression key for a unary operation."""
        return ("unary", instr.op, self._value_key(instr.operand))

    def _const_key(self, instr: LoadConst) -> ExpressionKey:
        """Get expression key for a constant load."""
        return ("const", instr.value_type, instr.value)

    def _value_key(self, value: IRValue) -> Tuple:
        """
        Get a hashable key for an IRValue.

        For constants, use the constant value.
        For variables, use (name, version).
        """
        if value.is_constant:
            return ("const", value.ir_type, value.constant_value)
        return ("var", value.name, value.version)

    def _is_commutative(self, op: OpCode) -> bool:
        """Check if an operation is commutative."""
        return op in {
            OpCode.ADD,
            OpCode.MUL,
            OpCode.EQ,
            OpCode.NE,
            OpCode.AND,
            OpCode.OR,
        }
