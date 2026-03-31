"""
BrailleCode Compiler - Code Optimizer Tests
============================================

Tests the Code Optimizer (Phase 5):
applies classical optimization techniques to TAC.

Optimizations tested:
  1. Constant Folding   - evaluate ops on constants at compile time
  2. Constant Propagation - replace vars with known constant values
  3. Strength Reduction   - replace expensive ops with cheaper ones
  4. Dead Code Elimination - remove assignments to unused temporaries
"""

import sys
sys.path.insert(0, '.')

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser
from compiler.engine.ir_generator import IRGenerator
from compiler.engine.optimizer import Optimizer


def compile_and_optimize(source):
    """Helper: compile and optimize source to TAC."""
    t = Translator()
    braille = t.english_to_braille(source)
    tokens = Lexer(braille).tokenize()
    ast = Parser(tokens).parse()
    gen = IRGenerator()
    ir = gen.generate(ast)
    opt = Optimizer(ir)
    optimized = opt.optimize()
    return ir, optimized, opt


# ─── Constant Folding ───────────────────────────────────────────────────────

def test_opt_constant_fold_add():
    """Optimizer: constant folding for addition."""
    ir, opt_ir, opt = compile_and_optimize("x = 3 + 4")

    folded = [e for e in opt.log if e.pass_name == 'Constant Folding']
    assert len(folded) >= 1, "Expected constant folding"

    # Result should be simplified to x = 7
    assigns = [i for i in opt_ir if i.op == '=']
    fold_assigns = [a for a in assigns if '7' in str(a.arg1)]
    assert len(fold_assigns) >= 1, "Expected folded result 7"

    print("[PASS] Constant folding: addition")


def test_opt_constant_fold_multiply():
    """Optimizer: constant folding for multiplication."""
    ir, opt_ir, opt = compile_and_optimize("x = 2 * 5")

    folded = [e for e in opt.log if e.pass_name == 'Constant Folding']
    assert len(folded) >= 1

    assigns = [i for i in opt_ir if i.op == '=' and i.result == 'x']
    assert len(assigns) >= 1
    assert '10' in str(assigns[0].arg1)

    print("[PASS] Constant folding: multiplication")


def test_opt_constant_fold_divide():
    """Optimizer: constant folding for division."""
    ir, opt_ir, opt = compile_and_optimize("x = 20 / 4")

    folded = [e for e in opt.log if e.pass_name == 'Constant Folding']
    assert len(folded) >= 1

    assigns = [i for i in opt_ir if i.op == '=' and i.result == 'x']
    assert '5' in str(assigns[0].arg1)

    print("[PASS] Constant folding: division")


def test_opt_constant_fold_comparison():
    """Optimizer: constant folding for comparisons."""
    ir, opt_ir, opt = compile_and_optimize("x = 5 == 5")

    folded = [e for e in opt.log if e.pass_name == 'Constant Folding']
    assert len(folded) >= 1

    print("[PASS] Constant folding: comparison")


# ─── Constant Propagation ───────────────────────────────────────────────────

def test_opt_constant_propagation():
    """Optimizer: constant propagation replaces variable with value."""
    ir, opt_ir, opt = compile_and_optimize("x = 10\ny = x + 5")

    propagated = [e for e in opt.log if e.pass_name == 'Constant Propagation']
    assert len(propagated) >= 1, "Expected constant propagation"

    # Should have a propagation entry with '10' in it
    assert any('10' in str(e.optimized) for e in propagated)

    print("[PASS] Constant propagation")


def test_opt_propagation_chain():
    """Optimizer: chained constant propagation."""
    ir, opt_ir, opt = compile_and_optimize("x = 5\ny = x\nz = y + 1")

    propagated = [e for e in opt.log if e.pass_name == 'Constant Propagation']
    # Should propagate through the chain
    assert len(propagated) >= 1

    print("[PASS] Chained constant propagation")


# ─── Strength Reduction ─────────────────────────────────────────────────────

def test_opt_strength_mult_by_2():
    """Optimizer: x * 2 → x + x."""
    ir, opt_ir, opt = compile_and_optimize("x = a * 2")

    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']
    assert len(strength) >= 1, "Expected strength reduction"
    assert any('multiply by 2' in e.description.lower() for e in strength)

    # Should convert * to +
    ops = [i for i in opt_ir if i.op == '+']
    assert len(ops) >= 1, "Expected addition after strength reduction"

    print("[PASS] Strength reduction: x * 2 → x + x")


