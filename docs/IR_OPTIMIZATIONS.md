# IR Optimization Guide

## Overview

This document explains the IR optimization passes in detail, with algorithms, examples, and implementation strategies.

## Why Optimize IR?

Optimizations at the IR level are **language-independent** and **target-independent**:
- Work on three-address code (TAC), not source code or assembly
- Same optimizations work regardless of backend (interpreter, assembly, LLVM)
- Easy to analyze and transform (simpler than AST or assembly)

## Control Flow Graph (CFG)

Before optimizing, we need to understand program structure.

### Basic Blocks

A **basic block** is a sequence of instructions with:
- One entry point (first instruction)
- One exit point (last instruction)
- No jumps in the middle

**Example:**
```
// TAC code
L1: t0 = a + b
    t1 = t0 * 2
    x = t1
    if x < 10 goto L2
    y = 5
    goto L3
L2: y = 10
L3: return y
```

**Basic blocks:**
```
Block 1 (L1):
    t0 = a + b
    t1 = t0 * 2
    x = t1
    if x < 10 goto L2

Block 2:
    y = 5
    goto L3

Block 3 (L2):
    y = 10

Block 4 (L3):
    return y
```

### CFG Construction Algorithm

```python
def build_cfg(instructions):
    # Step 1: Identify leaders (first instruction of each block)
    leaders = {0}  # First instruction is always a leader

    for i, instr in enumerate(instructions):
        # Instruction after jump/branch is a leader
        if instr.is_jump() or instr.is_branch():
            leaders.add(i + 1)

        # Jump target is a leader
        if instr.has_target():
            target_index = find_label_index(instr.target)
            leaders.add(target_index)

    # Step 2: Create basic blocks
    leaders = sorted(leaders)
    blocks = []

    for i in range(len(leaders)):
        start = leaders[i]
        end = leaders[i + 1] if i + 1 < len(leaders) else len(instructions)
        blocks.append(BasicBlock(instructions[start:end]))

    # Step 3: Add edges
    for block in blocks:
        last_instr = block.instructions[-1]

        if last_instr.is_unconditional_jump():
            # Single successor (jump target)
            target = find_block_by_label(last_instr.target)
            block.add_successor(target)

        elif last_instr.is_conditional_branch():
            # Two successors (branch target + fall-through)
            target = find_block_by_label(last_instr.target)
            fall_through = get_next_block(block)
            block.add_successor(target)
            block.add_successor(fall_through)

        else:
            # Fall-through to next block
            next_block = get_next_block(block)
            if next_block:
                block.add_successor(next_block)

    return blocks
```

---

## Optimization 1: Constant Folding

### Goal
Evaluate constant expressions at compile time.

### Algorithm

```python
def constant_fold(instruction):
    """
    Fold constant expressions.

    Returns:
        - New instruction if folding occurred
        - None if no folding possible
    """
    if not isinstance(instruction, BinaryOp):
        return None

    # Check if both operands are constants
    if not (is_constant(instruction.left) and is_constant(instruction.right)):
        return None

    left_val = get_constant_value(instruction.left)
    right_val = get_constant_value(instruction.right)
    op = instruction.operator

    # Evaluate based on operator
    result = None

    if op == '+':
        result = left_val + right_val
    elif op == '-':
        result = left_val - right_val
    elif op == '*':
        result = left_val * right_val
    elif op == '/':
        if right_val == 0:
            return None  # Don't fold division by zero
        result = left_val / right_val
    elif op == '%':
        if right_val == 0:
            return None
        result = left_val % right_val
    elif op == '<':
        result = left_val < right_val
    elif op == '>':
        result = left_val > right_val
    elif op == '==':
        result = left_val == right_val
    elif op == '!=':
        result = left_val != right_val
    elif op == '&&':
        result = left_val and right_val
    elif op == '||':
        result = left_val or right_val

    if result is not None:
        # Replace: t1 = 2 + 3  →  t1 = 5
        return Assign(instruction.dest, Constant(result))

    return None
```

### Example

**Before:**
```
t0 = 2 + 3
t1 = t0 * 4
t2 = t1 - 10
x = t2
```

**After constant folding:**
```
t0 = 5        // 2 + 3 folded
t1 = 20       // 5 * 4 folded
t2 = 10       // 20 - 10 folded
x = 10        // Copy propagation (separate pass)
```

### Edge Cases

- **Don't fold operations that can fail**: Division/modulo by zero
- **Handle type conversions**: int + float
- **Preserve semantics**: Overflow behavior

---

