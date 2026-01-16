"""
IR Pretty Printer for the Toy compiler.

This module provides utilities for formatting and displaying IR code
in a human-readable format. Supports multiple output formats:
- Plain text (for terminal output)
- DOT format (for graph visualization with Graphviz)
- Annotated format (with SSA version tracking)

Usage:
    printer = IRPrinter()
    print(printer.format_module(module))

    # Or for DOT output:
    dot = printer.format_cfg_dot(function)
    # Then: dot -Tpng output.dot -o output.png
"""

from typing import Optional, List
from src.ir.instructions import (
    IRModule,
    IRFunction,
    BasicBlock,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Jump,
    Branch,
    Phi,
    Call,
    Return,
    IRType,
    IRValue,
)


class IRPrinter:
    """
    Pretty printer for IR code.

    Formats IR instructions, basic blocks, functions, and modules
    for human-readable output.
    """

    def __init__(self, indent: str = "  ", show_block_info: bool = True):
        """
        Initialize the IR printer.

        Args:
            indent: String to use for indentation
            show_block_info: Whether to show predecessor/successor info
        """
        self.indent = indent
        self.show_block_info = show_block_info

    def format_module(self, module: IRModule) -> str:
        """
        Format an entire IR module.

        Args:
            module: The IR module to format

        Returns:
            Formatted string representation
        """
        lines = []

        # Module header
        lines.append(f"; Module: {module.name}")
        lines.append(f"; Functions: {len(module.functions)}")
        lines.append("")

        # Global variables
        if module.globals:
            lines.append("; Global variables:")
            for name, value in module.globals.items():
                if value.is_constant:
                    lines.append(f"  @{name} = {value.constant_value} : {value.ir_type}")
                else:
                    lines.append(f"  @{name} : {value.ir_type}")
            lines.append("")

        # Functions
        for func in module.functions.values():
            lines.append(self.format_function(func))
            lines.append("")

        return "\n".join(lines)

    def format_function(self, func: IRFunction) -> str:
        """
        Format an IR function.

        Args:
            func: The IR function to format

        Returns:
            Formatted string representation
        """
        lines = []

        # Function signature
        params_str = ", ".join(
            f"{p.name}_0: {p.ir_type}" for p in func.parameters
        )
        lines.append(f"FUNCTION {func.name}({params_str}) -> {func.return_type}:")

        # Print blocks in order (entry first, then sorted)
        block_order = self._get_block_order(func)

        for label in block_order:
            block = func.blocks.get(label)
            if block:
                lines.append(self.format_block(block))

        return "\n".join(lines)

    def format_block(self, block: BasicBlock) -> str:
        """
        Format a basic block.

        Args:
            block: The basic block to format

        Returns:
            Formatted string representation
        """
        lines = []

        # Block header with optional predecessor/successor info
        if self.show_block_info and (block.predecessors or block.successors):
            preds = ", ".join(block.predecessors) if block.predecessors else "none"
            succs = ", ".join(block.successors) if block.successors else "none"
            lines.append(f"  {block.label}: ; preds: [{preds}], succs: [{succs}]")
        else:
            lines.append(f"  {block.label}:")

        # Instructions
        for instr in block.instructions:
            lines.append(self.format_instruction(instr))

        return "\n".join(lines)

    def format_instruction(self, instr: IRInstruction) -> str:
        """
        Format a single IR instruction.

        Args:
            instr: The instruction to format

        Returns:
            Formatted string representation
        """
        # The instruction's __str__ method provides basic formatting
        # We add extra indentation here
        return f"  {instr}"

    def _get_block_order(self, func: IRFunction) -> List[str]:
        """
        Get blocks in a sensible display order.

        Entry block first, then others in sorted order.
        """
        order = []
        if func.entry_block in func.blocks:
            order.append(func.entry_block)

        for label in sorted(func.blocks.keys()):
            if label not in order:
                order.append(label)

        return order

    def format_cfg_dot(self, func: IRFunction, title: Optional[str] = None) -> str:
        """
        Generate DOT format graph for CFG visualization.

        Can be rendered with Graphviz:
            dot -Tpng output.dot -o output.png

        Args:
            func: The IR function
            title: Optional title for the graph

        Returns:
            DOT format string
        """
        graph_title = title or func.name
        lines = [
            f'digraph "{graph_title}" {{',
            '  rankdir=TB;',
            '  node [shape=box, fontname="Courier New", fontsize=10];',
            '  edge [fontname="Courier New", fontsize=9];',
            ''
        ]

        # Find entry and exit blocks
        exit_blocks = set()
        for label, block in func.blocks.items():
            if any(isinstance(i, Return) for i in block.instructions):
                exit_blocks.add(label)

        # Add nodes
        for label, block in func.blocks.items():
            # Build label content
            content_lines = [f"<b>{label}</b>"]
            for instr in block.instructions:
                instr_str = str(instr).strip()
                # Escape HTML special characters
                instr_str = instr_str.replace("&", "&amp;")
                instr_str = instr_str.replace("<", "&lt;")
                instr_str = instr_str.replace(">", "&gt;")
                instr_str = instr_str.replace('"', "&quot;")
                content_lines.append(instr_str)

            content = "<br align='left'/>".join(content_lines) + "<br align='left'/>"

            # Node styling
            style = ""
            if label == func.entry_block:
                style = ', style="filled", fillcolor="lightgreen"'
            elif label in exit_blocks:
                style = ', style="filled", fillcolor="lightcoral"'

            lines.append(f'  {label} [label=<{content}>{style}];')

        lines.append('')

        # Add edges
        for label, block in func.blocks.items():
            terminator = block.get_terminator()
            if terminator is None:
                continue

            if isinstance(terminator, Jump):
                lines.append(f'  {label} -> {terminator.target};')
            elif isinstance(terminator, Branch):
                lines.append(f'  {label} -> {terminator.true_target} [label="T", color="green"];')
                lines.append(f'  {label} -> {terminator.false_target} [label="F", color="red"];')

        lines.append('}')
        return '\n'.join(lines)


def print_ir(module: IRModule) -> None:
    """
    Print IR module to stdout.

    Args:
        module: The IR module to print
    """
    printer = IRPrinter()
    print(printer.format_module(module))


def format_ir(module: IRModule) -> str:
    """
    Format IR module as string.

    Args:
        module: The IR module to format

    Returns:
        Formatted string
    """
    printer = IRPrinter()
    return printer.format_module(module)


def format_function_dot(func: IRFunction) -> str:
    """
    Format function CFG as DOT graph.

    Args:
        func: The IR function

    Returns:
        DOT format string
    """
    printer = IRPrinter()
    return printer.format_cfg_dot(func)