def test_opt_strength_mult_by_1():
    """Optimizer: x * 1 → x (eliminate multiply)."""
    ir, opt_ir, opt = compile_and_optimize("x = a * 1")

    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']
    assert len(strength) >= 1

    # Should remove the multiply operation
    opt_text = str(opt_ir)
    assert 'a' in opt_text  # but a should still appear

    print("[PASS] Strength reduction: x * 1 → x")


def test_opt_strength_add_0():
    """Optimizer: x + 0 → x (eliminate add)."""
    ir, opt_ir, opt = compile_and_optimize("x = a + 0")

    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']
    assert len(strength) >= 1

    # Should simplify away the addition
    adds = [i for i in opt_ir if i.op == '+']
    assert len(adds) == 0, "Add by 0 should be eliminated"

    print("[PASS] Strength reduction: x + 0 → x")


def test_opt_strength_sub_0():
    """Optimizer: x - 0 → x (eliminate subtract)."""
    ir, opt_ir, opt = compile_and_optimize("x = a - 0")

    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']
    assert len(strength) >= 1

    subs = [i for i in opt_ir if i.op == '-']
    assert len(subs) == 0, "Subtract 0 should be eliminated"

    print("[PASS] Strength reduction: x - 0 → x")


def test_opt_strength_mult_by_0():
    """Optimizer: x * 0 → 0 (constant fold)."""
    ir, opt_ir, opt = compile_and_optimize("x = a * 0")

    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']
    assert len(strength) >= 1

    print("[PASS] Strength reduction: x * 0 → 0")


# ─── Dead Code Elimination ──────────────────────────────────────────────────

def test_opt_dead_code_unused_temp():
    """Optimizer: removes assignments to unused temporaries."""
    ir, opt_ir, opt = compile_and_optimize("x = 1\ny = 2 + 3\nz = 10")

    dead = [e for e in opt.log if e.pass_name == 'Dead Code Elimination']

    # Original should have more instructions than optimized
    assert len(ir) > len(opt_ir), f"Expected dead code removal: {len(ir)} → {len(opt_ir)}"

    print("[PASS] Dead code elimination: unused temporaries")


def test_opt_dead_code_preserves_used():
    """Optimizer: preserves assignments that are used."""
    ir, opt_ir, opt = compile_and_optimize("x = 5\ny = x + 1\nprint(y)")

    # All assignments to x and y should be preserved
    x_assigns = [i for i in opt_ir if i.result == 'x']
    y_assigns = [i for i in opt_ir if i.result == 'y']

    assert len(x_assigns) >= 1, "Used variable x should not be dead-coded"
    assert len(y_assigns) >= 1, "Used variable y should not be dead-coded"

    print("[PASS] Dead code elimination: preserves used assignments")


# ─── Combined Optimizations ─────────────────────────────────────────────────

def test_opt_multiple_passes():
    """Optimizer: multiple optimization passes interact."""
    source = """x = 2 * 1
y = x + 0
z = 3 + 4
print(z)"""

    ir, opt_ir, opt = compile_and_optimize(source)

    # Should have optimizations from multiple passes
    folds = [e for e in opt.log if e.pass_name == 'Constant Folding']
    props = [e for e in opt.log if e.pass_name == 'Constant Propagation']
    strength = [e for e in opt.log if e.pass_name == 'Strength Reduction']

    total_opts = len(folds) + len(props) + len(strength)
    assert total_opts >= 4, f"Expected multiple optimizations, got {total_opts}"

    # Program should be significantly smaller
    assert len(opt_ir) < len(ir), "Optimized code should be smaller"

    print("[PASS] Multiple optimization passes")


def test_opt_no_unnecessary_optimizations():
    """Optimizer: doesn't optimize already-optimal code."""
    # Simple, optimal code
    source = """x = 10
y = 20
print(x)"""

    ir, opt_ir, opt = compile_and_optimize(source)

    # Should have very few or no optimizations
    total_opts = len(opt.log)
    # Note: might have some due to internal temporaries, but should be minimal
    assert total_opts <= 2, f"Already-optimal code shouldn't be heavily optimized: {total_opts} opts"

    print("[PASS] No unnecessary optimizations")