## Optimization 2: Dead Code Elimination (DCE)

### Goal
Remove instructions that don't affect program output.

### Types of Dead Code

1. **Unused variable assignments**: Variable defined but never read
2. **Unreachable code**: After return/unconditional jump
3. **Dead basic blocks**: Blocks with no predecessors

### Algorithm: Liveness Analysis

```python
def dead_code_elimination(cfg):
    """
    Remove dead code using backward liveness analysis.
    """
    # Step 1: Compute live variables for each instruction
    live_out = compute_liveness(cfg)

    # Step 2: Mark live instructions
    live_instructions = set()

    for block in cfg.blocks:
        live_vars = live_out[block]

        # Traverse block backwards
        for instr in reversed(block.instructions):
            # Critical instructions are always live
            if instr.is_critical():  # return, print, function call
                live_instructions.add(instr)
                live_vars.update(instr.get_uses())
            else:
                # Instruction is live if it defines a live variable
                defined_var = instr.get_defined_var()
                if defined_var and defined_var in live_vars:
                    live_instructions.add(instr)
                    live_vars.remove(defined_var)
                    live_vars.update(instr.get_uses())

    # Step 3: Remove dead instructions
    for block in cfg.blocks:
        block.instructions = [i for i in block.instructions if i in live_instructions]

    # Step 4: Remove unreachable blocks
    reachable = compute_reachable_blocks(cfg)
    cfg.blocks = [b for b in cfg.blocks if b in reachable]
```

### Liveness Analysis

```python
def compute_liveness(cfg):
    """
    Compute live variables at the end of each block.
    Uses iterative dataflow analysis.
    """
    live_out = {block: set() for block in cfg.blocks}
    changed = True

    while changed:
        changed = False

        for block in reversed(cfg.blocks):  # Backwards
            old_live_out = live_out[block].copy()

            # live_out = union of successors' live_in
            new_live_out = set()
            for successor in block.successors:
                # live_in = use ∪ (live_out - def)
                live_in = compute_live_in(successor, live_out[successor])
                new_live_out.update(live_in)

            if new_live_out != old_live_out:
                live_out[block] = new_live_out
                changed = True

    return live_out

def compute_live_in(block, live_out):
    """
    live_in(block) = use(block) ∪ (live_out(block) - def(block))
    """
    live = live_out.copy()

    # Traverse backwards
    for instr in reversed(block.instructions):
        # Remove defined variable (kill)
        defined = instr.get_defined_var()
        if defined:
            live.discard(defined)

        # Add used variables (gen)
        live.update(instr.get_uses())

    return live
```

### Example

**Before:**
```
t0 = 5        // Dead: t0 never used
x = 10
y = x + 1     // Dead: y never used
return x
z = 20        // Unreachable
```

**After DCE:**
```
x = 10
return x
```

---

## Optimization 3: Common Subexpression Elimination (CSE)

### Goal
Avoid recomputing the same expression.

### Algorithm

```python
def common_subexpression_elimination(block):
    """
    Eliminate common subexpressions within a basic block.
    """
    # Map: expression → temporary variable
    available_exprs = {}

    new_instructions = []

    for instr in block.instructions:
        if isinstance(instr, BinaryOp):
            # Create canonical expression key
            expr_key = (instr.operator, instr.left, instr.right)

            if expr_key in available_exprs:
                # Expression already computed!
                # Replace: t1 = a + b  →  t1 = t0 (where t0 = a + b)
                previous_result = available_exprs[expr_key]
                new_instructions.append(Copy(instr.dest, previous_result))
            else:
                # First occurrence of this expression
                new_instructions.append(instr)
                available_exprs[expr_key] = instr.dest

        else:
            new_instructions.append(instr)

            # Invalidate expressions that use modified variables
            if instr.modifies_variable():
                modified_var = instr.get_modified_var()
                invalidate_expressions(available_exprs, modified_var)

    block.instructions = new_instructions

def invalidate_expressions(available_exprs, modified_var):
    """
    Remove expressions that use the modified variable.
    """
    to_remove = []
    for (op, left, right), temp in available_exprs.items():
        if left == modified_var or right == modified_var:
            to_remove.append((op, left, right))

    for key in to_remove:
        del available_exprs[key]
```

### Example

**Before:**
```
t0 = a + b
x = t0
t1 = a + b    // Same as t0!
y = t1
t2 = c * d
t3 = c * d    // Same as t2!
z = t3
```

**After CSE:**
```
t0 = a + b
x = t0
t1 = t0       // Reuse t0
y = t1
t2 = c * d
t3 = t2       // Reuse t2
z = t3
```

