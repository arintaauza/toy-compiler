"""
SSA (Static Single Assignment) variable management for the Luna compiler.

This module provides utilities for managing SSA variable versioning:
- Variable versioning (x_0, x_1, x_2, ...)
- Temporary variable generation (t_0, t_1, ...)
- Block label generation (B0, B1, ...)
- Version tracking across scopes

Key concepts:
- Each variable assignment creates a new version
- Version numbers are per-variable (not global)
- Phi functions at join points merge versions
"""

from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field

from src.ir.instructions import IRValue, IRType


class SSANameGenerator:
    """
    Generates unique SSA names and versions for variables.

    Tracks:
    - Current version for each variable
    - Temporary variable counter
    - Block label counter

    Example usage:
        gen = SSANameGenerator()
        x_0 = gen.new_variable("x", IRType.INT)  # x_0
        x_1 = gen.new_version("x")                # x_1
        t_0 = gen.new_temp(IRType.INT)           # t_0
        B1 = gen.new_block_label()               # B1
    """

    def __init__(self):
        # Maps variable name to its current version
        self._var_versions: Dict[str, int] = {}
        # Maps variable name to its type
        self._var_types: Dict[str, IRType] = {}
        # Counter for temporary variables
        self._temp_counter: int = 0
        # Counter for block labels
        self._block_counter: int = 0
        # Stack of scope snapshots for nested scopes
        self._scope_stack: List[Dict[str, int]] = []

    def new_variable(self, name: str, ir_type: IRType) -> IRValue:
        """
        Create a new variable with version 0.

        Args:
            name: Variable name
            ir_type: Type of the variable

        Returns:
            IRValue with version 0
        """
        if name not in self._var_versions:
            self._var_versions[name] = 0
            self._var_types[name] = ir_type
        else:
            # Variable already exists, get next version
            self._var_versions[name] += 1

        return IRValue(
            name=name,
            version=self._var_versions[name],
            ir_type=ir_type
        )

    def new_version(self, name: str) -> IRValue:
        """
        Create a new version of an existing variable.

        Args:
            name: Variable name

        Returns:
            IRValue with incremented version

        Raises:
            KeyError: If variable doesn't exist
        """
        if name not in self._var_versions:
            raise KeyError(f"Variable '{name}' not found in SSA context")

        self._var_versions[name] += 1
        return IRValue(
            name=name,
            version=self._var_versions[name],
            ir_type=self._var_types[name]
        )

    def get_current(self, name: str) -> IRValue:
        """
        Get the current version of a variable.

        Args:
            name: Variable name

        Returns:
            IRValue with current version

        Raises:
            KeyError: If variable doesn't exist
        """
        if name not in self._var_versions:
            raise KeyError(f"Variable '{name}' not found in SSA context")

        return IRValue(
            name=name,
            version=self._var_versions[name],
            ir_type=self._var_types[name]
        )

    def get_current_version(self, name: str) -> int:
        """Get just the version number for a variable."""
        if name not in self._var_versions:
            raise KeyError(f"Variable '{name}' not found in SSA context")
        return self._var_versions[name]

    def set_version(self, name: str, version: int) -> None:
        """
        Set the current version of a variable.

        Used for phi function resolution in loops where we need to
        update the current version to match the phi destination.

        Args:
            name: Variable name
            version: Version number to set

        Raises:
            KeyError: If variable doesn't exist
        """
        if name not in self._var_versions:
            raise KeyError(f"Variable '{name}' not found in SSA context")
        self._var_versions[name] = version

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        return name in self._var_versions

    def new_temp(self, ir_type: IRType = IRType.INT) -> IRValue:
        """
        Create a new temporary variable.

        Temporaries are named t_0, t_1, t_2, ...

        Args:
            ir_type: Type of the temporary

        Returns:
            New temporary IRValue
        """
        temp = IRValue(
            name="t",
            version=self._temp_counter,
            ir_type=ir_type
        )
        self._temp_counter += 1
        return temp

    def new_block_label(self, prefix: str = "B") -> str:
        """
        Generate a new unique block label.

        Labels are B0, B1, B2, ... or with custom prefix.

        Args:
            prefix: Label prefix (default "B")

        Returns:
            New block label string
        """
        label = f"{prefix}{self._block_counter}"
        self._block_counter += 1
        return label

    def push_scope(self) -> None:
        """
        Push current variable versions onto the scope stack.

        Used when entering a new scope (e.g., function body, if branch).
        """
        self._scope_stack.append(self._var_versions.copy())

    def pop_scope(self) -> Dict[str, int]:
        """
        Pop and restore previous variable versions.

        Used when exiting a scope.

        Returns:
            The popped scope's version mapping
        """
        if not self._scope_stack:
            raise RuntimeError("Cannot pop from empty scope stack")
        return self._scope_stack.pop()

    def get_scope_snapshot(self) -> Dict[str, int]:
        """Get a snapshot of current variable versions."""
        return self._var_versions.copy()

    def restore_scope(self, snapshot: Dict[str, int]) -> None:
        """Restore variable versions from a snapshot."""
        self._var_versions = snapshot.copy()

    def get_all_variables(self) -> Set[str]:
        """Get all variable names."""
        return set(self._var_versions.keys())

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._var_versions.clear()
        self._var_types.clear()
        self._temp_counter = 0
        self._block_counter = 0
        self._scope_stack.clear()


@dataclass
class SSAContext:
    """
    Context for SSA construction during IR generation.

    Tracks:
    - Current basic block being generated
    - Variable versions per block (for phi insertion)
    - Incomplete phi functions that need backpatching

    Attributes:
        name_gen: The SSA name generator
        current_block: Label of the current block
        block_var_versions: Mapping of block -> (var -> version at block end)
        incomplete_phis: Phi functions needing source additions
    """
    name_gen: SSANameGenerator = field(default_factory=SSANameGenerator)
    current_block: str = "B0"
    # Maps block label -> (var name -> version at end of block)
    block_var_versions: Dict[str, Dict[str, int]] = field(default_factory=dict)
    # Maps (block_label, var_name) -> Phi instruction needing sources
    incomplete_phis: Dict[tuple, 'Phi'] = field(default_factory=dict)

    def snapshot_versions(self, block_label: str) -> None:
        """Save current variable versions for a block."""
        self.block_var_versions[block_label] = self.name_gen.get_scope_snapshot()

    def get_block_versions(self, block_label: str) -> Dict[str, int]:
        """Get the variable versions at the end of a block."""
        return self.block_var_versions.get(block_label, {})


def luna_type_to_ir_type(luna_type_name: str) -> IRType:
    """
    Convert Luna type name to IR type.

    Args:
        luna_type_name: Luna type as string ("int", "float", etc.)

    Returns:
        Corresponding IRType

    Raises:
        ValueError: If type is unknown
    """
    type_map = {
        "int": IRType.INT,
        "INT": IRType.INT,
        "float": IRType.FLOAT,
        "FLOAT": IRType.FLOAT,
        "bool": IRType.BOOL,
        "BOOL": IRType.BOOL,
        "string": IRType.STRING,
        "STRING": IRType.STRING,
        "void": IRType.VOID,
        "VOID": IRType.VOID,
    }

    if luna_type_name in type_map:
        return type_map[luna_type_name]

    raise ValueError(f"Unknown Luna type: {luna_type_name}")
