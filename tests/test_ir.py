"""
Tests for the IR (Intermediate Representation) module.

Tests cover:
- IR instruction creation and formatting
- SSA variable management
- CFG construction
- IR generation from AST
- Phi function insertion
- Control flow handling
"""

import pytest
from src.ir.instructions import (
    IRType,
    IRValue,
    OpCode,
    make_constant,
    BinaryOp,
    UnaryOp,
    Copy,
    LoadConst,
    Jump,
    Branch,
    Phi,
    PhiSource,
    Call,
    Return,
    BasicBlock,
    IRParameter,
    IRFunction,
    IRModule,
)
from src.ir.ssa import SSANameGenerator, luna_type_to_ir_type
from src.ir.cfg import CFG, CFGBuilder
from src.ir.ir_generator import IRGenerator, generate_ir
from src.ir.ir_printer import IRPrinter, format_ir
from src.parser.parser import parse_source


# =============================================================================
# IRValue Tests
# =============================================================================

class TestIRValue:
    """Tests for IRValue class."""

    def test_create_variable(self):
        """Test creating a variable IRValue."""
        v = IRValue(name="x", version=0, ir_type=IRType.INT)
        assert v.name == "x"
        assert v.version == 0
        assert v.ir_type == IRType.INT
        assert not v.is_constant
        assert str(v) == "x_0"

    def test_create_versioned_variable(self):
        """Test creating versioned variables."""
        v1 = IRValue(name="x", version=0, ir_type=IRType.INT)
        v2 = IRValue(name="x", version=1, ir_type=IRType.INT)
        v3 = IRValue(name="x", version=2, ir_type=IRType.INT)

        assert str(v1) == "x_0"
        assert str(v2) == "x_1"
        assert str(v3) == "x_2"

    def test_create_constant(self):
        """Test creating constant IRValues."""
        c = make_constant(42, IRType.INT)
        assert c.is_constant
        assert c.constant_value == 42
        assert str(c) == "42"

    def test_constant_types(self):
        """Test different constant types."""
        int_c = make_constant(42, IRType.INT)
        float_c = make_constant(3.14, IRType.FLOAT)
        bool_c = make_constant(True, IRType.BOOL)
        str_c = make_constant("hello", IRType.STRING)

        assert str(int_c) == "42"
        assert str(float_c) == "3.14"
        assert str(bool_c) == "true"
        assert str(str_c) == '"hello"'

    def test_value_equality(self):
        """Test IRValue equality."""
        v1 = IRValue(name="x", version=0, ir_type=IRType.INT)
        v2 = IRValue(name="x", version=0, ir_type=IRType.INT)
        v3 = IRValue(name="x", version=1, ir_type=IRType.INT)

        assert v1 == v2
        assert v1 != v3


# =============================================================================
# IR Instruction Tests
# =============================================================================

