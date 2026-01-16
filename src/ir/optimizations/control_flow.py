"""
Control Flow Optimization Pass for the Toy compiler.

This pass performs several control flow optimizations:

1. Branch simplification: Convert branches with constant conditions to jumps
   branch true, L1, L2  -> jump L1
   branch false, L1, L2 -> jump L2

2. Empty block elimination: Remove blocks that only contain a jump
   B1: jump B2  -> redirect all jumps to B1 to go directly to B2

3. Unreachable code elimination: Remove blocks with no predecessors
   (except entry block)

4. Jump threading: When a block ends with a jump to a block that only
   contains a jump, go directly to the final target

5. Block merging: Merge a block with its unique successor if the
   successor has only that block as predecessor
"""

from typing import Set, List, Dict
from src.ir.instructions import (
    IRModule,
    IRFunction,
    BasicBlock,
    IRInstruction,
    Jump,
    Branch,
    Return,
    Phi,
    PhiSource,
    IRValue,
    IRType,
)
from src.ir.optimizations.pass_manager import FunctionPass, PassStatistics


class ControlFlowOptimization(FunctionPass):
    """
    Control flow optimization pass.

    Simplifies the control flow graph by eliminating redundant branches,
    empty blocks, and unreachable code.
    """

    @property
    def name(self) -> str:
        return "ControlFlowOptimization"

    def optimize(self, func: IRFunction) -> PassStatistics:
        """
        Run control flow optimizations on a function.

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

            # 1. Branch simplification
            branch_stats = self._simplify_branches(func)
            if branch_stats.instructions_modified > 0:
                changed = True
                stats.instructions_modified += branch_stats.instructions_modified

            # 2. Jump threading
            thread_stats = self._thread_jumps(func)
            if thread_stats.instructions_modified > 0:
                changed = True
                stats.instructions_modified += thread_stats.instructions_modified

            # 3. Remove unreachable blocks
            removed = self._remove_unreachable(func)
            if removed > 0:
                changed = True
                stats.blocks_removed += removed

            # 4. Merge blocks
            merged = self._merge_blocks(func)
            if merged > 0:
                changed = True
                stats.blocks_removed += merged

        # Rebuild predecessor/successor info
        self._rebuild_cfg(func)

        return stats

    def _simplify_branches(self, func: IRFunction) -> PassStatistics:
        """
        Simplify branches with constant conditions.

        branch true, L1, L2  -> jump L1
        branch false, L1, L2 -> jump L2
        """
        stats = PassStatistics(pass_name=self.name)

        for block in func.blocks.values():
            if not block.instructions:
                continue

            terminator = block.get_terminator()
            if isinstance(terminator, Branch):
                cond = terminator.condition

                if cond.is_constant:
                    # Replace branch with jump
                    if cond.constant_value:
                        new_target = terminator.true_target
                    else:
                        new_target = terminator.false_target

                    # Replace the branch with a jump
                    block.instructions[-1] = Jump(target=new_target)
                    stats.instructions_modified += 1

        return stats

    def _thread_jumps(self, func: IRFunction) -> PassStatistics:
        """
        Thread jumps through empty blocks.

        If B1 jumps to B2, and B2 only contains a jump to B3,
        make B1 jump directly to B3.
        """
        stats = PassStatistics(pass_name=self.name)

        # Build map of blocks that are just jumps (no other instructions)
        jump_only: Dict[str, str] = {}
        for label, block in func.blocks.items():
            if (len(block.instructions) == 1 and
                isinstance(block.instructions[0], Jump)):
                jump_only[label] = block.instructions[0].target

        # Thread through jump-only blocks
        for block in func.blocks.values():
            if not block.instructions:
                continue

            terminator = block.get_terminator()

            if isinstance(terminator, Jump):
                final_target = self._follow_jumps(terminator.target, jump_only)
                if final_target != terminator.target:
                    block.instructions[-1] = Jump(target=final_target)
                    stats.instructions_modified += 1

            elif isinstance(terminator, Branch):
                true_final = self._follow_jumps(terminator.true_target, jump_only)
                false_final = self._follow_jumps(terminator.false_target, jump_only)

                if (true_final != terminator.true_target or
                    false_final != terminator.false_target):
                    block.instructions[-1] = Branch(
                        condition=terminator.condition,
                        true_target=true_final,
                        false_target=false_final
                    )
                    stats.instructions_modified += 1

        return stats

    def _follow_jumps(self, target: str, jump_only: Dict[str, str]) -> str:
        """Follow a chain of jump-only blocks to the final target."""
        visited: Set[str] = set()
        current = target

        while current in jump_only and current not in visited:
            visited.add(current)
            current = jump_only[current]

        return current

    def _remove_unreachable(self, func: IRFunction) -> int:
        """
        Remove blocks that are not reachable from the entry block.

        Returns the number of blocks removed.
        """
        # Find all reachable blocks via BFS
        reachable: Set[str] = set()
        worklist = [func.entry_block]

        while worklist:
            label = worklist.pop()
            if label in reachable:
                continue
            if label not in func.blocks:
                continue

            reachable.add(label)
            block = func.blocks[label]

            terminator = block.get_terminator()
            if isinstance(terminator, Jump):
                worklist.append(terminator.target)
            elif isinstance(terminator, Branch):
                worklist.append(terminator.true_target)
                worklist.append(terminator.false_target)

        # Remove unreachable blocks
        unreachable = set(func.blocks.keys()) - reachable
        for label in unreachable:
            del func.blocks[label]

        return len(unreachable)

    def _merge_blocks(self, func: IRFunction) -> int:
        """
        Merge a block with its unique successor if:
        - The block ends with an unconditional jump
        - The successor has exactly one predecessor (this block)
        - The successor is not the entry block

        Returns the number of blocks removed.
        """
        merged_count = 0

        # Rebuild predecessor info first
        self._rebuild_cfg(func)

        # Find merge candidates
        to_merge: List[tuple] = []

        for label, block in func.blocks.items():
            if not block.instructions:
                continue

            terminator = block.get_terminator()
            if not isinstance(terminator, Jump):
                continue

            successor_label = terminator.target
            if successor_label not in func.blocks:
                continue

            successor = func.blocks[successor_label]

            # Check if successor has exactly one predecessor
            if (len(successor.predecessors) == 1 and
                successor.predecessors[0] == label and
                successor_label != func.entry_block):
                to_merge.append((label, successor_label))

        # Perform merges
        for pred_label, succ_label in to_merge:
            if pred_label not in func.blocks or succ_label not in func.blocks:
                continue

            pred_block = func.blocks[pred_label]
            succ_block = func.blocks[succ_label]

            # Remove the jump from predecessor
            pred_block.instructions.pop()

            # Skip phi functions in successor (they become invalid after merge)
            succ_instructions = [
                instr for instr in succ_block.instructions
                if not isinstance(instr, Phi)
            ]

            # Append successor's instructions to predecessor
            pred_block.instructions.extend(succ_instructions)

            # Update any references to the successor block
            self._update_references(func, succ_label, pred_label)

            # Remove the successor block
            del func.blocks[succ_label]
            merged_count += 1

        return merged_count

    def _update_references(self, func: IRFunction, old_label: str, new_label: str):
        """
        Update all references from old_label to new_label.

        This updates:
        - Jump targets
        - Branch targets
        - Phi sources
        """
        for block in func.blocks.values():
            # Update terminator
            if block.instructions:
                terminator = block.get_terminator()

                if isinstance(terminator, Jump):
                    if terminator.target == old_label:
                        block.instructions[-1] = Jump(target=new_label)

                elif isinstance(terminator, Branch):
                    true_target = terminator.true_target
                    false_target = terminator.false_target

                    if true_target == old_label:
                        true_target = new_label
                    if false_target == old_label:
                        false_target = new_label

                    if (true_target != terminator.true_target or
                        false_target != terminator.false_target):
                        block.instructions[-1] = Branch(
                            condition=terminator.condition,
                            true_target=true_target,
                            false_target=false_target
                        )

            # Update phi sources
            for i, instr in enumerate(block.instructions):
                if isinstance(instr, Phi):
                    new_sources = []
                    for source in instr.sources:
                        if source.block == old_label:
                            new_sources.append(PhiSource(source.value, new_label))
                        else:
                            new_sources.append(source)
                    block.instructions[i] = Phi(dest=instr.dest, sources=new_sources)

    def _rebuild_cfg(self, func: IRFunction):
        """
        Rebuild the predecessor/successor information for all blocks.
        """
        # Clear existing info
        for block in func.blocks.values():
            block.predecessors.clear()
            block.successors.clear()

        # Rebuild from terminators
        for label, block in func.blocks.items():
            terminator = block.get_terminator()

            if isinstance(terminator, Jump):
                block.successors.append(terminator.target)
                if terminator.target in func.blocks:
                    func.blocks[terminator.target].predecessors.append(label)

            elif isinstance(terminator, Branch):
                block.successors.append(terminator.true_target)
                block.successors.append(terminator.false_target)

                if terminator.true_target in func.blocks:
                    func.blocks[terminator.true_target].predecessors.append(label)
                if terminator.false_target in func.blocks:
                    func.blocks[terminator.false_target].predecessors.append(label)
