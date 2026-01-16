"""
Control Flow Graph (CFG) for the Luna compiler.

The CFG represents the control flow structure of a function:
- Nodes are basic blocks
- Edges represent possible control flow between blocks
- Supports predecessor/successor queries
- Can compute dominance information for SSA construction

Key operations:
- Building CFG from basic blocks
- Adding/removing edges
- Computing dominators (for phi placement)
- DOT output for visualization
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

from src.ir.instructions import (
    BasicBlock,
    IRInstruction,
    Jump,
    Branch,
    Return,
    Phi,
    PhiSource,
    IRValue,
)


@dataclass
class CFG:
    """
    Control Flow Graph for a function.

    Manages basic blocks and control flow edges.

    Attributes:
        blocks: Dictionary of block label -> BasicBlock
        entry: Label of the entry block
        exit_blocks: Labels of blocks that exit the function (contain Return)
    """
    blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    entry: str = "B0"
    exit_blocks: List[str] = field(default_factory=list)

    def add_block(self, block: BasicBlock) -> None:
        """Add a basic block to the CFG."""
        self.blocks[block.label] = block

    def get_block(self, label: str) -> Optional[BasicBlock]:
        """Get a block by label."""
        return self.blocks.get(label)

    def add_edge(self, from_label: str, to_label: str) -> None:
        """
        Add an edge from one block to another.

        Updates both successor and predecessor lists.
        """
        if from_label in self.blocks:
            self.blocks[from_label].add_successor(to_label)
        if to_label in self.blocks:
            self.blocks[to_label].add_predecessor(from_label)

    def remove_edge(self, from_label: str, to_label: str) -> None:
        """Remove an edge between blocks."""
        if from_label in self.blocks:
            block = self.blocks[from_label]
            if to_label in block.successors:
                block.successors.remove(to_label)
        if to_label in self.blocks:
            block = self.blocks[to_label]
            if from_label in block.predecessors:
                block.predecessors.remove(from_label)

    def get_predecessors(self, label: str) -> List[str]:
        """Get predecessor block labels."""
        block = self.blocks.get(label)
        return block.predecessors if block else []

    def get_successors(self, label: str) -> List[str]:
        """Get successor block labels."""
        block = self.blocks.get(label)
        return block.successors if block else []

    def compute_edges_from_terminators(self) -> None:
        """
        Compute CFG edges from block terminator instructions.

        Examines Jump and Branch instructions to determine edges.
        """
        for label, block in self.blocks.items():
            terminator = block.get_terminator()
            if terminator is None:
                continue

            if isinstance(terminator, Jump):
                self.add_edge(label, terminator.target)
            elif isinstance(terminator, Branch):
                self.add_edge(label, terminator.true_target)
                self.add_edge(label, terminator.false_target)
            elif isinstance(terminator, Return):
                if label not in self.exit_blocks:
                    self.exit_blocks.append(label)

    def get_reverse_postorder(self) -> List[str]:
        """
        Get block labels in reverse postorder (for dataflow analysis).

        Reverse postorder ensures that (except for back edges) a block
        is processed before its successors.
        """
        visited: Set[str] = set()
        postorder: List[str] = []

        def dfs(label: str):
            if label in visited:
                return
            visited.add(label)
            block = self.blocks.get(label)
            if block:
                for succ in block.successors:
                    dfs(succ)
            postorder.append(label)

        dfs(self.entry)
        return list(reversed(postorder))

    def get_dominators(self) -> Dict[str, Set[str]]:
        """
        Compute dominators for all blocks.

        A block D dominates block B if every path from entry to B
        goes through D.

        Returns:
            Dictionary mapping block label -> set of dominator labels
        """
        # Initialize: entry is dominated only by itself,
        # all others are dominated by all blocks
        all_blocks = set(self.blocks.keys())
        dominators: Dict[str, Set[str]] = {}

        for label in self.blocks:
            if label == self.entry:
                dominators[label] = {label}
            else:
                dominators[label] = all_blocks.copy()

        # Iterate until fixed point
        changed = True
        while changed:
            changed = False
            for label in self.get_reverse_postorder():
                if label == self.entry:
                    continue

                # Dom(n) = {n} ∪ ∩{Dom(p) | p ∈ pred(n)}
                preds = self.get_predecessors(label)
                if not preds:
                    continue

                new_dom = all_blocks.copy()
                for pred in preds:
                    new_dom &= dominators.get(pred, all_blocks)
                new_dom.add(label)

                if new_dom != dominators[label]:
                    dominators[label] = new_dom
                    changed = True

        return dominators

    def get_immediate_dominators(self) -> Dict[str, Optional[str]]:
        """
        Compute immediate dominators.

        The immediate dominator of a block B is the unique block D
        that strictly dominates B but does not strictly dominate
        any other dominator of B.

        Returns:
            Dictionary mapping block label -> immediate dominator label (or None for entry)
        """
        dominators = self.get_dominators()
        idom: Dict[str, Optional[str]] = {}

        for label in self.blocks:
            if label == self.entry:
                idom[label] = None
                continue

            # Find immediate dominator: dominator closest to label
            doms = dominators[label] - {label}  # Strict dominators
            if not doms:
                idom[label] = None
                continue

            # idom is the dominator that is dominated by all other dominators
            for d in doms:
                d_doms = dominators[d] - {d}
                if doms - {d} == d_doms:
                    idom[label] = d
                    break
            else:
                # Fallback: pick any (shouldn't happen with valid CFG)
                idom[label] = next(iter(doms)) if doms else None

        return idom

    def get_dominance_frontier(self) -> Dict[str, Set[str]]:
        """
        Compute dominance frontiers.

        The dominance frontier of a block B is the set of blocks
        where B's dominance stops: blocks that B does not strictly
        dominate, but has a predecessor that B dominates.

        This is where phi functions need to be placed.

        Returns:
            Dictionary mapping block label -> set of frontier labels
        """
        idom = self.get_immediate_dominators()
        frontier: Dict[str, Set[str]] = {label: set() for label in self.blocks}

        for label, block in self.blocks.items():
            if len(block.predecessors) < 2:
                continue

            for pred in block.predecessors:
                runner = pred
                while runner is not None and runner != idom.get(label):
                    frontier[runner].add(label)
                    runner = idom.get(runner)

        return frontier

    def to_dot(self, function_name: str = "function") -> str:
        """
        Generate DOT format graph for visualization.

        Can be rendered with Graphviz: dot -Tpng cfg.dot -o cfg.png

        Args:
            function_name: Name to show in graph title

        Returns:
            DOT format string
        """
        lines = [
            f'digraph "{function_name}" {{',
            '  rankdir=TB;',
            '  node [shape=box, fontname="Courier"];',
            ''
        ]

        # Add nodes with instruction content
        for label, block in self.blocks.items():
            # Build label content
            content_lines = [label + ":"]
            for instr in block.instructions:
                # Escape special characters for DOT
                instr_str = str(instr).strip()
                instr_str = instr_str.replace('"', '\\"')
                instr_str = instr_str.replace('<', '\\<')
                instr_str = instr_str.replace('>', '\\>')
                content_lines.append(instr_str)

            content = "\\l".join(content_lines) + "\\l"
            node_style = ""
            if label == self.entry:
                node_style = ', style=filled, fillcolor=lightgreen'
            elif label in self.exit_blocks:
                node_style = ', style=filled, fillcolor=lightcoral'

            lines.append(f'  {label} [label="{content}"{node_style}];')

        lines.append('')

        # Add edges
        for label, block in self.blocks.items():
            for succ in block.successors:
                # Color true/false branches differently
                terminator = block.get_terminator()
                edge_style = ""
                if isinstance(terminator, Branch):
                    if succ == terminator.true_target:
                        edge_style = ' [color=green, label="T"]'
                    elif succ == terminator.false_target:
                        edge_style = ' [color=red, label="F"]'
                lines.append(f'  {label} -> {succ}{edge_style};')

        lines.append('}')
        return '\n'.join(lines)

    def __str__(self) -> str:
        """String representation showing blocks and edges."""
        lines = [f"CFG (entry={self.entry}):"]
        for label in sorted(self.blocks.keys()):
            block = self.blocks[label]
            preds = ", ".join(block.predecessors) if block.predecessors else "none"
            succs = ", ".join(block.successors) if block.successors else "none"
            lines.append(f"  {label}: preds=[{preds}], succs=[{succs}]")
        return "\n".join(lines)


class CFGBuilder:
    """
    Builder for constructing CFGs during IR generation.

    Provides a convenient API for creating blocks and managing
    the current insertion point.
    """

    def __init__(self):
        self.cfg = CFG()
        self._current_block: Optional[BasicBlock] = None
        self._block_counter = 0

    def new_block(self, prefix: str = "B") -> BasicBlock:
        """Create a new basic block with unique label."""
        label = f"{prefix}{self._block_counter}"
        self._block_counter += 1
        block = BasicBlock(label=label)
        self.cfg.add_block(block)
        return block

    def set_entry(self, label: str) -> None:
        """Set the entry block."""
        self.cfg.entry = label

    def position_at_end(self, block: BasicBlock) -> None:
        """Set insertion point to end of block."""
        self._current_block = block

    def get_current_block(self) -> Optional[BasicBlock]:
        """Get the current block."""
        return self._current_block

    def get_current_label(self) -> str:
        """Get label of current block."""
        if self._current_block:
            return self._current_block.label
        return ""

    def emit(self, instruction: IRInstruction) -> None:
        """Emit an instruction to the current block."""
        if self._current_block:
            self._current_block.add_instruction(instruction)

    def emit_jump(self, target: str) -> None:
        """Emit a jump and update CFG edges."""
        if self._current_block:
            self._current_block.add_instruction(Jump(target))
            self.cfg.add_edge(self._current_block.label, target)

    def emit_branch(self, condition: IRValue, true_target: str, false_target: str) -> None:
        """Emit a conditional branch and update CFG edges."""
        if self._current_block:
            self._current_block.add_instruction(Branch(condition, true_target, false_target))
            self.cfg.add_edge(self._current_block.label, true_target)
            self.cfg.add_edge(self._current_block.label, false_target)

    def emit_return(self, value: Optional[IRValue] = None) -> None:
        """Emit a return instruction."""
        if self._current_block:
            self._current_block.add_instruction(Return(value))
            if self._current_block.label not in self.cfg.exit_blocks:
                self.cfg.exit_blocks.append(self._current_block.label)

    def finalize(self) -> CFG:
        """Finalize and return the CFG."""
        return self.cfg
