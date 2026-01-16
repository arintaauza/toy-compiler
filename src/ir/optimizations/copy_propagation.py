"""
Copy Propagation Optimization Pass for the Luna compiler.

Copy propagation replaces uses of a variable with its source when the
variable is just a copy. This enables further optimizations and reduces
register pressure.

Examples:
    y = x           y = x
    z = y + 1   ->  z = x + 1     ; replace y with x

After copy propagation, DCE can often remove the now-unused copy.

The algorithm:
1. Find all copy instructions (dest = source)
2. For each use of the copy's destination, replace with the source
3. Iterate until no more changes

This is a local optimization (within basic blocks). We're careful about:
- Not propagating past redefinitions of the source
- Handling phi functions specially
"""

from typing import Dict, Optional, List, Tuple
from src.ir.instructions import (
    IRFunction,
    BasicBlock,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Branch,
    Return,
    Call,
    Phi,
    PhiSource,
    IRValue,
)
from src.ir.optimizations.pass_manager import FunctionPass, PassStatistics


class CopyPropagation(FunctionPass):
    """
    Copy propagation optimization pass.

    Replaces uses of copied values with their sources.
    """

    @property
    def name(self) -> str:
        return "CopyPropagation"

    def optimize(self, func: IRFunction) -> PassStatistics:
        """
        Run copy propagation on a function.

        Args:
            func: The function to optimize (modified in place)

        Returns:
            Statistics about changes made
        """
        stats = PassStatistics(pass_name=self.name)

        # Iterate until no more changes
        changed = True
        while changed:
            changed = False

            for block in func.blocks.values():
                # Build copy map for this block
                # Maps dest -> source for all copies
                copy_map: Dict[Tuple[str, int], IRValue] = {}

                for i, instr in enumerate(block.instructions):
                    # First, propagate copies into this instruction
                    new_instr, propagated = self._propagate_in_instruction(
                        instr, copy_map
                    )
                    if propagated:
                        block.instructions[i] = new_instr
                        stats.instructions_modified += 1
                        changed = True
                        instr = new_instr

                    # Then, if this is a copy, record it
                    if isinstance(instr, Copy):
                        dest = instr.dest
                        source = instr.source
                        if not dest.is_constant:
                            key = (dest.name, dest.version)
                            copy_map[key] = source

                    # If this instruction defines a value, it might invalidate
                    # a previous copy if it redefines the source
                    defined = instr.get_def()
                    if defined is not None and not defined.is_constant:
                        # Remove any copies whose source is now redefined
                        key_to_remove = (defined.name, defined.version)
                        to_remove = []
                        for dest_key, src in copy_map.items():
                            if not src.is_constant:
                                src_key = (src.name, src.version)
                                if src_key == key_to_remove:
                                    to_remove.append(dest_key)
                        for k in to_remove:
                            del copy_map[k]

        return stats

    def _propagate_in_instruction(
        self,
        instr: IRInstruction,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[IRInstruction, bool]:
        """
        Propagate copies into an instruction.

        Args:
            instr: The instruction to transform
            copy_map: Map from copied destination to source

        Returns:
            Tuple of (new_instruction, was_changed)
        """
        if isinstance(instr, BinaryOp):
            return self._propagate_binary(instr, copy_map)
        elif isinstance(instr, UnaryOp):
            return self._propagate_unary(instr, copy_map)
        elif isinstance(instr, Copy):
            return self._propagate_copy(instr, copy_map)
        elif isinstance(instr, Branch):
            return self._propagate_branch(instr, copy_map)
        elif isinstance(instr, Return):
            return self._propagate_return(instr, copy_map)
        elif isinstance(instr, Call):
            return self._propagate_call(instr, copy_map)
        elif isinstance(instr, Phi):
            return self._propagate_phi(instr, copy_map)

        return instr, False

    def _lookup(
        self,
        value: IRValue,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[IRValue, bool]:
        """
        Look up a value in the copy map.

        Returns the source if it's a copy, otherwise the original value.
        Also returns True if a substitution was made.
        """
        if value.is_constant:
            return value, False

        key = (value.name, value.version)
        if key in copy_map:
            return copy_map[key], True

        return value, False

    def _propagate_binary(
        self,
        instr: BinaryOp,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[BinaryOp, bool]:
        """Propagate copies into a binary operation."""
        new_left, left_changed = self._lookup(instr.left, copy_map)
        new_right, right_changed = self._lookup(instr.right, copy_map)

        if left_changed or right_changed:
            return BinaryOp(
                dest=instr.dest,
                op=instr.op,
                left=new_left,
                right=new_right
            ), True

        return instr, False

    def _propagate_unary(
        self,
        instr: UnaryOp,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[UnaryOp, bool]:
        """Propagate copies into a unary operation."""
        new_operand, changed = self._lookup(instr.operand, copy_map)

        if changed:
            return UnaryOp(
                dest=instr.dest,
                op=instr.op,
                operand=new_operand
            ), True

        return instr, False

    def _propagate_copy(
        self,
        instr: Copy,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[Copy, bool]:
        """Propagate copies into a copy instruction."""
        new_source, changed = self._lookup(instr.source, copy_map)

        if changed:
            return Copy(
                dest=instr.dest,
                source=new_source
            ), True

        return instr, False

    def _propagate_branch(
        self,
        instr: Branch,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[Branch, bool]:
        """Propagate copies into a branch instruction."""
        new_cond, changed = self._lookup(instr.condition, copy_map)

        if changed:
            return Branch(
                condition=new_cond,
                true_target=instr.true_target,
                false_target=instr.false_target
            ), True

        return instr, False

    def _propagate_return(
        self,
        instr: Return,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[Return, bool]:
        """Propagate copies into a return instruction."""
        if instr.value is None:
            return instr, False

        new_value, changed = self._lookup(instr.value, copy_map)

        if changed:
            return Return(value=new_value), True

        return instr, False

    def _propagate_call(
        self,
        instr: Call,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[Call, bool]:
        """Propagate copies into a call instruction."""
        new_args = []
        any_changed = False

        for arg in instr.arguments:
            new_arg, changed = self._lookup(arg, copy_map)
            new_args.append(new_arg)
            if changed:
                any_changed = True

        if any_changed:
            return Call(
                dest=instr.dest,
                function=instr.function,
                arguments=new_args
            ), True

        return instr, False

    def _propagate_phi(
        self,
        instr: Phi,
        copy_map: Dict[Tuple[str, int], IRValue]
    ) -> Tuple[Phi, bool]:
        """
        Propagate copies into a phi instruction.

        Note: We need to be careful here because phi sources come from
        different blocks, so our local copy_map might not be valid.
        For now, we skip phi propagation in local copy propagation.
        """
        # Skip phi propagation in local analysis
        return instr, False
