"""
Stack Frame Layout for x86-64 Code Generation.

This module handles stack frame management for the Toy compiler,
including:
- Assigning stack offsets to SSA variables
- Tracking frame size for prologue/epilogue
- Managing function parameters

Stack Frame Layout (System V AMD64 ABI):
    +------------------+ <- rbp (frame pointer)
    | Saved rbp        | [rbp+0]
    +------------------+
    | Return address   | [rbp+8] (pushed by call)
    +------------------+
    | ... caller's     |
    | stack frame ...  |
    +------------------+
    |                  |
    | Local variables  | [rbp-8], [rbp-16], etc.
    |                  |
    +------------------+
    | Alignment pad    | (if needed for 16-byte alignment)
    +------------------+ <- rsp (stack pointer)

Each SSA variable (x_0, x_1, t_0, etc.) gets its own 8-byte slot.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from src.ir.instructions import (
    IRFunction,
    IRInstruction,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Phi,
    Call,
    Return,
    IRValue,
    IRType,
)


@dataclass
class StackSlot:
    """Represents a slot on the stack."""
    offset: int  # Negative offset from rbp
    size: int = 8  # All slots are 8 bytes (64-bit)
    ir_type: IRType = IRType.INT

    def __str__(self) -> str:
        return f"[rbp{self.offset:+d}]"


@dataclass
class StackFrame:
    """
    Manages the stack frame for a function.

    Tracks:
    - Variable to stack offset mapping
    - Total frame size
    - Parameter locations
    """
    function_name: str
    # Maps (var_name, version) to stack slot
    variables: Dict[Tuple[str, int], StackSlot] = field(default_factory=dict)
    # Current stack offset (grows negative)
    current_offset: int = 0
    # Number of parameters
    param_count: int = 0

    def allocate(self, var_name: str, version: int, ir_type: IRType = IRType.INT) -> StackSlot:
        """
        Allocate a stack slot for a variable.

        Args:
            var_name: Variable name
            version: SSA version number
            ir_type: Type of the variable

        Returns:
            The allocated StackSlot
        """
        key = (var_name, version)
        if key in self.variables:
            return self.variables[key]

        # Allocate new slot (8 bytes, aligned)
        self.current_offset -= 8
        slot = StackSlot(offset=self.current_offset, ir_type=ir_type)
        self.variables[key] = slot
        return slot

    def get_slot(self, value: IRValue) -> Optional[StackSlot]:
        """
        Get the stack slot for an IRValue.

        Args:
            value: The IR value to look up

        Returns:
            The StackSlot, or None if not found (e.g., for constants)
        """
        if value.is_constant:
            return None

        key = (value.name, value.version)
        return self.variables.get(key)

    def get_or_allocate(self, value: IRValue) -> Optional[StackSlot]:
        """
        Get existing slot or allocate new one for a variable.

        Args:
            value: The IR value

        Returns:
            The StackSlot, or None for constants
        """
        if value.is_constant:
            return None

        slot = self.get_slot(value)
        if slot is None:
            slot = self.allocate(value.name, value.version, value.ir_type)
        return slot

    @property
    def frame_size(self) -> int:
        """
        Get the total frame size (positive value).

        The frame size is rounded up to 16 bytes for alignment.
        """
        size = -self.current_offset
        # Align to 16 bytes (required by System V ABI for calls)
        if size % 16 != 0:
            size = ((size // 16) + 1) * 16
        return size

    def __str__(self) -> str:
        lines = [f"StackFrame for {self.function_name}:"]
        lines.append(f"  Frame size: {self.frame_size} bytes")
        lines.append(f"  Variables ({len(self.variables)}):")
        for (name, version), slot in sorted(self.variables.items()):
            lines.append(f"    {name}_{version}: {slot}")
        return "\n".join(lines)


class StackFrameBuilder:
    """
    Builds stack frame layout for a function.

    Analyzes the function's IR to determine all variables
    that need stack slots.
    """

    # Argument registers in order (System V AMD64 ABI)
    ARG_REGISTERS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']

    def __init__(self):
        pass

    def build(self, func: IRFunction) -> StackFrame:
        """
        Build a stack frame for a function.

        Args:
            func: The IR function to analyze

        Returns:
            A StackFrame with all variables allocated
        """
        frame = StackFrame(function_name=func.name)
        frame.param_count = len(func.parameters)

        # First, allocate slots for parameters
        # Parameters come in via registers, we copy them to stack
        for param in func.parameters:
            frame.allocate(param.name, 0, param.ir_type)

        # Then, scan all instructions and allocate for all defined values
        for block in func.blocks.values():
            for instr in block.instructions:
                self._process_instruction(instr, frame)

        return frame

    def _process_instruction(self, instr: IRInstruction, frame: StackFrame) -> None:
        """
        Process an instruction and allocate stack slots for defined values.

        Args:
            instr: The instruction to process
            frame: The stack frame to update
        """
        # Get the value defined by this instruction
        defined = instr.get_def()
        if defined is not None and not defined.is_constant:
            frame.get_or_allocate(defined)

        # Also allocate for any non-constant uses
        # (they might be defined in other blocks)
        for use in instr.get_uses():
            if not use.is_constant:
                frame.get_or_allocate(use)

    def get_param_register(self, index: int) -> Optional[str]:
        """
        Get the register used for a parameter by index.

        Args:
            index: Parameter index (0-based)

        Returns:
            Register name, or None if passed on stack
        """
        if index < len(self.ARG_REGISTERS):
            return self.ARG_REGISTERS[index]
        return None

    def get_param_stack_offset(self, index: int) -> Optional[int]:
        """
        Get the stack offset for a parameter passed on stack.

        Args:
            index: Parameter index (0-based)

        Returns:
            Positive offset from rbp, or None if passed in register
        """
        if index < len(self.ARG_REGISTERS):
            return None
        # Parameters 7+ are on stack at [rbp+16], [rbp+24], etc.
        # (rbp+0 is saved rbp, rbp+8 is return address)
        stack_index = index - len(self.ARG_REGISTERS)
        return 16 + (stack_index * 8)
