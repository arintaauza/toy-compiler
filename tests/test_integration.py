"""
Integration tests for the Luna compiler.

Tests the complete compilation pipeline from source to execution,
including all example programs and both backends.
"""

import pytest
import subprocess
import sys
from pathlib import Path

from src.codegen import compile_and_run, compile_and_run_llvm


# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


# =============================================================================
# Example Program Tests
# =============================================================================

class TestExamplePrograms:
    """Test that all example programs compile and run correctly."""

    def test_hello_world(self):
        """Test hello_world.luna example."""
        source = (EXAMPLES_DIR / "hello_world.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert "Hello, World!" in result.stdout
        assert result.return_code == 0

    def test_fibonacci(self):
        """Test fibonacci.luna example."""
        source = (EXAMPLES_DIR / "fibonacci.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        # First 10 fibonacci numbers: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34
        assert "0" in result.stdout
        assert "1" in result.stdout
        assert "34" in result.stdout

    def test_factorial(self):
        """Test factorial.luna example."""
        source = (EXAMPLES_DIR / "factorial.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        assert "120" in result.stdout  # 5! = 120

    def test_fizzbuzz(self):
        """Test fizzbuzz.luna example."""
        source = (EXAMPLES_DIR / "fizzbuzz.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        assert "FizzBuzz" in result.stdout
        assert "Fizz" in result.stdout
        assert "Buzz" in result.stdout

    def test_prime_checker(self):
        """Test prime_checker.luna example."""
        source = (EXAMPLES_DIR / "prime_checker.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        # Should contain some primes
        assert "2" in result.stdout
        assert "3" in result.stdout
        assert "47" in result.stdout

    def test_gcd(self):
        """Test gcd.luna example."""
        source = (EXAMPLES_DIR / "gcd.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        assert "6" in result.stdout   # GCD of 48 and 18
        assert "144" in result.stdout  # LCM of 48 and 18

    def test_power(self):
        """Test power.luna example."""
        source = (EXAMPLES_DIR / "power.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        assert "1024" in result.stdout  # 2^10
        assert "243" in result.stdout   # 3^5
        assert "125" in result.stdout   # 5^3

    def test_sum_of_digits(self):
        """Test sum_of_digits.luna example."""
        source = (EXAMPLES_DIR / "sum_of_digits.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        assert "15" in result.stdout  # 1+2+3+4+5 = 15
        assert "5" in result.stdout   # 5 digits

    def test_collatz(self):
        """Test collatz.luna example."""
        source = (EXAMPLES_DIR / "collatz.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0

    def test_triangle(self):
        """Test triangle.luna example."""
        source = (EXAMPLES_DIR / "triangle.luna").read_text()
        result = compile_and_run(source)

        assert result.success
        assert result.return_code == 0
        # First few triangle numbers: 1, 3, 6, 10, 15, 21, 28
        assert "1" in result.stdout
        assert "3" in result.stdout
        assert "6" in result.stdout


# =============================================================================
# LLVM Backend Tests
# =============================================================================

class TestLLVMBackend:
    """Test examples with LLVM backend."""

    def test_hello_world_llvm(self):
        """Test hello_world.luna with LLVM backend."""
        source = (EXAMPLES_DIR / "hello_world.luna").read_text()
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 0

    def test_fibonacci_llvm(self):
        """Test fibonacci calculation with LLVM."""
        source = """
        fn fib(n: int) -> int {
            if n <= 1 { return n; }
            return fib(n - 1) + fib(n - 2);
        }
        fn main() -> int {
            return fib(10);
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 55

    def test_factorial_llvm(self):
        """Test factorial with LLVM backend."""
        source = """
        fn factorial(n: int) -> int {
            if n <= 1 { return 1; }
            return n * factorial(n - 1);
        }
        fn main() -> int {
            return factorial(6);
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 720  # 6!

    def test_gcd_llvm(self):
        """Test GCD with LLVM backend."""
        source = """
        fn gcd(a: int, b: int) -> int {
            if b == 0 { return a; }
            return gcd(b, a % b);
        }
        fn main() -> int {
            return gcd(48, 18);
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 6

    def test_power_llvm(self):
        """Test power calculation with LLVM."""
        source = """
        fn power(base: int, exp: int) -> int {
            if exp == 0 { return 1; }
            if exp == 1 { return base; }
            let half: int = power(base, exp / 2);
            if exp % 2 == 0 {
                return half * half;
            } else {
                return base * half * half;
            }
        }
        fn main() -> int {
            return power(2, 10);
        }
        """
        result = compile_and_run_llvm(source)

        assert result.success
        assert result.return_value == 1024


# =============================================================================
# Backend Comparison Tests
# =============================================================================

class TestBackendComparison:
    """Ensure both backends produce the same results."""

    @pytest.mark.parametrize("source,expected", [
        ("fn main() -> int { return 42; }", 42),
        ("fn main() -> int { return 10 + 5; }", 15),
        ("fn main() -> int { return 100 - 30; }", 70),
        ("fn main() -> int { return 7 * 8; }", 56),
        ("fn main() -> int { return 100 / 5; }", 20),
        ("fn main() -> int { return 17 % 5; }", 2),
        ("fn main() -> int { if 5 > 3 { return 1; } return 0; }", 1),
        ("fn main() -> int { if 3 > 5 { return 1; } return 0; }", 0),
    ])
    def test_simple_expressions(self, source, expected):
        """Test that simple expressions produce same result in both backends."""
        x86_result = compile_and_run(source)
        llvm_result = compile_and_run_llvm(source)

        assert x86_result.success
        assert llvm_result.success
        # Note: x86 return codes are unsigned 0-255, LLVM returns full int
        assert x86_result.return_code == expected
        assert llvm_result.return_value == expected

    def test_negation_llvm(self):
        """Test negation using LLVM backend (full int return)."""
        source = "fn main() -> int { return -42; }"
        result = compile_and_run_llvm(source)
        assert result.success
        assert result.return_value == -42

    def test_recursive_function_both_backends(self):
        """Test recursive function produces same result."""
        source = """
        fn sum_to(n: int) -> int {
            if n <= 0 { return 0; }
            return n + sum_to(n - 1);
        }
        fn main() -> int {
            return sum_to(10);
        }
        """
        x86_result = compile_and_run(source)
        llvm_result = compile_and_run_llvm(source)

        assert x86_result.success
        assert llvm_result.success
        # sum from 1 to 10 = 55
        assert x86_result.return_code == 55
        assert llvm_result.return_value == 55

    def test_while_loop_both_backends(self):
        """Test while loop produces same result."""
        source = """
        fn main() -> int {
            let sum: int = 0;
            let i: int = 1;
            while i <= 10 {
                sum = sum + i;
                i = i + 1;
            }
            return sum;
        }
        """
        x86_result = compile_and_run(source)
        llvm_result = compile_and_run_llvm(source)

        assert x86_result.success
        assert llvm_result.success
        assert x86_result.return_code == 55
        assert llvm_result.return_value == 55


# =============================================================================
# Optimization Tests
# =============================================================================

class TestOptimizations:
    """Test that optimizations don't break correctness."""

    def test_constant_folding_correctness(self):
        """Ensure constant folding produces correct results."""
        source = """
        fn main() -> int {
            let x: int = 10 + 20;
            let y: int = x * 2;
            return y - 5;
        }
        """
        # With optimizations
        opt_result = compile_and_run(source, optimize=True)
        # Without optimizations
        no_opt_result = compile_and_run(source, optimize=False)

        assert opt_result.success
        assert no_opt_result.success
        assert opt_result.return_code == no_opt_result.return_code
        assert opt_result.return_code == 55  # (10+20)*2 - 5 = 55

    def test_dead_code_elimination_correctness(self):
        """Ensure DCE doesn't remove needed code."""
        source = """
        fn main() -> int {
            let x: int = 10;
            let unused: int = 999;  // Should be eliminated
            let y: int = x + 5;
            return y;
        }
        """
        result = compile_and_run(source, optimize=True)

        assert result.success
        assert result.return_code == 15


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    """Test the luna.py CLI tool."""

    @pytest.fixture
    def luna_py(self):
        """Path to luna.py."""
        return Path(__file__).parent.parent / "luna.py"

    def test_cli_help(self, luna_py):
        """Test --help option."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Luna Programming Language Compiler" in result.stdout

    def test_cli_version(self, luna_py):
        """Test --version option."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Luna Compiler" in result.stdout

    def test_cli_run_example(self, luna_py):
        """Test running an example program."""
        result = subprocess.run(
            [sys.executable, str(luna_py), str(EXAMPLES_DIR / "hello_world.luna")],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "Hello, World!" in result.stdout

    def test_cli_tokens_output(self, luna_py):
        """Test --tokens option."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "--tokens", str(EXAMPLES_DIR / "hello_world.luna")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Tokens:" in result.stdout
        assert "FN" in result.stdout

    def test_cli_ir_output(self, luna_py):
        """Test --ir option."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "--ir", str(EXAMPLES_DIR / "hello_world.luna")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Intermediate Representation:" in result.stdout
        assert "FUNCTION main" in result.stdout

    def test_cli_llvm_output(self, luna_py):
        """Test --llvm option."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "--llvm", str(EXAMPLES_DIR / "hello_world.luna")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "LLVM IR:" in result.stdout
        assert "define i64" in result.stdout

    def test_cli_file_not_found(self, luna_py):
        """Test error on non-existent file."""
        result = subprocess.run(
            [sys.executable, str(luna_py), "nonexistent.luna"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "File not found" in result.stdout or "Error" in result.stdout


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test that errors are handled gracefully."""

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        source = "fn main() -> int { return }"  # Missing value
        result = compile_and_run(source)
        assert not result.success

    def test_type_error(self):
        """Test handling of type errors."""
        source = """
        fn main() -> int {
            let x: int = "hello";  // Type mismatch
            return 0;
        }
        """
        result = compile_and_run(source)
        assert not result.success

    def test_undefined_variable(self):
        """Test handling of undefined variable."""
        source = """
        fn main() -> int {
            return undefined_var;
        }
        """
        result = compile_and_run(source)
        assert not result.success

    def test_undefined_function(self):
        """Test handling of undefined function call."""
        source = """
        fn main() -> int {
            return unknown_func();
        }
        """
        result = compile_and_run(source)
        assert not result.success
