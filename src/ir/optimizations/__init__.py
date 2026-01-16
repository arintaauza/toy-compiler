"""
IR Optimization Passes for the Luna compiler.

This module provides a collection of optimization passes that transform
the SSA-based IR to improve performance and reduce code size.

Available passes:
- ConstantFolding: Evaluate constant expressions at compile time
- DeadCodeElimination: Remove instructions whose results are never used
- CommonSubexpressionElimination: Reuse previously computed expressions
- CopyPropagation: Replace copies with original values
- AlgebraicSimplification: Apply mathematical identities
- ControlFlowOptimization: Simplify branches and remove unreachable code

Usage:
    from src.ir.optimizations import create_default_pass_manager

    manager = create_default_pass_manager()
    manager.run_until_fixed_point(ir_module)

Or use individual passes:
    from src.ir.optimizations import ConstantFolding, PassManager

    manager = PassManager()
    manager.add_pass(ConstantFolding())
    manager.run(module)
"""

from src.ir.optimizations.pass_manager import (
    PassStatistics,
    OptimizationPass,
    FunctionPass,
    BlockPass,
    PassManager,
    create_default_pass_manager,
)

from src.ir.optimizations.constant_folding import ConstantFolding
from src.ir.optimizations.dead_code_elimination import DeadCodeElimination
from src.ir.optimizations.cse import CommonSubexpressionElimination
from src.ir.optimizations.copy_propagation import CopyPropagation
from src.ir.optimizations.algebraic import AlgebraicSimplification
from src.ir.optimizations.control_flow import ControlFlowOptimization


__all__ = [
    # Pass infrastructure
    "PassStatistics",
    "OptimizationPass",
    "FunctionPass",
    "BlockPass",
    "PassManager",
    "create_default_pass_manager",

    # Individual passes
    "ConstantFolding",
    "DeadCodeElimination",
    "CommonSubexpressionElimination",
    "CopyPropagation",
    "AlgebraicSimplification",
    "ControlFlowOptimization",
]
