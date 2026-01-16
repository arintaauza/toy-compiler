"""
Optimization Pass Manager for the Luna compiler.

The pass manager orchestrates running optimization passes on IR.
It supports:
- Running individual passes
- Running passes until fixed point (no more changes)
- Collecting statistics on optimizations applied
- Pass ordering and dependencies

Usage:
    manager = PassManager()
    manager.add_pass(ConstantFolding())
    manager.add_pass(DeadCodeElimination())
    optimized_module = manager.run(module)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
from dataclasses import dataclass, field
import copy

from src.ir.instructions import (
    IRModule,
    IRFunction,
    BasicBlock,
    IRInstruction,
)


@dataclass
class PassStatistics:
    """Statistics collected during optimization."""
    pass_name: str
    instructions_removed: int = 0
    instructions_modified: int = 0
    instructions_added: int = 0
    blocks_removed: int = 0
    iterations: int = 0

    def __str__(self) -> str:
        return (
            f"{self.pass_name}: "
            f"removed={self.instructions_removed}, "
            f"modified={self.instructions_modified}, "
            f"added={self.instructions_added}"
        )

    def any_changes(self) -> bool:
        """Check if any changes were made."""
        return (
            self.instructions_removed > 0 or
            self.instructions_modified > 0 or
            self.instructions_added > 0 or
            self.blocks_removed > 0
        )


class OptimizationPass(ABC):
    """
    Abstract base class for optimization passes.

    Each pass implements a specific optimization that transforms
    the IR to improve performance or reduce code size.

    Subclasses must implement:
    - name: Property returning the pass name
    - run_on_function: Method to optimize a single function
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this optimization pass."""
        pass

    @abstractmethod
    def run_on_function(self, func: IRFunction) -> PassStatistics:
        """
        Run the optimization on a single function.

        Args:
            func: The function to optimize (modified in place)

        Returns:
            Statistics about changes made
        """
        pass

    def run_on_module(self, module: IRModule) -> PassStatistics:
        """
        Run the optimization on an entire module.

        Default implementation runs on each function.

        Args:
            module: The module to optimize

        Returns:
            Combined statistics
        """
        total_stats = PassStatistics(pass_name=self.name)

        for func in module.functions.values():
            stats = self.run_on_function(func)
            total_stats.instructions_removed += stats.instructions_removed
            total_stats.instructions_modified += stats.instructions_modified
            total_stats.instructions_added += stats.instructions_added
            total_stats.blocks_removed += stats.blocks_removed

        return total_stats


class FunctionPass(OptimizationPass):
    """
    Base class for passes that operate on individual functions.

    Provides helper methods for common operations like:
    - Iterating over instructions
    - Replacing instructions
    - Removing dead instructions
    """

    def run_on_function(self, func: IRFunction) -> PassStatistics:
        """Run the pass on a function."""
        return self.optimize(func)

    @abstractmethod
    def optimize(self, func: IRFunction) -> PassStatistics:
        """Implement the optimization logic."""
        pass

    def iterate_instructions(self, func: IRFunction):
        """
        Yield (block, index, instruction) for all instructions.

        Useful for passes that need to examine every instruction.
        """
        for block in func.blocks.values():
            for i, instr in enumerate(block.instructions):
                yield block, i, instr

    def replace_instruction(
        self,
        block: BasicBlock,
        index: int,
        new_instr: IRInstruction
    ) -> None:
        """Replace an instruction at the given index."""
        block.instructions[index] = new_instr

    def remove_instruction(self, block: BasicBlock, index: int) -> None:
        """Remove an instruction at the given index."""
        del block.instructions[index]


class BlockPass(OptimizationPass):
    """
    Base class for passes that operate on individual basic blocks.

    Useful for local optimizations that don't need global information.
    """

    def run_on_function(self, func: IRFunction) -> PassStatistics:
        """Run the pass on each block in the function."""
        total_stats = PassStatistics(pass_name=self.name)

        for block in func.blocks.values():
            stats = self.optimize_block(block)
            total_stats.instructions_removed += stats.instructions_removed
            total_stats.instructions_modified += stats.instructions_modified
            total_stats.instructions_added += stats.instructions_added

        return total_stats

    @abstractmethod
    def optimize_block(self, block: BasicBlock) -> PassStatistics:
        """Implement the optimization logic for a single block."""
        pass


class PassManager:
    """
    Manages and runs optimization passes.

    The pass manager:
    - Maintains a list of passes to run
    - Runs passes in order
    - Supports fixed-point iteration (run until no changes)
    - Collects statistics from all passes

    Usage:
        manager = PassManager()
        manager.add_pass(ConstantFolding())
        manager.add_pass(DeadCodeElimination())

        # Run once
        stats = manager.run(module)

        # Or run until fixed point
        stats = manager.run_until_fixed_point(module)
    """

    def __init__(self):
        """Initialize the pass manager."""
        self._passes: List[OptimizationPass] = []
        self._statistics: List[PassStatistics] = []
        self._verbose: bool = False

    def add_pass(self, pass_: OptimizationPass) -> 'PassManager':
        """
        Add an optimization pass to the manager.

        Args:
            pass_: The pass to add

        Returns:
            self for chaining
        """
        self._passes.append(pass_)
        return self

    def set_verbose(self, verbose: bool) -> 'PassManager':
        """Enable/disable verbose output."""
        self._verbose = verbose
        return self

    def run(self, module: IRModule) -> List[PassStatistics]:
        """
        Run all passes once on the module.

        Args:
            module: The module to optimize (modified in place)

        Returns:
            Statistics from each pass
        """
        self._statistics = []

        for pass_ in self._passes:
            stats = pass_.run_on_module(module)
            self._statistics.append(stats)

            if self._verbose and stats.any_changes():
                print(f"  {stats}")

        return self._statistics

    def run_until_fixed_point(
        self,
        module: IRModule,
        max_iterations: int = 10
    ) -> List[PassStatistics]:
        """
        Run all passes repeatedly until no changes are made.

        This allows passes to enable each other's optimizations.
        For example, constant folding might create dead code that
        DCE can remove.

        Args:
            module: The module to optimize
            max_iterations: Maximum number of iterations

        Returns:
            Combined statistics from all iterations
        """
        total_stats: Dict[str, PassStatistics] = {}
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            any_changes = False

            if self._verbose:
                print(f"Optimization iteration {iteration}:")

            stats_list = self.run(module)

            for stats in stats_list:
                if stats.any_changes():
                    any_changes = True

                # Accumulate statistics
                if stats.pass_name not in total_stats:
                    total_stats[stats.pass_name] = PassStatistics(
                        pass_name=stats.pass_name
                    )

                total_stats[stats.pass_name].instructions_removed += stats.instructions_removed
                total_stats[stats.pass_name].instructions_modified += stats.instructions_modified
                total_stats[stats.pass_name].instructions_added += stats.instructions_added
                total_stats[stats.pass_name].blocks_removed += stats.blocks_removed

            if not any_changes:
                if self._verbose:
                    print(f"Fixed point reached after {iteration} iterations")
                break

        # Set iteration count
        for stats in total_stats.values():
            stats.iterations = iteration

        return list(total_stats.values())

    def get_statistics(self) -> List[PassStatistics]:
        """Get statistics from the last run."""
        return self._statistics

    def clear_passes(self) -> None:
        """Remove all registered passes."""
        self._passes.clear()
        self._statistics.clear()


def create_default_pass_manager() -> PassManager:
    """
    Create a pass manager with the standard optimization pipeline.

    The default pipeline includes:
    1. Constant folding (evaluate constant expressions)
    2. Copy propagation (simplify copies)
    3. Common subexpression elimination
    4. Algebraic simplification
    5. Dead code elimination (clean up)
    6. Control flow optimization

    Returns:
        Configured PassManager
    """
    from src.ir.optimizations.constant_folding import ConstantFolding
    from src.ir.optimizations.copy_propagation import CopyPropagation
    from src.ir.optimizations.cse import CommonSubexpressionElimination
    from src.ir.optimizations.algebraic import AlgebraicSimplification
    from src.ir.optimizations.dead_code_elimination import DeadCodeElimination
    from src.ir.optimizations.control_flow import ControlFlowOptimization

    manager = PassManager()
    manager.add_pass(ConstantFolding())
    manager.add_pass(CopyPropagation())
    manager.add_pass(CommonSubexpressionElimination())
    manager.add_pass(AlgebraicSimplification())
    manager.add_pass(DeadCodeElimination())
    manager.add_pass(ControlFlowOptimization())

    return manager