class TestIRInstructions:
    """Tests for IR instruction classes."""

    def test_binary_op(self):
        """Test BinaryOp instruction."""
        dest = IRValue("t", 0, IRType.INT)
        left = IRValue("a", 0, IRType.INT)
        right = IRValue("b", 0, IRType.INT)

        instr = BinaryOp(dest=dest, op=OpCode.ADD, left=left, right=right)

        assert instr.dest == dest
        assert instr.op == OpCode.ADD
        assert instr.left == left
        assert instr.right == right
        assert "t_0 = a_0 + b_0" in str(instr)

    def test_binary_op_uses_and_defs(self):
        """Test BinaryOp uses and definitions."""
        dest = IRValue("t", 0, IRType.INT)
        left = IRValue("a", 0, IRType.INT)
        right = IRValue("b", 0, IRType.INT)

        instr = BinaryOp(dest=dest, op=OpCode.ADD, left=left, right=right)

        assert instr.get_def() == dest
        assert left in instr.get_uses()
        assert right in instr.get_uses()

    def test_unary_op(self):
        """Test UnaryOp instruction."""
        dest = IRValue("t", 0, IRType.INT)
        operand = IRValue("x", 0, IRType.INT)

        instr = UnaryOp(dest=dest, op=OpCode.NEG, operand=operand)

        assert "t_0 = neg x_0" in str(instr)

    def test_copy(self):
        """Test Copy instruction."""
        dest = IRValue("x", 1, IRType.INT)
        source = IRValue("t", 0, IRType.INT)

        instr = Copy(dest=dest, source=source)

        assert "x_1 = t_0" in str(instr)

    def test_load_const(self):
        """Test LoadConst instruction."""
        dest = IRValue("t", 0, IRType.INT)
        instr = LoadConst(dest=dest, value=42, value_type=IRType.INT)

        assert "t_0 = 42" in str(instr)

    def test_load_const_string(self):
        """Test LoadConst with string."""
        dest = IRValue("t", 0, IRType.STRING)
        instr = LoadConst(dest=dest, value="hello", value_type=IRType.STRING)

        assert 't_0 = "hello"' in str(instr)

    def test_jump(self):
        """Test Jump instruction."""
        instr = Jump(target="B1")
        assert "jump B1" in str(instr)

    def test_branch(self):
        """Test Branch instruction."""
        cond = IRValue("t", 0, IRType.BOOL)
        instr = Branch(condition=cond, true_target="B1", false_target="B2")

        assert "branch t_0, B1, B2" in str(instr)

    def test_phi(self):
        """Test Phi instruction."""
        dest = IRValue("x", 2, IRType.INT)
        sources = [
            PhiSource(IRValue("x", 0, IRType.INT), "B1"),
            PhiSource(IRValue("x", 1, IRType.INT), "B2"),
        ]
        instr = Phi(dest=dest, sources=sources)

        result = str(instr)
        assert "x_2 = phi" in result
        assert "[x_0, B1]" in result
        assert "[x_1, B2]" in result

    def test_call_with_return(self):
        """Test Call instruction with return value."""
        dest = IRValue("t", 0, IRType.INT)
        args = [IRValue("a", 0, IRType.INT), IRValue("b", 0, IRType.INT)]
        instr = Call(dest=dest, function="add", arguments=args)

        assert "t_0 = call add(a_0, b_0)" in str(instr)

    def test_call_void(self):
        """Test Call instruction for void function."""
        args = [IRValue("x", 0, IRType.INT)]
        instr = Call(dest=None, function="print", arguments=args)

        assert "call print(x_0)" in str(instr)

    def test_return_value(self):
        """Test Return instruction with value."""
        value = IRValue("x", 0, IRType.INT)
        instr = Return(value=value)

        assert "return x_0" in str(instr)

    def test_return_void(self):
        """Test Return instruction without value."""
        instr = Return(value=None)
        assert str(instr).strip() == "return"


# =============================================================================
# BasicBlock Tests
# =============================================================================

class TestBasicBlock:
    """Tests for BasicBlock class."""

    def test_create_block(self):
        """Test creating a basic block."""
        block = BasicBlock(label="B0")
        assert block.label == "B0"
        assert block.instructions == []
        assert block.predecessors == []
        assert block.successors == []

    def test_add_instruction(self):
        """Test adding instructions to a block."""
        block = BasicBlock(label="B0")
        dest = IRValue("t", 0, IRType.INT)
        instr = LoadConst(dest=dest, value=42, value_type=IRType.INT)

        block.add_instruction(instr)

        assert len(block.instructions) == 1
        assert block.instructions[0] == instr

    def test_predecessors_successors(self):
        """Test predecessor/successor tracking."""
        block = BasicBlock(label="B0")
        block.add_predecessor("entry")
        block.add_successor("B1")
        block.add_successor("B2")

        assert "entry" in block.predecessors
        assert "B1" in block.successors
        assert "B2" in block.successors

    def test_terminator_detection(self):
        """Test terminator detection."""
        block = BasicBlock(label="B0")
        assert not block.is_terminated()

        block.add_instruction(LoadConst(
            dest=IRValue("t", 0, IRType.INT),
            value=42,
            value_type=IRType.INT
        ))
        assert not block.is_terminated()

        block.add_instruction(Return(value=IRValue("t", 0, IRType.INT)))
        assert block.is_terminated()

    def test_get_phi_instructions(self):
        """Test getting phi instructions from block."""
        block = BasicBlock(label="B0")

        phi = Phi(
            dest=IRValue("x", 2, IRType.INT),
            sources=[PhiSource(IRValue("x", 0, IRType.INT), "B1")]
        )
        block.add_instruction(phi)
        block.add_instruction(LoadConst(
            dest=IRValue("t", 0, IRType.INT),
            value=42,
            value_type=IRType.INT
        ))

        phis = block.get_phi_instructions()
        assert len(phis) == 1
        assert phis[0] == phi


