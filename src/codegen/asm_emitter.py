"""
Assembly File Emitter for the Luna compiler.

This module provides high-level functions to compile Luna source code
to assembly files and optionally assemble/link them.

Usage:
    from src.codegen import compile_to_asm, compile_and_run

    # Generate assembly file
    compile_to_asm("program.luna", "program.s")

    # Compile and run
    result = compile_and_run("program.luna")
    print(result.stdout)
"""

import subprocess
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from src.ir import generate_ir_from_source, generate_ir
from src.ir.optimizations import create_default_pass_manager
from src.codegen.x86_64_codegen import generate_assembly


@dataclass
class CompileResult:
    """Result of compiling and running a program."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    assembly: str = ""
    error_message: str = ""


def compile_source_to_asm(
    source: str,
    optimize: bool = True,
    module_name: str = "module"
) -> str:
    """
    Compile Luna source code to x86-64 assembly.

    Args:
        source: Luna source code string
        optimize: Whether to run optimization passes
        module_name: Name for the IR module

    Returns:
        Assembly code as a string
    """
    # Generate IR from source
    module = generate_ir_from_source(source)

    # Optionally optimize
    if optimize:
        manager = create_default_pass_manager()
        manager.run_until_fixed_point(module)

    # Generate assembly
    assembly = generate_assembly(module)

    return assembly


def compile_to_asm(
    source_path: str,
    output_path: str,
    optimize: bool = True
) -> None:
    """
    Compile a Luna source file to an assembly file.

    Args:
        source_path: Path to the .luna source file
        output_path: Path for the output .s assembly file
        optimize: Whether to run optimization passes
    """
    with open(source_path, 'r') as f:
        source = f.read()

    assembly = compile_source_to_asm(source, optimize)

    with open(output_path, 'w') as f:
        f.write(assembly)


def assemble_and_link(
    asm_path: str,
    output_path: str
) -> CompileResult:
    """
    Assemble and link an assembly file to an executable.

    Args:
        asm_path: Path to the .s assembly file
        output_path: Path for the output executable

    Returns:
        CompileResult with success status and any error messages
    """
    obj_path = output_path + ".o"

    try:
        # Assemble
        result = subprocess.run(
            ["as", "-o", obj_path, asm_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return CompileResult(
                success=False,
                stderr=result.stderr,
                error_message=f"Assembly failed: {result.stderr}"
            )

        # Link with gcc (to link libc)
        result = subprocess.run(
            ["gcc", "-o", output_path, obj_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return CompileResult(
                success=False,
                stderr=result.stderr,
                error_message=f"Linking failed: {result.stderr}"
            )

        return CompileResult(success=True)

    except FileNotFoundError as e:
        return CompileResult(
            success=False,
            error_message=f"Tool not found: {e}"
        )
    finally:
        # Clean up object file
        if os.path.exists(obj_path):
            os.remove(obj_path)


def compile_and_run(
    source: str,
    optimize: bool = True,
    timeout: float = 10.0
) -> CompileResult:
    """
    Compile Luna source code, assemble, link, and run it.

    Args:
        source: Luna source code string
        optimize: Whether to run optimization passes
        timeout: Timeout in seconds for program execution

    Returns:
        CompileResult with execution output
    """
    try:
        # Generate assembly
        assembly = compile_source_to_asm(source, optimize)
    except Exception as e:
        return CompileResult(
            success=False,
            error_message=f"Compilation failed: {str(e)}",
            assembly=""
        )

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        asm_path = os.path.join(tmpdir, "program.s")
        exe_path = os.path.join(tmpdir, "program")

        # Write assembly
        with open(asm_path, 'w') as f:
            f.write(assembly)

        # Assemble and link
        link_result = assemble_and_link(asm_path, exe_path)
        if not link_result.success:
            link_result.assembly = assembly
            return link_result

        # Run the program
        try:
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return CompileResult(
                success=True,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                assembly=assembly
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                error_message=f"Program timed out after {timeout} seconds",
                assembly=assembly
            )
        except Exception as e:
            return CompileResult(
                success=False,
                error_message=f"Execution failed: {str(e)}",
                assembly=assembly
            )


def compile_file_and_run(
    source_path: str,
    optimize: bool = True,
    timeout: float = 10.0
) -> CompileResult:
    """
    Compile a Luna source file, assemble, link, and run it.

    Args:
        source_path: Path to the .luna source file
        optimize: Whether to run optimization passes
        timeout: Timeout in seconds for program execution

    Returns:
        CompileResult with execution output
    """
    with open(source_path, 'r') as f:
        source = f.read()

    return compile_and_run(source, optimize, timeout)


def print_assembly(source: str, optimize: bool = True) -> None:
    """
    Print the generated assembly for Luna source code.

    Useful for debugging and learning.

    Args:
        source: Luna source code string
        optimize: Whether to run optimization passes
    """
    assembly = compile_source_to_asm(source, optimize)
    print(assembly)
