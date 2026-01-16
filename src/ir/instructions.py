"""
SSA-based Intermediate Representation for the Luna compiler.

This module defines the instruction set for Luna's IR in Static Single Assignment
(SSA) form. In SSA form:
- Each variable is assigned exactly once
- Variables are versioned (x_0, x_1, x_2, etc.)
- Phi functions merge values at control flow join points

Instruction Types:
- BinaryOp: x_n = y_m op z_k
- UnaryOp: x_n = op y_m
- Copy: x_n = y_m
- LoadConst: x_n = constant
- Jump: unconditional branch
- Branch: conditional branch (if x_n goto L1 else L2)
- Phi: x_n = phi [x_i, B1], [x_j, B2]
- Call: x_n = call func(args...)
- Return: return x_n
- Label: block label (implicit in BasicBlock)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union, Any
from enum import Enum, auto


class IRType(Enum):
    """Types in the IR."""
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    VOID = auto()

    def __str__(self) -> str:
        return self.name.lower()


@dataclass
class IRValue:
    """
    Represents a value in SSA form.

    An IRValue can be:
    - A versioned variable: name="x", version=0 -> x_0
    - A constant: is_constant=True, constant_value=42
    - A temporary: name="t", version=5 -> t_5

    Attributes:
        name: Variable/temporary name
        version: SSA version number
        ir_type: Type of the value
        is_constant: True if this is a constant value
        constant_value: The constant value (if is_constant)
    """
    name: str
    version: int = 0
    ir_type: IRType = IRType.INT
    is_constant: bool = False
    constant_value: Any = None

    def __str__(self) -> str:
        if self.is_constant:
            if self.ir_type == IRType.STRING:
                return f'"{self.constant_value}"'
            elif self.ir_type == IRType.BOOL:
                return "true" if self.constant_value else "false"
            return str(self.constant_value)
        return f"{self.name}_{self.version}"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, IRValue):
            return False
        if self.is_constant and other.is_constant:
            return self.constant_value == other.constant_value and self.ir_type == other.ir_type
        return self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        if self.is_constant:
            return hash((self.constant_value, self.ir_type))
        return hash((self.name, self.version))


def make_constant(value: Any, ir_type: IRType) -> IRValue:
    """Create a constant IRValue."""
    return IRValue(
        name="",
        version=0,
        ir_type=ir_type,
        is_constant=True,
        constant_value=value
    )


class OpCode(Enum):
    """Operation codes for IR instructions."""
    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    NEG = "neg"  # Unary minus

    # Comparison
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    EQ = "=="
    NE = "!="

    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"

    def __str__(self) -> str:
        return self.value


@dataclass
class IRInstruction:
    """Base class for all IR instructions."""

    def __str__(self) -> str:
        raise NotImplementedError

    def get_uses(self) -> List[IRValue]:
        """Return list of values used by this instruction."""
        return []

    def get_def(self) -> Optional[IRValue]:
        """Return the value defined by this instruction, if any."""
        return None


@dataclass
class BinaryOp(IRInstruction):
    """
    Binary operation: dest = left op right

    Example: t_0 = a_0 + b_0
    """
    dest: IRValue
    op: OpCode
    left: IRValue
    right: IRValue

    def __str__(self) -> str:
        return f"    {self.dest} = {self.left} {self.op} {self.right}"

    def get_uses(self) -> List[IRValue]:
        return [self.left, self.right]

    def get_def(self) -> Optional[IRValue]:
        return self.dest


@dataclass
class UnaryOp(IRInstruction):
    """
    Unary operation: dest = op operand

    Example: t_0 = neg x_0
    Example: t_1 = not b_0
    """
    dest: IRValue
    op: OpCode
    operand: IRValue

    def __str__(self) -> str:
        return f"    {self.dest} = {self.op} {self.operand}"

    def get_uses(self) -> List[IRValue]:
        return [self.operand]

    def get_def(self) -> Optional[IRValue]:
        return self.dest


@dataclass
class Copy(IRInstruction):
    """
    Copy instruction: dest = source

    Used for assignments and register moves.
    Example: x_1 = t_0
    """
    dest: IRValue
    source: IRValue

    def __str__(self) -> str:
        return f"    {self.dest} = {self.source}"

    def get_uses(self) -> List[IRValue]:
        return [self.source]

    def get_def(self) -> Optional[IRValue]:
        return self.dest


@dataclass
class LoadConst(IRInstruction):
    """
    Load a constant value: dest = constant

    Example: t_0 = 42
    Example: t_1 = "hello"
    """
    dest: IRValue
    value: Any
    value_type: IRType

    def __str__(self) -> str:
        if self.value_type == IRType.STRING:
            return f'    {self.dest} = "{self.value}"'
        elif self.value_type == IRType.BOOL:
            bool_str = "true" if self.value else "false"
            return f"    {self.dest} = {bool_str}"
        return f"    {self.dest} = {self.value}"

    def get_def(self) -> Optional[IRValue]:
        return self.dest


@dataclass
class Jump(IRInstruction):
    """
    Unconditional jump: goto target_block

    Example: jump B2
    """
    target: str  # Block label

    def __str__(self) -> str:
        return f"    jump {self.target}"


@dataclass
class Branch(IRInstruction):
    """
    Conditional branch: if condition goto true_block else false_block

    Example: branch t_0, B1, B2
    """
    condition: IRValue
    true_target: str   # Block label for true case
    false_target: str  # Block label for false case

    def __str__(self) -> str:
        return f"    branch {self.condition}, {self.true_target}, {self.false_target}"

    def get_uses(self) -> List[IRValue]:
        return [self.condition]


@dataclass
class PhiSource:
    """A single source for a Phi function: (value, from_block)."""
    value: IRValue
    block: str  # Block label

    def __str__(self) -> str:
        return f"[{self.value}, {self.block}]"


@dataclass
class Phi(IRInstruction):
    """
    Phi function for SSA form: dest = phi [v1, B1], [v2, B2], ...

    Phi functions are placed at join points in the CFG where different
    control flow paths merge. They select the appropriate value based
    on which predecessor block control came from.

    Example: x_2 = phi [x_0, B1], [x_1, B2]
    """
    dest: IRValue
    sources: List[PhiSource]

    def __str__(self) -> str:
        sources_str = ", ".join(str(s) for s in self.sources)
        return f"    {self.dest} = phi {sources_str}"

    def get_uses(self) -> List[IRValue]:
        return [s.value for s in self.sources]

    def get_def(self) -> Optional[IRValue]:
        return self.dest

    def add_source(self, value: IRValue, block: str) -> None:
        """Add a new source to the phi function."""
        self.sources.append(PhiSource(value, block))


@dataclass
class Call(IRInstruction):
    """
    Function call: dest = call func(args...)

    Example: t_0 = call add(a_0, b_0)
    Example: call print(x_0)  (void return)
    """
    dest: Optional[IRValue]  # None for void functions
    function: str
    arguments: List[IRValue]

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.arguments)
        if self.dest is not None:
            return f"    {self.dest} = call {self.function}({args_str})"
        return f"    call {self.function}({args_str})"

    def get_uses(self) -> List[IRValue]:
        return self.arguments.copy()

    def get_def(self) -> Optional[IRValue]:
        return self.dest


@dataclass
class Return(IRInstruction):
    """
    Return statement: return value

    Example: return x_0
    Example: return (void)
    """
    value: Optional[IRValue] = None

    def __str__(self) -> str:
        if self.value is not None:
            return f"    return {self.value}"
        return "    return"

    def get_uses(self) -> List[IRValue]:
        if self.value is not None:
            return [self.value]
        return []


@dataclass
class BasicBlock:
    """
    A basic block in the control flow graph.

    A basic block is a sequence of instructions with:
    - One entry point (the first instruction)
    - One exit point (the last instruction, which is a terminator)
    - No internal branches (straight-line code except at the end)

    Attributes:
        label: Unique identifier for the block (B0, B1, etc.)
        instructions: List of IR instructions in the block
        predecessors: Labels of predecessor blocks
        successors: Labels of successor blocks
    """
    label: str
    instructions: List[IRInstruction] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"  {self.label}:"]
        for instr in self.instructions:
            lines.append(str(instr))
        return "\n".join(lines)

    def add_instruction(self, instr: IRInstruction) -> None:
        """Add an instruction to the block."""
        self.instructions.append(instr)

    def add_predecessor(self, block_label: str) -> None:
        """Add a predecessor block."""
        if block_label not in self.predecessors:
            self.predecessors.append(block_label)

    def add_successor(self, block_label: str) -> None:
        """Add a successor block."""
        if block_label not in self.successors:
            self.successors.append(block_label)

    def get_terminator(self) -> Optional[IRInstruction]:
        """Return the terminating instruction (Jump, Branch, or Return)."""
        if self.instructions:
            last = self.instructions[-1]
            if isinstance(last, (Jump, Branch, Return)):
                return last
        return None

    def is_terminated(self) -> bool:
        """Check if block has a terminator instruction."""
        return self.get_terminator() is not None

    def get_phi_instructions(self) -> List[Phi]:
        """Return all phi instructions at the start of the block."""
        phis = []
        for instr in self.instructions:
            if isinstance(instr, Phi):
                phis.append(instr)
            else:
                # Phi instructions must be at the start of the block
                break
        return phis


@dataclass
class IRParameter:
    """A function parameter in the IR."""
    name: str
    ir_type: IRType

    def __str__(self) -> str:
        return f"{self.name}_0: {self.ir_type}"


@dataclass
class IRFunction:
    """
    A function in the IR.

    Contains the function's entry block and all basic blocks in the CFG.

    Attributes:
        name: Function name
        parameters: List of parameters (with SSA version 0)
        return_type: Return type
        blocks: Dictionary of block label -> BasicBlock
        entry_block: Label of the entry block
    """
    name: str
    parameters: List[IRParameter] = field(default_factory=list)
    return_type: IRType = IRType.VOID
    blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    entry_block: str = "B0"

    def __str__(self) -> str:
        params_str = ", ".join(str(p) for p in self.parameters)
        lines = [f"FUNCTION {self.name}({params_str}) -> {self.return_type}:"]

        # Print blocks in order (entry first, then by label)
        if self.entry_block in self.blocks:
            lines.append(str(self.blocks[self.entry_block]))

        for label in sorted(self.blocks.keys()):
            if label != self.entry_block:
                lines.append(str(self.blocks[label]))

        return "\n".join(lines)

    def add_block(self, block: BasicBlock) -> None:
        """Add a basic block to the function."""
        self.blocks[block.label] = block

    def get_block(self, label: str) -> Optional[BasicBlock]:
        """Get a block by its label."""
        return self.blocks.get(label)

    def get_entry(self) -> Optional[BasicBlock]:
        """Get the entry block."""
        return self.blocks.get(self.entry_block)


@dataclass
class IRModule:
    """
    A complete IR module (compilation unit).

    Contains all functions in the program.

    Attributes:
        name: Module name (usually source file name)
        functions: Dictionary of function name -> IRFunction
        globals: Dictionary of global variable name -> IRValue
    """
    name: str = "module"
    functions: Dict[str, IRFunction] = field(default_factory=dict)
    globals: Dict[str, IRValue] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [f"; Module: {self.name}", ""]

        # Print global variables
        if self.globals:
            lines.append("; Globals:")
            for name, value in self.globals.items():
                lines.append(f"  @{name} = {value}")
            lines.append("")

        # Print functions
        for func in self.functions.values():
            lines.append(str(func))
            lines.append("")

        return "\n".join(lines)

    def add_function(self, func: IRFunction) -> None:
        """Add a function to the module."""
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[IRFunction]:
        """Get a function by name."""
        return self.functions.get(name)