# =============================================================================
# SSA Name Generator Tests
# =============================================================================

class TestSSANameGenerator:
    """Tests for SSA variable versioning."""

    def test_new_variable(self):
        """Test creating new variables."""
        gen = SSANameGenerator()

        x = gen.new_variable("x", IRType.INT)
        assert x.name == "x"
        assert x.version == 0

        y = gen.new_variable("y", IRType.FLOAT)
        assert y.name == "y"
        assert y.version == 0

    def test_new_version(self):
        """Test creating new versions of variables."""
        gen = SSANameGenerator()

        x0 = gen.new_variable("x", IRType.INT)
        assert x0.version == 0

        x1 = gen.new_version("x")
        assert x1.version == 1

        x2 = gen.new_version("x")
        assert x2.version == 2

    def test_get_current(self):
        """Test getting current version."""
        gen = SSANameGenerator()

        gen.new_variable("x", IRType.INT)
        gen.new_version("x")

        current = gen.get_current("x")
        assert current.version == 1

    def test_new_temp(self):
        """Test temporary variable generation."""
        gen = SSANameGenerator()

        t0 = gen.new_temp(IRType.INT)
        t1 = gen.new_temp(IRType.INT)
        t2 = gen.new_temp(IRType.BOOL)

        assert t0.name == "t"
        assert t0.version == 0
        assert t1.version == 1
        assert t2.version == 2

    def test_new_block_label(self):
        """Test block label generation."""
        gen = SSANameGenerator()

        b0 = gen.new_block_label()
        b1 = gen.new_block_label()
        b2 = gen.new_block_label("loop")

        assert b0 == "B0"
        assert b1 == "B1"
        assert b2 == "loop2"

    def test_scope_snapshot(self):
        """Test scope snapshot and restore."""
        gen = SSANameGenerator()

        gen.new_variable("x", IRType.INT)
        gen.new_version("x")  # x is now version 1

        snapshot = gen.get_scope_snapshot()

        gen.new_version("x")  # x is now version 2
        assert gen.get_current("x").version == 2

        gen.restore_scope(snapshot)
        assert gen.get_current("x").version == 1


# =============================================================================
# CFG Tests
# =============================================================================

class TestCFG:
    """Tests for Control Flow Graph."""

    def test_create_cfg(self):
        """Test creating a CFG."""
        cfg = CFG()
        cfg.entry = "B0"

        b0 = BasicBlock(label="B0")
        b1 = BasicBlock(label="B1")

        cfg.add_block(b0)
        cfg.add_block(b1)

        assert "B0" in cfg.blocks
        assert "B1" in cfg.blocks

    def test_add_edge(self):
        """Test adding edges to CFG."""
        cfg = CFG()

        b0 = BasicBlock(label="B0")
        b1 = BasicBlock(label="B1")
        cfg.add_block(b0)
        cfg.add_block(b1)

        cfg.add_edge("B0", "B1")

        assert "B1" in cfg.get_successors("B0")
        assert "B0" in cfg.get_predecessors("B1")

    def test_compute_edges_from_terminators(self):
        """Test computing edges from terminator instructions."""
        cfg = CFG()

        b0 = BasicBlock(label="B0")
        b1 = BasicBlock(label="B1")
        b2 = BasicBlock(label="B2")

        b0.add_instruction(Branch(
            condition=IRValue("t", 0, IRType.BOOL),
            true_target="B1",
            false_target="B2"
        ))
        b1.add_instruction(Return(value=IRValue("x", 0, IRType.INT)))
        b2.add_instruction(Return(value=IRValue("y", 0, IRType.INT)))

        cfg.add_block(b0)
        cfg.add_block(b1)
        cfg.add_block(b2)
        cfg.entry = "B0"

        cfg.compute_edges_from_terminators()

        assert "B1" in cfg.get_successors("B0")
        assert "B2" in cfg.get_successors("B0")
        assert "B1" in cfg.exit_blocks
        assert "B2" in cfg.exit_blocks