**After copy propagation (separate pass):**
```
t0 = a + b
x = t0
y = t0        // Replaced t1 with t0
t2 = c * d
z = t2        // Replaced t3 with t2
```

---

## Optimization 4: Copy Propagation

### Goal
Replace copies with original variables.

### Algorithm

```python
def copy_propagation(block):
    """
    Propagate copies within a basic block.
    """
    # Map: variable → its value
    copy_map = {}

    new_instructions = []

    for instr in block.instructions:
        # Substitute operands
        instr = substitute_operands(instr, copy_map)

        if isinstance(instr, Copy):
            # Track copy: x = y
            copy_map[instr.dest] = instr.source
        else:
            # Variable modified, invalidate copies
            if instr.modifies_variable():
                modified_var = instr.get_modified_var()
                if modified_var in copy_map:
                    del copy_map[modified_var]

                # Also invalidate if this var is used as a source
                invalidate_copies_using(copy_map, modified_var)

        new_instructions.append(instr)

    block.instructions = new_instructions

def substitute_operands(instr, copy_map):
    """
    Replace operands with their copied values.
    """
    if hasattr(instr, 'left') and instr.left in copy_map:
        instr.left = copy_map[instr.left]

    if hasattr(instr, 'right') and instr.right in copy_map:
        instr.right = copy_map[instr.right]

    return instr
```

### Example

**Before:**
```
x = a
y = x + 1    // Use 'a' directly
z = x * 2    // Use 'a' directly
x = 5        // x redefined, stop propagation
w = x + 1
```

**After:**
```
x = a
y = a + 1    // Replaced x with a
z = a * 2    // Replaced x with a
x = 5
w = x + 1    // x was redefined, don't propagate
```

---

## Optimization 5: Algebraic Simplification

### Goal
Apply mathematical identities to simplify expressions.

### Simplification Rules

```python
def algebraic_simplify(instr):
    """
    Apply algebraic identities.
    """
    if not isinstance(instr, BinaryOp):
        return instr

    op = instr.operator
    left = instr.left
    right = instr.right

    # Identity: x + 0 = x
    if op == '+' and is_constant(right, 0):
        return Copy(instr.dest, left)

    # Identity: 0 + x = x
    if op == '+' and is_constant(left, 0):
        return Copy(instr.dest, right)

    # Identity: x - 0 = x
    if op == '-' and is_constant(right, 0):
        return Copy(instr.dest, left)

    # Identity: x * 1 = x
    if op == '*' and is_constant(right, 1):
        return Copy(instr.dest, left)

    # Identity: 1 * x = x
    if op == '*' and is_constant(left, 1):
        return Copy(instr.dest, right)

    # Identity: x * 0 = 0
    if op == '*' and (is_constant(left, 0) or is_constant(right, 0)):
        return Assign(instr.dest, Constant(0))

    # Identity: x / 1 = x
    if op == '/' and is_constant(right, 1):
        return Copy(instr.dest, left)

    # Strength reduction: x * 2 = x + x
    if op == '*' and is_constant(right, 2):
        return BinaryOp(instr.dest, left, '+', left)

    # Strength reduction: x * power_of_2 = x << log2(n)
    if op == '*' and is_power_of_2(right):
        shift_amount = log2(get_constant_value(right))
        return BinaryOp(instr.dest, left, '<<', Constant(shift_amount))

    return instr
```

### Example

**Before:**
```
t0 = x + 0    // Identity
t1 = y * 1    // Identity
t2 = z * 0    // Annihilation
t3 = a * 2    // Strength reduction
t4 = b * 8    // Strength reduction
```

**After:**
```
t0 = x        // Removed + 0
t1 = y        // Removed * 1
t2 = 0        // Multiplication by 0
t3 = a + a    // 2x = x + x
t4 = b << 3   // 8x = x << 3 (if targeting assembly)
```

---

## Optimization 6: Branch Elimination

### Goal
Remove branches with constant conditions.

### Algorithm

