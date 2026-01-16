"""
Symbol table for the Luna compiler.

The symbol table manages variable and function declarations across scopes.
It supports:
- Nested scopes (global, function, block)
- Symbol lookup with scope chain traversal
- Duplicate declaration detection
- Constant tracking
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto

from src.semantic.types import LunaType, FunctionType


class SymbolKind(Enum):
    """Kind of symbol (variable, constant, function, parameter)."""
    VARIABLE = auto()
    CONSTANT = auto()
    FUNCTION = auto()
    PARAMETER = auto()


@dataclass
class Symbol:
    """
    Represents a declared symbol in the program.

    Attributes:
        name: The symbol's identifier
        type: The symbol's Luna type
        kind: Kind of symbol (variable, constant, function, parameter)
        line: Line number where symbol was declared
        column: Column number where symbol was declared
        is_initialized: Whether the symbol has been assigned a value
    """
    name: str
    type: LunaType
    kind: SymbolKind
    line: int = 0
    column: int = 0
    is_initialized: bool = False

    def __repr__(self) -> str:
        return f"Symbol({self.name}: {self.type}, {self.kind.name})"

    @property
    def is_const(self) -> bool:
        """Check if this symbol is a constant."""
        return self.kind == SymbolKind.CONSTANT

    @property
    def is_function(self) -> bool:
        """Check if this symbol is a function."""
        return self.kind == SymbolKind.FUNCTION


@dataclass
class Scope:
    """
    Represents a single scope level in the symbol table.

    Each scope has:
    - A name (for debugging)
    - A dictionary of symbols declared in this scope
    - An optional parent scope
    """
    name: str
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    parent: Optional['Scope'] = None

    def define(self, symbol: Symbol) -> bool:
        """
        Define a new symbol in this scope.

        Args:
            symbol: The symbol to define

        Returns:
            True if successful, False if symbol already exists in this scope
        """
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol in this scope only (not parent scopes).

        Args:
            name: Symbol name to look up

        Returns:
            The symbol if found, None otherwise
        """
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol in this scope and all parent scopes.

        Args:
            name: Symbol name to look up

        Returns:
            The symbol if found in any scope, None otherwise
        """
        # Check this scope first
        if name in self.symbols:
            return self.symbols[name]

        # Check parent scopes
        if self.parent is not None:
            return self.parent.lookup(name)

        return None

    def __repr__(self) -> str:
        return f"Scope({self.name}, {len(self.symbols)} symbols)"


class SymbolTable:
    """
    Manages symbol declarations across all scopes.

    The symbol table uses a stack of scopes:
    - Global scope is always at the bottom
    - Function scopes are pushed when entering functions
    - Block scopes are pushed when entering blocks

    Usage:
        table = SymbolTable()
        table.enter_scope("function_main")  # Enter a new scope
        table.define(Symbol("x", INT, SymbolKind.VARIABLE))  # Define a symbol
        sym = table.lookup("x")  # Look up a symbol
        table.exit_scope()  # Exit the scope
    """

    def __init__(self):
        """Initialize the symbol table with a global scope."""
        self._global_scope = Scope("global")
        self._current_scope = self._global_scope
        self._scope_stack: List[Scope] = [self._global_scope]

    @property
    def current_scope(self) -> Scope:
        """Get the current (innermost) scope."""
        return self._current_scope

    @property
    def global_scope(self) -> Scope:
        """Get the global scope."""
        return self._global_scope

    @property
    def scope_depth(self) -> int:
        """Get the current scope depth (0 = global)."""
        return len(self._scope_stack) - 1

    def enter_scope(self, name: str = "block") -> Scope:
        """
        Enter a new scope.

        Args:
            name: Name for the scope (for debugging)

        Returns:
            The new scope
        """
        new_scope = Scope(name=name, parent=self._current_scope)
        self._scope_stack.append(new_scope)
        self._current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Scope:
        """
        Exit the current scope and return to the parent scope.

        Returns:
            The exited scope

        Raises:
            RuntimeError: If attempting to exit the global scope
        """
        if self._current_scope == self._global_scope:
            raise RuntimeError("Cannot exit global scope")

        exited_scope = self._current_scope
        self._scope_stack.pop()
        self._current_scope = self._scope_stack[-1]
        return exited_scope

    def define(self, symbol: Symbol) -> bool:
        """
        Define a symbol in the current scope.

        Args:
            symbol: The symbol to define

        Returns:
            True if successful, False if symbol already exists in current scope
        """
        return self._current_scope.define(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol in the current scope chain.

        Searches the current scope first, then parent scopes.

        Args:
            name: Symbol name to look up

        Returns:
            The symbol if found, None otherwise
        """
        return self._current_scope.lookup(name)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol in the current scope only.

        Does not search parent scopes.

        Args:
            name: Symbol name to look up

        Returns:
            The symbol if found in current scope, None otherwise
        """
        return self._current_scope.lookup_local(name)

    def lookup_global(self, name: str) -> Optional[Symbol]:
        """
        Look up a symbol in the global scope only.

        Args:
            name: Symbol name to look up

        Returns:
            The symbol if found in global scope, None otherwise
        """
        return self._global_scope.lookup_local(name)

    def is_global_scope(self) -> bool:
        """Check if the current scope is the global scope."""
        return self._current_scope == self._global_scope

    def define_builtin_function(
        self,
        name: str,
        param_types: List[LunaType],
        return_type: LunaType
    ) -> Symbol:
        """
        Define a built-in function in the global scope.

        Args:
            name: Function name
            param_types: List of parameter types
            return_type: Return type

        Returns:
            The created symbol
        """
        func_type = FunctionType(
            parameter_types=param_types,
            return_type=return_type
        )
        symbol = Symbol(
            name=name,
            type=func_type,
            kind=SymbolKind.FUNCTION,
            is_initialized=True
        )
        self._global_scope.define(symbol)
        return symbol

    def __repr__(self) -> str:
        return f"SymbolTable(depth={self.scope_depth}, current={self._current_scope.name})"


def create_symbol_table_with_builtins() -> SymbolTable:
    """
    Create a symbol table pre-populated with Luna's built-in functions.

    Built-in functions:
    - print(value: any) -> void
    - input(prompt: string) -> string
    - len(str: string) -> int

    Returns:
        A new SymbolTable with built-in functions defined
    """
    from src.semantic.types import INT, STRING, VOID

    table = SymbolTable()

    # print() - accepts any type, returns void
    # For simplicity, we'll define multiple overloads or use a special "any" handling
    # For now, we'll handle print specially in the type checker
    table.define_builtin_function("print", [INT], VOID)

    # input() - takes prompt, returns string
    table.define_builtin_function("input", [STRING], STRING)

    # len() - takes string, returns int
    table.define_builtin_function("len", [STRING], INT)

    return table
