"""
Code Generation module for the Toy compiler.

This module provides code generation from SSA-based IR to:
- x86-64 assembly (direct generation)
- LLVM IR (via llvmlite for optimized native code)

Components:
- stack_frame: Stack frame layout and variable allocation
- x86_64_codegen: Main code generator for x86-64 assembly
- asm_emitter: High-level compilation functions for x86-64
- llvm_codegen: LLVM IR code generator
- llvm_emitter: High-level compilation functions for LLVM

Usage (x86-64):
    from src.codegen import compile_and_run, compile_to_asm

    # Compile and run Toy source code
    result = compile_and_run('''
        fn main() -> int {
            print(42);
            return 0;
        }
    ''')
    print(result.stdout)  # "42"

Usage (LLVM):
    from src.codegen import compile_to_llvm_ir, compile_and_run_llvm

    # Generate LLVM IR
    llvm_ir = compile_to_llvm_ir(source)
    print(llvm_ir)

    # Compile and run with LLVM JIT
    result = compile_and_run_llvm(source)
    print(result.return_value)
"""

from src.codegen.stack_frame import (
    StackSlot,
    StackFrame,
    StackFrameBuilder,
)

from src.codegen.x86_64_codegen import (
    X86_64CodeGenerator,
    generate_assembly,
)

from src.codegen.asm_emitter import (
    CompileResult,
    compile_source_to_asm,
    compile_to_asm,
    assemble_and_link,
    compile_and_run,
    compile_file_and_run,
    print_assembly,
)

from src.codegen.llvm_codegen import (
    LLVMCodeGenerator,
    generate_llvm_ir,
)

from src.codegen.llvm_emitter import (
    LLVMCompileResult,
    compile_to_llvm_ir,
    compile_and_run_llvm,
    compile_to_object,
    get_llvm_target_info,
    optimize_llvm_ir,
    print_llvm_ir,
    LLVMJITEngine,
)


__all__ = [
    # Stack frame
    "StackSlot",
    "StackFrame",
    "StackFrameBuilder",

    # Code generator
    "X86_64CodeGenerator",
    "generate_assembly",

    # High-level API (x86-64)
    "CompileResult",
    "compile_source_to_asm",
    "compile_to_asm",
    "assemble_and_link",
    "compile_and_run",
    "compile_file_and_run",
    "print_assembly",

    # LLVM code generator
    "LLVMCodeGenerator",
    "generate_llvm_ir",

    # LLVM high-level API
    "LLVMCompileResult",
    "compile_to_llvm_ir",
    "compile_and_run_llvm",
    "compile_to_object",
    "get_llvm_target_info",
    "optimize_llvm_ir",
    "print_llvm_ir",
    "LLVMJITEngine",
]