```python
def branch_elimination(cfg):
    """
    Eliminate branches with constant conditions.
    """
    changed = True

    while changed:
        changed = False

        for block in cfg.blocks:
            last_instr = block.instructions[-1]

            if isinstance(last_instr, ConditionalBranch):
                condition = last_instr.condition

                # if true goto L  →  goto L
                if is_constant(condition, True):
                    block.instructions[-1] = UnconditionalJump(last_instr.target)
                    # Remove fall-through edge
                    remove_fall_through_edge(block)
                    changed = True

                # if false goto L  →  remove instruction
                elif is_constant(condition, False):
                    block.instructions.pop()  # Remove branch
                    # Remove branch edge
                    remove_branch_edge(block, last_instr.target)
                    changed = True

        # Remove unreachable blocks
        reachable = compute_reachable_blocks(cfg)
        old_count = len(cfg.blocks)
        cfg.blocks = [b for b in cfg.blocks if b in reachable]
        if len(cfg.blocks) < old_count:
            changed = True
```

### Example

**Before:**
```
t0 = true
if t0 goto L1    // Always true
  y = 10         // Unreachable
L1:
  x = 5
```

**After:**
```
t0 = true
goto L1          // Unconditional
L1:
  x = 5
```

**After DCE:**
```
x = 5
```

---

## Pass Manager

### Fixed-Point Iteration

Optimizations enable each other, so we run them repeatedly until no changes occur.

```python
class OptimizationPassManager:
    def __init__(self):
        self.passes = [
            ConstantFoldingPass(),
            AlgebraicSimplificationPass(),
            CopyPropagationPass(),
            CommonSubexpressionEliminationPass(),
            BranchEliminationPass(),
            DeadCodeEliminationPass(),
        ]

    def optimize(self, ir):
        """
        Run optimization passes until fixed point.
        """
        iteration = 0
        max_iterations = 10  # Prevent infinite loops

        while iteration < max_iterations:
            changed = False

            for pass_obj in self.passes:
                if pass_obj.run(ir):
                    changed = True

            if not changed:
                # Fixed point reached
                break

            iteration += 1

        return ir
```

### Pass Ordering

Order matters! Some passes create opportunities for others:

**Good order:**
1. Constant Folding (creates constants)
2. Algebraic Simplification (simplifies using constants)
3. Copy Propagation (exposes more constants)
4. CSE (finds common expressions)
5. Branch Elimination (simplifies control flow)
6. DCE (removes unused code)

**Why this order?**
- Constant folding first → creates constants for other passes
- Copy propagation → exposes more optimization opportunities
- DCE last → cleans up after all other passes

---

## Metrics and Testing

### Measuring Optimization Effectiveness

```python
def measure_optimization_impact(ir_before, ir_after):
    """
    Calculate optimization metrics.
    """
    metrics = {
        'instructions_before': count_instructions(ir_before),
        'instructions_after': count_instructions(ir_after),
        'reduction_percent': 0,
        'optimizations_applied': [],
    }

    reduction = metrics['instructions_before'] - metrics['instructions_after']
    metrics['reduction_percent'] = (reduction / metrics['instructions_before']) * 100

    return metrics
```

### Testing Strategy

**1. Unit tests for each optimization:**
```python
def test_constant_folding():
    ir = [
        BinaryOp('t0', Constant(2), '+', Constant(3)),
    ]
    optimized = constant_folding_pass.run(ir)
    assert optimized == [Assign('t0', Constant(5))]
```

**2. Integration tests:**
```python
def test_optimization_pipeline():
    source = """
    fn main() -> int {
        let x: int = 2 + 3;
        let y: int = x * 1;
        return y;
    }
    """
    ir = compile_to_ir(source)
    optimized_ir = optimize(ir)

    # Should be reduced to: return 5
    assert count_instructions(optimized_ir) < count_instructions(ir)
```

**3. Correctness tests:**
```python
def test_optimization_preserves_semantics():
    """
    Ensure optimizations don't change program behavior.
    """
    programs = load_test_programs()

    for program in programs:
        # Run unoptimized version
        output_before = run_program(program, optimize=False)

        # Run optimized version
        output_after = run_program(program, optimize=True)

        # Must produce same output
        assert output_before == output_after
```

---

## Advanced Topics

### Loop Optimizations (Future)

- **Loop-invariant code motion**: Move unchanging code outside loop
- **Loop unrolling**: Duplicate loop body to reduce iteration overhead
- **Induction variable elimination**: Simplify loop counters

### Global Optimizations (Future)

- **Interprocedural analysis**: Optimize across function calls
- **Inlining**: Replace function call with function body
- **Global value numbering**: CSE across basic blocks

---

## Next Steps

1. Implement basic optimizations (constant folding, DCE)
2. Build CFG infrastructure
3. Add remaining optimizations
4. Create pass manager with fixed-point iteration
5. Add metrics and benchmarking
6. Test thoroughly to ensure semantic preservation

This forms the foundation for a production-quality optimizing compiler!
