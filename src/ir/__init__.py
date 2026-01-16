"""
Intermediate Representation (IR) module for the Luna compiler.

This module provides SSA-based three-address code (TAC) generation:
- instructions.py: IR instruction definitions
- ssa.py: SSA variable management
- cfg.py: Control Flow Graph
- ir_generator.py: AST to IR translation
- ir_printer.py: IR pretty printing

Usage:
    from src.ir import generate_ir, print_ir

    # From AST:
    module = generate_ir(program)
    print_ir(module)

    # From source:
    module = generate_ir_from_source(source_code)
"""

from src.ir.instructions import (
    # Types
    IRType,
    IRValue,
    OpCode,
    make_constant,

    # Instructions
    IRInstruction,
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

    # Containers
    BasicBlock,
    IRParameter,
    IRFunction,
    IRModule,
)

from src.ir.ssa import (
    SSANameGenerator,
    SSAContext,
    luna_type_to_ir_type,
)

from src.ir.cfg import (
    CFG,
    CFGBuilder,
)

from src.ir.ir_generator import (
    IRGenerator,
    generate_ir,
    generate_ir_from_source,
)

from src.ir.ir_printer import (
    IRPrinter,
    print_ir,
    format_ir,
    format_function_dot,
)


__all__ = [
    # Types
    "IRType",
    "IRValue",
    "OpCode",
    "make_constant",

    # Instructions
    "IRInstruction",
    "BinaryOp",
    "UnaryOp",
    "Copy",
    "LoadConst",
    "Jump",
    "Branch",
    "Phi",
    "PhiSource",
    "Call",
    "Return",

    # Containers
    "BasicBlock",
    "IRParameter",
    "IRFunction",
    "IRModule",

    # SSA
    "SSANameGenerator",
    "SSAContext",
    "luna_type_to_ir_type",

    # CFG
    "CFG",
    "CFGBuilder",

    # Generator
    "IRGenerator",
    "generate_ir",
    "generate_ir_from_source",

    # Printer
    "IRPrinter",
    "print_ir",
    "format_ir",
    "format_function_dot",
]