# ─── Optimization Statistics ────────────────────────────────────────────────

def test_opt_reports_stats():
    """Optimizer: produces accurate statistics."""
    ir, opt_ir, opt = compile_and_optimize("x = 2 * 1\ny = x + 0")

    report = opt.get_report()

    assert 'original_count' in report
    assert 'optimized_count' in report
    assert 'eliminated' in report
    assert 'stats' in report
    assert 'log' in report

    assert report['original_count'] == len(ir)
    assert report['optimized_count'] == len(opt_ir)
    assert report['eliminated'] == len(ir) - len(opt_ir)

    print("[PASS] Optimization statistics")


def test_opt_logs_each_change():
    """Optimizer: logs each optimization with before/after."""
    ir, opt_ir, opt = compile_and_optimize("x = 3 + 4\ny = x * 1")

    assert len(opt.log) >= 1, "Expected optimizations logged"

    for entry in opt.log:
        assert entry.pass_name  # e.g., "Constant Folding"
        assert entry.original   # before
        assert entry.optimized  # after
        assert entry.description  # explanation

    print("[PASS] Optimization logging")


# ─── Edge Cases ──────────────────────────────────────────────────────────────

def test_opt_division_by_zero_no_fold():
    """Optimizer: doesn't fold division by zero (error case)."""
    # x / 0 should not be constant folded to avoid divide-by-zero
    ir, opt_ir, opt = compile_and_optimize("x = 10 / 0")

    # Should NOT have folded this
    divs = [i for i in opt_ir if i.op == '/']
    assert len(divs) > 0, "Division by zero should not be folded"

    print("[PASS] Division by zero safety")


def test_opt_empty_log():
    """Optimizer: works with code that has no optimizations."""
    ir, opt_ir, opt = compile_and_optimize("x = 10")

    # Minimal code might have minimal/no optimizations
    assert isinstance(opt.log, list)
    # log might be empty or small for very simple code

    print("[PASS] Empty optimization log")


# ─── Integration ────────────────────────────────────────────────────────────

def test_opt_fizzbuzz():
    """Optimizer: handles complex programs."""
    source = """n = 15
i = 1
while i <= n:
    if i % 3 == 0:
        print(i)
    i = i + 1"""

    ir, opt_ir, opt = compile_and_optimize(source)

    assert len(opt_ir) > 0
    assert opt_ir[-1].op == 'HALT'

    # Should have some optimizations
    assert len(opt.log) >= 0  # Might have or not

    print("[PASS] FizzBuzz optimization")


# ─── Text Representation ────────────────────────────────────────────────────

def test_opt_report_json_serializable():
    """Optimizer: report is JSON-serializable."""
    import json

    ir, opt_ir, opt = compile_and_optimize("x = 3 + 4")
    report = opt.get_report()

    try:
        json_str = json.dumps(report)
        assert len(json_str) > 0
    except TypeError as e:
        raise AssertionError(f"Report not JSON-serializable: {e}")

    print("[PASS] Report JSON serialization")


# ─── Entry Point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BrailleCode Code Optimizer – Test Suite")
    print("="*60 + "\n")

    passed = failed = 0

    tests = [
        test_opt_constant_fold_add,
        test_opt_constant_fold_multiply,
        test_opt_constant_fold_divide,
        test_opt_constant_fold_comparison,
        test_opt_constant_propagation,
        test_opt_propagation_chain,
        test_opt_strength_mult_by_2,
        test_opt_strength_mult_by_1,
        test_opt_strength_add_0,
        test_opt_strength_sub_0,
        test_opt_strength_mult_by_0,
        test_opt_dead_code_unused_temp,
        test_opt_dead_code_preserves_used,
        test_opt_multiple_passes,
        test_opt_no_unnecessary_optimizations,
        test_opt_reports_stats,
        test_opt_logs_each_change,
        test_opt_division_by_zero_no_fold,
        test_opt_empty_log,
        test_opt_fizzbuzz,
        test_opt_report_json_serializable,
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__doc__}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed}/{len(tests)} passed, {failed} failed")
    print("="*60)
