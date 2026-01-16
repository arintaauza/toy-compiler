"""
LLVM Emitter for the Luna compiler.

High-level API for compiling Luna source code to LLVM IR and executing it.

Features:
- Compile Luna source to LLVM IR text
- JIT compilation and execution via MCJIT
- Object file generation for native binaries
- Integration with Luna's optimization passes
"""

from typing import Optional, Any
from dataclasses import dataclass
import ctypes

from llvmlite import ir, binding

from src.ir import generate_ir_from_source
from src.ir.optimizations import create_default_pass_manager
from src.codegen.llvm_codegen import LLVMCodeGenerator, generate_llvm_ir


@dataclass
class LLVMCompileResult:
    """Result of LLVM compilation."""
    success: bool
    llvm_ir: str = ""
    return_value: Optional[int] = None
    error: Optional[str] = None
    stdout: str = ""


def compile_to_llvm_ir(source: str, optimize: bool = True) -> str:
    """
    Compile Luna source code to LLVM IR text.

    Args:
        source: Luna source code
        optimize: Whether to run Luna optimization passes first

    Returns:
        LLVM IR as a string

    Raises:
        Exception: If compilation fails
    """
    # Generate IR from source (includes lexing, parsing, semantic analysis)
    ir_module = generate_ir_from_source(source)

    # Optimization (Luna-level)
    if optimize:
        pass_manager = create_default_pass_manager()
        pass_manager.run_until_fixed_point(ir_module)

    # LLVM IR Generation
    llvm_module = generate_llvm_ir(ir_module)

    return str(llvm_module)


def compile_and_run_llvm(source: str, optimize: bool = True) -> LLVMCompileResult:
    """
    Compile Luna source and execute using LLVM JIT.

    Args:
        source: Luna source code
        optimize: Whether to run optimization passes

    Returns:
        LLVMCompileResult with execution results
    """
    try:
        # Generate LLVM IR
        llvm_ir_str = compile_to_llvm_ir(source, optimize)

        # Parse the LLVM IR
        llvm_module = binding.parse_assembly(llvm_ir_str)
        llvm_module.verify()

        # Create target machine
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()

        # Create execution engine with MCJIT
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)

        # Add module to engine
        engine.add_module(llvm_module)
        engine.finalize_object()

        # Get main function pointer
        main_ptr = engine.get_function_address("main")

        if main_ptr == 0:
            return LLVMCompileResult(
                success=False,
                llvm_ir=llvm_ir_str,
                error="Function 'main' not found"
            )

        # Create ctypes function and call it
        main_func = ctypes.CFUNCTYPE(ctypes.c_int64)(main_ptr)
        return_value = main_func()

        return LLVMCompileResult(
            success=True,
            llvm_ir=llvm_ir_str,
            return_value=return_value
        )

    except Exception as e:
        return LLVMCompileResult(
            success=False,
            error=str(e)
        )


def compile_to_object(source: str, output_path: str, optimize: bool = True) -> bool:
    """
    Compile Luna source to a native object file.

    Args:
        source: Luna source code
        output_path: Path for the output .o file
        optimize: Whether to run optimization passes

    Returns:
        True if compilation succeeded
    """
    try:
        # Generate LLVM IR
        llvm_ir_str = compile_to_llvm_ir(source, optimize)

        # Parse and verify
        llvm_module = binding.parse_assembly(llvm_ir_str)
        llvm_module.verify()

        # Create target machine
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()

        # Generate object code
        object_code = target_machine.emit_object(llvm_module)

        # Write to file
        with open(output_path, 'wb') as f:
            f.write(object_code)

        return True

    except Exception as e:
        print(f"Compilation error: {e}")
        return False


def get_llvm_target_info() -> dict:
    """
    Get information about the LLVM target.

    Returns:
        Dictionary with target information
    """
    return {
        "triple": binding.get_default_triple(),
        "host_cpu": binding.get_host_cpu_name(),
        "host_features": binding.get_host_cpu_features().flatten(),
    }


def optimize_llvm_ir(llvm_ir_str: str, level: int = 2) -> str:
    """
    Run LLVM optimization passes on LLVM IR.

    Args:
        llvm_ir_str: LLVM IR as text
        level: Optimization level (0-3)

    Returns:
        Optimized LLVM IR as text
    """
    # Parse the module
    llvm_module = binding.parse_assembly(llvm_ir_str)
    llvm_module.verify()

    # Create target machine for target-specific optimizations
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine(opt=level)

    # Create pass manager with optimization level
    pmb = binding.PassManagerBuilder()
    pmb.opt_level = level

    # Module pass manager
    pm = binding.ModulePassManager()
    pmb.populate(pm)

    # Run passes
    pm.run(llvm_module)

    return str(llvm_module)


def print_llvm_ir(source: str, optimize: bool = False) -> None:
    """
    Print LLVM IR for Luna source code.

    Args:
        source: Luna source code
        optimize: Whether to run optimization passes
    """
    llvm_ir = compile_to_llvm_ir(source, optimize)
    print(llvm_ir)


class LLVMJITEngine:
    """
    Reusable JIT compilation engine for LLVM.

    Allows adding multiple modules and executing functions.
    """

    def __init__(self):
        """Initialize the JIT engine."""
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        target = binding.Target.from_default_triple()
        self.target_machine = target.create_target_machine()

        # Create backing module and engine
        backing_mod = binding.parse_assembly("")
        self.engine = binding.create_mcjit_compiler(backing_mod, self.target_machine)

        self.modules = []

    def add_module(self, llvm_ir_str: str) -> None:
        """
        Add an LLVM IR module to the engine.

        Args:
            llvm_ir_str: LLVM IR as text
        """
        llvm_module = binding.parse_assembly(llvm_ir_str)
        llvm_module.verify()
        self.engine.add_module(llvm_module)
        self.modules.append(llvm_module)

    def finalize(self) -> None:
        """Finalize the engine for execution."""
        self.engine.finalize_object()

    def get_function_ptr(self, name: str) -> int:
        """
        Get the address of a function.

        Args:
            name: Function name

        Returns:
            Function pointer as integer
        """
        return self.engine.get_function_address(name)

    def call_int_function(self, name: str, *args) -> int:
        """
        Call a function that returns an integer.

        Args:
            name: Function name
            *args: Function arguments

        Returns:
            Integer return value
        """
        ptr = self.get_function_ptr(name)
        if ptr == 0:
            raise ValueError(f"Function '{name}' not found")

        # Build argument types
        arg_types = [ctypes.c_int64] * len(args)
        func_type = ctypes.CFUNCTYPE(ctypes.c_int64, *arg_types)
        func = func_type(ptr)

        return func(*args)

    def compile_and_call_main(self, source: str, optimize: bool = True) -> int:
        """
        Compile Luna source and call main().

        Args:
            source: Luna source code
            optimize: Whether to optimize

        Returns:
            Return value from main()
        """
        llvm_ir = compile_to_llvm_ir(source, optimize)
        self.add_module(llvm_ir)
        self.finalize()
        return self.call_int_function("main")
