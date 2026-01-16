#!/usr/bin/env python3
"""
Toy Compiler - Main CLI Entry Point

The Toy programming language compiler with multiple backends:
- x86-64 assembly (native)
- LLVM IR (optimized, multi-platform)

Usage:
    toy examples/fibonacci.toy              # Compile and run
    toy --optimize examples/fibonacci.toy   # With optimizations
    toy --asm -o fib.s examples/fibonacci.toy  # Generate assembly
    toy --llvm examples/fibonacci.toy       # Generate LLVM IR
    toy --ir examples/test.toy              # Show IR

For more information: toy --help
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY or Windows without ANSI support)."""
        cls.RESET = ""
        cls.BOLD = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.GRAY = ""


@dataclass
class CompilationStats:
    """Statistics for each compilation phase."""
    phase_times: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0
    tokens_count: int = 0
    ast_nodes: int = 0
    ir_instructions: int = 0
    optimized_instructions: int = 0

    def add_phase(self, name: str, duration: float):
        self.phase_times[name] = duration
        self.total_time += duration

    def print_stats(self):
        """Print compilation statistics."""
        print(f"\n{Colors.CYAN}Compilation Statistics:{Colors.RESET}")
        print("-" * 40)
        for phase, time_ms in self.phase_times.items():
            print(f"  {phase:<20} {time_ms:>8.2f} ms")
        print("-" * 40)
        print(f"  {'Total':<20} {self.total_time:>8.2f} ms")

        if self.ir_instructions > 0 and self.optimized_instructions > 0:
            reduction = (1 - self.optimized_instructions / self.ir_instructions) * 100
            print(f"\n{Colors.CYAN}Optimization Impact:{Colors.RESET}")
            print(f"  Instructions: {self.ir_instructions} -> {self.optimized_instructions} ({reduction:.1f}% reduction)")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the Toy compiler."""
    parser = argparse.ArgumentParser(
        prog="toy",
        description="Toy Programming Language Compiler",
        epilog="Examples:\n"
               "  toy examples/fibonacci.toy              # Compile and run\n"
               "  toy --optimize examples/fibonacci.toy   # With optimizations\n"
               "  toy --asm -o fib.s examples/fibonacci.toy  # Generate assembly\n"
               "  toy --llvm examples/fibonacci.toy       # Generate LLVM IR\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "source",
        nargs="?",
        help="Toy source file to compile"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output file path"
    )
    output_group.add_argument(
        "--run", "-r",
        action="store_true",
        help="Compile and run the program (default if no output options)"
    )

    # Display options
    display_group = parser.add_argument_group("Display Options")
    display_group.add_argument(
        "--tokens",
        action="store_true",
        help="Display lexer tokens"
    )
    display_group.add_argument(
        "--ast",
        action="store_true",
        help="Display abstract syntax tree"
    )
    display_group.add_argument(
        "--ir",
        action="store_true",
        help="Display intermediate representation"
    )
    display_group.add_argument(
        "--ir-opt",
        action="store_true",
        help="Display optimized IR"
    )
    display_group.add_argument(
        "--asm",
        action="store_true",
        help="Display/output x86-64 assembly"
    )
    display_group.add_argument(
        "--llvm",
        action="store_true",
        help="Display/output LLVM IR"
    )

    # Compilation options
    compile_group = parser.add_argument_group("Compilation Options")
    compile_group.add_argument(
        "-O", "--optimize",
        action="store_true",
        help="Enable optimizations"
    )
    compile_group.add_argument(
        "--backend",
        choices=["x86", "llvm"],
        default="x86",
        help="Code generation backend (default: x86)"
    )

    # Debug options
    debug_group = parser.add_argument_group("Debug Options")
    debug_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output with compilation statistics"
    )
    debug_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    # Info options
    info_group = parser.add_argument_group("Information")
    info_group.add_argument(
        "--version",
        action="version",
        version="Toy Compiler v1.0.0"
    )

    return parser


def print_error(message: str, source: str = None, line: int = None, column: int = None):
    """Print a formatted error message with source context."""
    print(f"{Colors.RED}{Colors.BOLD}Error:{Colors.RESET} {message}")

    if source and line is not None:
        lines = source.split('\n')
        if 0 < line <= len(lines):
            source_line = lines[line - 1]
            print(f"\n  {Colors.GRAY}{line:4d} |{Colors.RESET} {source_line}")

            if column is not None and column > 0:
                pointer = " " * (7 + column - 1) + Colors.RED + "^" + Colors.RESET
                print(pointer)


def print_tokens(source: str):
    """Print tokens from the source code."""
    from src.lexer.lexer import Lexer

    print(f"\n{Colors.CYAN}{Colors.BOLD}Tokens:{Colors.RESET}")
    print("-" * 60)

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    for token in tokens:
        token_type = f"{Colors.YELLOW}{token.type.name:<15}{Colors.RESET}"
        value = f"{Colors.GREEN}{repr(token.value):<20}{Colors.RESET}" if token.value else ""
        location = f"{Colors.GRAY}line {token.line}, col {token.column}{Colors.RESET}"
        print(f"  {token_type} {value} {location}")

    print(f"\n  Total: {len(tokens)} tokens")
    return tokens


def print_ast(source: str):
    """Print the AST from the source code."""
    from src.lexer.lexer import Lexer
    from src.parser.parser import Parser

    print(f"\n{Colors.CYAN}{Colors.BOLD}Abstract Syntax Tree:{Colors.RESET}")
    print("-" * 60)

    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Simple AST printer
    def print_node(node, indent=0):
        prefix = "  " * indent
        node_name = node.__class__.__name__
        print(f"{prefix}{Colors.MAGENTA}{node_name}{Colors.RESET}", end="")

        # Print relevant attributes
        if hasattr(node, 'name'):
            print(f" {Colors.GREEN}{node.name}{Colors.RESET}", end="")
        if hasattr(node, 'value') and not hasattr(node, 'left'):
            print(f" = {Colors.YELLOW}{node.value}{Colors.RESET}", end="")
        if hasattr(node, 'operator'):
            print(f" ({Colors.CYAN}{node.operator}{Colors.RESET})", end="")
        if hasattr(node, 'type_annotation') and node.type_annotation:
            print(f" : {Colors.BLUE}{node.type_annotation}{Colors.RESET}", end="")
        print()

        # Recursively print children
        for attr in ['functions', 'parameters', 'body', 'statements', 'condition',
                     'then_body', 'else_body', 'left', 'right', 'operand',
                     'expression', 'callee', 'arguments', 'initializer']:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child is not None:
                    if isinstance(child, list):
                        for item in child:
                            print_node(item, indent + 1)
                    elif hasattr(child, '__class__') and child.__class__.__module__.startswith('src'):
                        print_node(child, indent + 1)

    print_node(ast)
    return ast


def print_ir(source: str, optimize: bool = False) -> str:
    """Print the IR from the source code."""
    from src.ir import generate_ir_from_source
    from src.ir.optimizations import create_default_pass_manager

    ir_module = generate_ir_from_source(source)

    if optimize:
        print(f"\n{Colors.CYAN}{Colors.BOLD}Optimized IR:{Colors.RESET}")
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(ir_module)
    else:
        print(f"\n{Colors.CYAN}{Colors.BOLD}Intermediate Representation:{Colors.RESET}")

    print("-" * 60)
    print(ir_module)
    return str(ir_module)


def compile_and_display(args, source: str, stats: CompilationStats):
    """Compile source and display requested outputs."""
    from src.lexer.lexer import Lexer
    from src.parser.parser import Parser

    # Tokenization
    if args.tokens:
        start = time.perf_counter()
        tokens = print_tokens(source)
        stats.add_phase("Lexer", (time.perf_counter() - start) * 1000)
        stats.tokens_count = len(tokens)

    # AST
    if args.ast:
        start = time.perf_counter()
        ast = print_ast(source)
        stats.add_phase("Parser", (time.perf_counter() - start) * 1000)

    # IR (unoptimized)
    if args.ir:
        start = time.perf_counter()
        print_ir(source, optimize=False)
        stats.add_phase("IR Generation", (time.perf_counter() - start) * 1000)

    # IR (optimized)
    if args.ir_opt:
        start = time.perf_counter()
        print_ir(source, optimize=True)
        stats.add_phase("Optimization", (time.perf_counter() - start) * 1000)

    # Assembly
    if args.asm:
        from src.codegen import compile_source_to_asm

        start = time.perf_counter()
        asm = compile_source_to_asm(source, optimize=args.optimize)
        stats.add_phase("x86-64 Codegen", (time.perf_counter() - start) * 1000)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(asm)
            print(f"{Colors.GREEN}Assembly written to {args.output}{Colors.RESET}")
        else:
            print(f"\n{Colors.CYAN}{Colors.BOLD}x86-64 Assembly:{Colors.RESET}")
            print("-" * 60)
            print(asm)

    # LLVM IR
    if args.llvm:
        from src.codegen import compile_to_llvm_ir

        start = time.perf_counter()
        llvm_ir = compile_to_llvm_ir(source, optimize=args.optimize)
        stats.add_phase("LLVM Codegen", (time.perf_counter() - start) * 1000)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(llvm_ir)
            print(f"{Colors.GREEN}LLVM IR written to {args.output}{Colors.RESET}")
        else:
            print(f"\n{Colors.CYAN}{Colors.BOLD}LLVM IR:{Colors.RESET}")
            print("-" * 60)
            print(llvm_ir)


def run_program(args, source: str, stats: CompilationStats) -> int:
    """Compile and run the program."""
    if args.backend == "llvm":
        from src.codegen import compile_and_run_llvm

        start = time.perf_counter()
        result = compile_and_run_llvm(source, optimize=args.optimize)
        stats.add_phase("LLVM Compile+Run", (time.perf_counter() - start) * 1000)

        if not result.success:
            print_error(result.error or "Compilation failed")
            return 1

        if args.verbose:
            print(f"\n{Colors.GREEN}Program exited with code: {result.return_value}{Colors.RESET}")

        return result.return_value or 0
    else:
        from src.codegen import compile_and_run

        start = time.perf_counter()
        result = compile_and_run(source, optimize=args.optimize)
        stats.add_phase("x86 Compile+Run", (time.perf_counter() - start) * 1000)

        if not result.success:
            print_error(result.error_message or "Compilation failed")
            if result.stderr:
                print(f"{Colors.GRAY}{result.stderr}{Colors.RESET}")
            return 1

        # Print stdout from program
        if result.stdout:
            print(result.stdout, end="")

        if args.verbose:
            print(f"\n{Colors.GREEN}Program exited with code: {result.return_code}{Colors.RESET}")

        return result.return_code


def main():
    """Main entry point for the Toy compiler."""
    parser = create_parser()
    args = parser.parse_args()

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Check if source file is provided
    if not args.source:
        parser.print_help()
        return 0

    # Read source file
    source_path = Path(args.source)
    if not source_path.exists():
        print_error(f"File not found: {args.source}")
        return 1

    if not source_path.suffix == ".toy":
        print(f"{Colors.YELLOW}Warning: File does not have .toy extension{Colors.RESET}")

    try:
        source = source_path.read_text()
    except Exception as e:
        print_error(f"Could not read file: {e}")
        return 1

    # Initialize statistics
    stats = CompilationStats()

    # Determine what to do
    display_only = args.tokens or args.ast or args.ir or args.ir_opt or args.asm or args.llvm
    should_run = args.run or (not display_only and not args.output)

    try:
        # Display requested outputs
        if display_only:
            compile_and_display(args, source, stats)

        # Run the program
        if should_run and not (args.asm or args.llvm):
            return_code = run_program(args, source, stats)

            if args.verbose:
                stats.print_stats()

            return return_code

        if args.verbose and display_only:
            stats.print_stats()

        return 0

    except Exception as e:
        # Try to extract line/column info from error
        error_msg = str(e)
        line = None
        column = None

        # Try to parse error location from common error message formats
        import re
        match = re.search(r'line (\d+)', error_msg, re.IGNORECASE)
        if match:
            line = int(match.group(1))
        match = re.search(r'column (\d+)', error_msg, re.IGNORECASE)
        if match:
            column = int(match.group(1))

        print_error(error_msg, source, line, column)

        if args.verbose:
            import traceback
            print(f"\n{Colors.GRAY}Traceback:{Colors.RESET}")
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