class TestCFGBuilder:
    """Tests for CFG builder."""

    def test_builder_new_block(self):
        """Test creating blocks with builder."""
        builder = CFGBuilder()

        b0 = builder.new_block()
        b1 = builder.new_block()
        b2 = builder.new_block("loop")

        assert b0.label == "B0"
        assert b1.label == "B1"
        assert b2.label == "loop2"

    def test_builder_emit(self):
        """Test emitting instructions."""
        builder = CFGBuilder()

        block = builder.new_block()
        builder.position_at_end(block)

        dest = IRValue("t", 0, IRType.INT)
        builder.emit(LoadConst(dest=dest, value=42, value_type=IRType.INT))

        assert len(block.instructions) == 1

    def test_builder_emit_jump(self):
        """Test emitting jump with edge."""
        builder = CFGBuilder()

        b0 = builder.new_block()
        b1 = builder.new_block()

        builder.position_at_end(b0)
        builder.emit_jump("B1")

        cfg = builder.finalize()
        assert "B1" in cfg.get_successors("B0")


# =============================================================================
# IR Generator Tests
# =============================================================================

class TestIRGenerator:
    """Tests for IR generation from AST."""

    def test_simple_function(self):
        """Test generating IR for a simple function."""
        source = """
        fn main() -> int {
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        assert "main" in module.functions
        func = module.functions["main"]
        assert func.return_type == IRType.INT

    def test_variable_declaration(self):
        """Test generating IR for variable declarations."""
        source = """
        fn main() -> int {
            let x: int = 42;
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        # Should have instructions for loading 42 and copying to x
        entry = func.blocks[func.entry_block]
        assert len(entry.instructions) > 0

    def test_binary_expression(self):
        """Test generating IR for binary expressions."""
        source = """
        fn main() -> int {
            let x: int = 1 + 2;
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        ir_text = str(func)
        assert "+" in ir_text

    def test_function_parameters(self):
        """Test generating IR for function with parameters."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        assert "add" in module.functions
        add_func = module.functions["add"]
        assert len(add_func.parameters) == 2

    def test_if_statement(self):
        """Test generating IR for if statements."""
        source = """
        fn main() -> int {
            let x: int = 0;
            if true {
                x = 1;
            }
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        # Should have multiple blocks (entry, then, merge)
        assert len(func.blocks) >= 2

    def test_if_else_statement(self):
        """Test generating IR for if-else statements."""
        source = """
        fn main() -> int {
            let x: int = 0;
            if true {
                x = 1;
            } else {
                x = 2;
            }
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        # Should have multiple blocks
        assert len(func.blocks) >= 3

    def test_while_loop(self):
        """Test generating IR for while loops."""
        source = """
        fn main() -> int {
            let i: int = 0;
            while i < 10 {
                i = i + 1;
            }
            return i;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        # Should have loop_header, loop_body, and loop_exit blocks
        assert len(func.blocks) >= 3

    def test_function_call(self):
        """Test generating IR for function calls."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }

        fn main() -> int {
            let result: int = add(1, 2);
            return result;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        assert "call add" in ir_text

    def test_print_call(self):
        """Test generating IR for print calls."""
        source = """
        fn main() -> int {
            print(42);
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        assert "call print" in ir_text

    def test_unary_operators(self):
        """Test generating IR for unary operators."""
        source = """
        fn main() -> int {
            let x: int = -5;
            let b: bool = !true;
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        assert "neg" in ir_text
        assert "not" in ir_text

    def test_comparison_operators(self):
        """Test generating IR for comparison operators."""
        source = """
        fn main() -> int {
            let a: bool = 1 < 2;
            let b: bool = 1 > 2;
            let c: bool = 1 == 2;
            let d: bool = 1 != 2;
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        assert "<" in ir_text
        assert ">" in ir_text
        assert "==" in ir_text
        assert "!=" in ir_text


# =============================================================================
# SSA Property Tests
# =============================================================================

class TestSSAProperties:
    """Tests for SSA form properties."""

    def test_single_assignment(self):
        """Test that each variable is assigned exactly once per version."""
        source = """
        fn main() -> int {
            let x: int = 1;
            x = 2;
            x = 3;
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        # Should see x_0, x_1, x_2 (different versions)
        assert "x_0" in ir_text
        assert "x_1" in ir_text

    def test_phi_functions_in_if(self):
        """Test phi functions are generated for if-else merge."""
        source = """
        fn main() -> int {
            let x: int = 0;
            if true {
                x = 1;
            } else {
                x = 2;
            }
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        # Should have phi function for x at merge point
        assert "phi" in ir_text


# =============================================================================
# IR Printer Tests
# =============================================================================

class TestIRPrinter:
    """Tests for IR pretty printing."""

    def test_format_module(self):
        """Test formatting a module."""
        source = """
        fn main() -> int {
            return 42;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        printer = IRPrinter()
        output = printer.format_module(module)

        assert "Module:" in output
        assert "FUNCTION main" in output

    def test_format_with_blocks(self):
        """Test formatting shows block structure."""
        source = """
        fn main() -> int {
            if true {
                return 1;
            }
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        output = format_ir(module)

        assert "entry" in output.lower() or "B0" in output

    def test_dot_output(self):
        """Test DOT format output."""
        source = """
        fn main() -> int {
            let x: int = 0;
            if true {
                x = 1;
            }
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        from src.ir.ir_printer import format_function_dot
        dot = format_function_dot(module.functions["main"])

        assert "digraph" in dot
        assert "->" in dot  # Edges


# =============================================================================
# Integration Tests
# =============================================================================

class TestIRIntegration:
    """Integration tests for full IR generation pipeline."""

    def test_fibonacci(self):
        """Test IR generation for fibonacci-like code."""
        source = """
        fn main() -> int {
            let a: int = 0;
            let b: int = 1;
            let i: int = 0;
            while i < 10 {
                let temp: int = a + b;
                a = b;
                b = temp;
                i = i + 1;
            }
            return a;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        assert "main" in module.functions
        func = module.functions["main"]

        # Should have loop structure
        assert len(func.blocks) >= 3

        # Should have phi functions in loop header
        ir_text = str(func)
        assert "phi" in ir_text

    def test_multiple_functions(self):
        """Test IR generation with multiple functions."""
        source = """
        fn square(n: int) -> int {
            return n * n;
        }

        fn main() -> int {
            let x: int = square(5);
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        assert len(module.functions) == 2
        assert "square" in module.functions
        assert "main" in module.functions

    def test_nested_if(self):
        """Test IR generation for nested if statements."""
        source = """
        fn main() -> int {
            let x: int = 0;
            if true {
                if true {
                    x = 1;
                } else {
                    x = 2;
                }
            } else {
                x = 3;
            }
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        # Should have many blocks for nested structure
        assert len(func.blocks) >= 4

    def test_logical_operators(self):
        """Test IR generation for logical operators."""
        source = """
        fn main() -> int {
            let a: bool = true && false;
            let b: bool = true || false;
            if a && b {
                return 1;
            }
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        ir_text = str(module)
        assert "and" in ir_text
        assert "or" in ir_text


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestIREdgeCases:
    """Tests for edge cases in IR generation."""

    def test_empty_function(self):
        """Test IR generation for function with no statements."""
        source = """
        fn main() -> int {
            return 0;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        func = module.functions["main"]
        assert len(func.blocks) >= 1

    def test_deeply_nested_expressions(self):
        """Test IR generation for deeply nested expressions."""
        source = """
        fn main() -> int {
            let x: int = ((1 + 2) * (3 + 4)) - ((5 - 6) / 1);
            return x;
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        # Should generate many temporaries
        func = module.functions["main"]
        ir_text = str(func)
        assert "t_" in ir_text  # Temporary variables

    def test_multiple_returns(self):
        """Test IR generation with multiple return paths."""
        source = """
        fn abs(n: int) -> int {
            if n < 0 {
                return 0 - n;
            }
            return n;
        }

        fn main() -> int {
            return abs(0 - 5);
        }
        """
        program = parse_source(source)
        module = generate_ir(program)

        abs_func = module.functions["abs"]
        # Should have multiple blocks ending in return
        return_count = sum(
            1 for block in abs_func.blocks.values()
            if any(isinstance(i, Return) for i in block.instructions)
        )
        assert return_count >= 2
