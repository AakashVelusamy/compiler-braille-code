"""
Tests for the Interpreter
===========================

Run from the project root:
    cd braillecode/backend
    python -m tests.test_interpreter
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser
from compiler.engine.analyzer import SemanticAnalyzer
from compiler.engine.interpreter import Interpreter, RuntimeError_, MaxIterationsError


# ─── Helper ───────────────────────────────────────────────────────────────────

translator = Translator()


def run(source: str) -> dict:
    """Full pipeline: English → Braille → tokens → AST → analyze → execute."""
    braille = translator.english_to_braille(source)
    tokens = Lexer(braille).tokenize()
    ast = Parser(tokens).parse()

    # Semantic check first
    sa = SemanticAnalyzer()
    sa.analyze(ast)
    if sa.errors:
        return {
            'output': [],
            'variables': {},
            'errors': [{'message': str(e), 'line': e.line} for e in sa.errors],
            'success': False,
        }

    # Execute
    interp = Interpreter()
    return interp.execute(ast)


def assert_output(result: dict, expected: list):
    """Assert the program output matches expected lines."""
    assert result['success'], (
        f"Program failed with errors:\n"
        + '\n'.join(f"  {e}" for e in result['errors'])
    )
    assert result['output'] == expected, (
        f"Output mismatch:\n"
        f"  Expected: {expected}\n"
        f"  Got:      {result['output']}"
    )


def assert_var(result: dict, name: str, value):
    """Assert a variable has the expected final value."""
    assert name in result['variables'], f"Variable '{name}' not found"
    actual = result['variables'][name]
    assert actual == value, f"Variable '{name}': expected {value!r}, got {actual!r}"


def assert_runtime_error(result: dict, substring: str):
    """Assert the program produced a runtime error containing the substring."""
    assert not result['success'], "Expected failure but program succeeded"
    for e in result['errors']:
        if substring in e['message']:
            return
    assert False, (
        f"Expected error containing '{substring}', got:\n"
        + '\n'.join(f"  {e['message']}" for e in result['errors'])
    )


# ─── Basic assignments ───────────────────────────────────────────────────────

def test_integer_assignment():
    """Interpreter: x = 42"""
    result = run("x = 42")
    assert_var(result, 'x', 42)
    print("[PASS] Integer assignment")


def test_string_assignment():
    """Interpreter: msg = "hello" """
    result = run('msg = "hello"')
    assert_var(result, 'msg', 'hello')
    print("[PASS] String assignment")


def test_boolean_assignment():
    """Interpreter: flag = True"""
    result = run("flag = True")
    assert_var(result, 'flag', True)
    result2 = run("flag = False")
    assert_var(result2, 'flag', False)
    print("[PASS] Boolean assignment")


def test_none_assignment():
    """Interpreter: x = None"""
    result = run("x = None")
    assert_var(result, 'x', None)
    print("[PASS] None assignment")


def test_variable_chain():
    """Interpreter: x = 10, y = x"""
    result = run("x = 10\ny = x")
    assert_var(result, 'x', 10)
    assert_var(result, 'y', 10)
    print("[PASS] Variable chain")


# ─── Arithmetic ──────────────────────────────────────────────────────────────

def test_addition():
    """Interpreter: x = 3 + 7"""
    result = run("x = 3 + 7")
    assert_var(result, 'x', 10)
    print("[PASS] Addition")


def test_subtraction():
    """Interpreter: x = 10 - 4"""
    result = run("x = 10 - 4")
    assert_var(result, 'x', 6)
    print("[PASS] Subtraction")


def test_multiplication():
    """Interpreter: x = 6 * 7"""
    result = run("x = 6 * 7")
    assert_var(result, 'x', 42)
    print("[PASS] Multiplication")


def test_division():
    """Interpreter: x = 10 / 3 (integer division)"""
    result = run("x = 10 / 3")
    assert_var(result, 'x', 3)
    print("[PASS] Integer division")


def test_modulo():
    """Interpreter: x = 10 % 3"""
    result = run("x = 10 % 3")
    assert_var(result, 'x', 1)
    print("[PASS] Modulo")


def test_operator_precedence():
    """Interpreter: x = 2 + 3 * 4 → 14"""
    result = run("x = 2 + 3 * 4")
    assert_var(result, 'x', 14)
    print("[PASS] Operator precedence (2 + 3*4 = 14)")


def test_parentheses():
    """Interpreter: x = (2 + 3) * 4 → 20"""
    result = run("x = (2 + 3) * 4")
    assert_var(result, 'x', 20)
    print("[PASS] Parentheses override precedence")


def test_unary_minus():
    """Interpreter: x = -5"""
    result = run("x = -5")
    assert_var(result, 'x', -5)
    print("[PASS] Unary minus")


def test_complex_arithmetic():
    """Interpreter: x = (10 + 5) * 2 - 8 / 4 → 28"""
    result = run("x = (10 + 5) * 2 - 8 / 4")
    assert_var(result, 'x', 28)
    print("[PASS] Complex arithmetic: (10+5)*2 - 8/4 = 28")


def test_string_concatenation():
    """Interpreter: x = "hello" + " " + "world" """
    # Need to build in steps since our translator handles one line at a time
    result = run('a = "hello"\nb = " world"\nc = a + b')
    assert_var(result, 'c', 'hello world')
    print("[PASS] String concatenation")


# ─── Print ────────────────────────────────────────────────────────────────────

def test_print_integer():
    """Interpreter: print(42)"""
    result = run("print(42)")
    assert_output(result, ['42'])
    print("[PASS] Print integer")


def test_print_string():
    """Interpreter: print("hello")"""
    result = run('print("hello")')
    assert_output(result, ['hello'])
    print("[PASS] Print string")


def test_print_variable():
    """Interpreter: x = 10, print(x)"""
    result = run("x = 10\nprint(x)")
    assert_output(result, ['10'])
    print("[PASS] Print variable")


def test_print_expression():
    """Interpreter: print(3 + 4)"""
    result = run("print(3 + 4)")
    assert_output(result, ['7'])
    print("[PASS] Print expression")


def test_print_boolean():
    """Interpreter: print(True), print(False)"""
    result = run("print(True)\nprint(False)")
    assert_output(result, ['True', 'False'])
    print("[PASS] Print boolean")


def test_print_none():
    """Interpreter: print(None)"""
    result = run("print(None)")
    assert_output(result, ['None'])
    print("[PASS] Print None")


def test_multiple_prints():
    """Interpreter: three print statements"""
    result = run("print(1)\nprint(2)\nprint(3)")
    assert_output(result, ['1', '2', '3'])
    print("[PASS] Multiple prints")


# ─── Comparisons ──────────────────────────────────────────────────────────────

def test_comparisons():
    """Interpreter: all 6 comparison operators"""
    tests = [
        ("x = 5 == 5",  'x', True),
        ("x = 5 != 3",  'x', True),
        ("x = 3 < 5",   'x', True),
        ("x = 5 > 3",   'x', True),
        ("x = 3 <= 3",  'x', True),
        ("x = 5 >= 5",  'x', True),
        ("x = 5 == 3",  'x', False),
        ("x = 5 < 3",   'x', False),
    ]
    for source, name, expected in tests:
        result = run(source)
        assert_var(result, name, expected)
        print(f"    {source} → {expected} OK")
    print("[PASS] All comparison operators work correctly")


# ─── Boolean logic ────────────────────────────────────────────────────────────

def test_and_operator():
    """Interpreter: True and False → False"""
    result = run("x = True and False")
    assert_var(result, 'x', False)
    result2 = run("x = True and True")
    assert_var(result2, 'x', True)
    print("[PASS] and operator")


def test_or_operator():
    """Interpreter: False or True → True"""
    result = run("x = False or True")
    assert_var(result, 'x', True)
    result2 = run("x = False or False")
    assert_var(result2, 'x', False)
    print("[PASS] or operator")


def test_not_operator():
    """Interpreter: not True → False"""
    result = run("x = not True")
    assert_var(result, 'x', False)
    result2 = run("x = not False")
    assert_var(result2, 'x', True)
    print("[PASS] not operator")


def test_short_circuit():
    """Interpreter: short-circuit evaluation"""
    # `and` short-circuits: False and <anything> → False without evaluating right
    result = run("x = False and True")
    assert_var(result, 'x', False)
    # `or` short-circuits: True or <anything> → True without evaluating right
    result2 = run("x = True or False")
    assert_var(result2, 'x', True)
    print("[PASS] Short-circuit evaluation")


# ─── If / elif / else ─────────────────────────────────────────────────────────

def test_if_true():
    """Interpreter: if True branch executes"""
    source = "x = 10\nif x > 5:\n    print(x)"
    result = run(source)
    assert_output(result, ['10'])
    print("[PASS] if-true branch executes")


def test_if_false():
    """Interpreter: if False branch skipped"""
    source = "x = 3\nif x > 5:\n    print(x)"
    result = run(source)
    assert_output(result, [])
    print("[PASS] if-false branch skipped")


def test_if_else():
    """Interpreter: if/else picks correct branch"""
    source = "x = 3\nif x > 5:\n    print(1)\nelse:\n    print(2)"
    result = run(source)
    assert_output(result, ['2'])
    print("[PASS] if/else picks else branch")


def test_if_elif_else():
    """Interpreter: if/elif/else chain"""
    source = """x = 15
if x > 20:
    print(3)
elif x > 10:
    print(2)
else:
    print(1)"""
    result = run(source)
    assert_output(result, ['2'])
    print("[PASS] if/elif/else picks elif branch")


def test_nested_if():
    """Interpreter: nested if statements"""
    source = """x = 10
if x > 5:
    if x > 8:
        print(1)"""
    result = run(source)
    assert_output(result, ['1'])
    print("[PASS] Nested if executes correctly")


# ─── While loop ───────────────────────────────────────────────────────────────

def test_while_countdown():
    """Interpreter: while loop counting down"""
    source = """x = 5
while x > 0:
    print(x)
    x = x - 1"""
    result = run(source)
    assert_output(result, ['5', '4', '3', '2', '1'])
    assert_var(result, 'x', 0)
    print("[PASS] While loop countdown 5→0")


def test_while_no_execute():
    """Interpreter: while condition false from start"""
    source = "x = 0\nwhile x > 5:\n    print(x)"
    result = run(source)
    assert_output(result, [])
    print("[PASS] While loop body never executes when condition is false")


def test_while_single_iteration():
    """Interpreter: while loop runs exactly once"""
    source = """x = 1
while x > 0:
    print(x)
    x = x - 1"""
    result = run(source)
    assert_output(result, ['1'])
    assert_var(result, 'x', 0)
    print("[PASS] While loop single iteration")


def test_while_accumulator():
    """Interpreter: while loop accumulating a sum"""
    source = """sum = 0
i = 1
while i <= 5:
    sum = sum + i
    i = i + 1
print(sum)"""
    result = run(source)
    assert_output(result, ['15'])  # 1+2+3+4+5 = 15
    assert_var(result, 'sum', 15)
    print("[PASS] While loop accumulator (sum 1..5 = 15)")


# ─── Runtime errors ──────────────────────────────────────────────────────────

def test_division_by_zero():
    """Interpreter: division by zero"""
    result = run("x = 10 / 0")
    assert_runtime_error(result, "Division by zero")
    print("[PASS] Division by zero caught")


def test_modulo_by_zero():
    """Interpreter: modulo by zero"""
    result = run("x = 10 % 0")
    assert_runtime_error(result, "Modulo by zero")
    print("[PASS] Modulo by zero caught")


def test_type_error_add():
    """Interpreter: adding string and int"""
    result = run('x = "hello"\ny = 5\nz = x + y')
    assert_runtime_error(result, "Cannot add")
    print("[PASS] Type error on string + int caught")


def test_undefined_variable():
    """Interpreter: using undefined variable at runtime"""
    # The semantic analyzer would catch this first, but test the interpreter's
    # own protection via direct AST execution
    from compiler.engine.ast_nodes import Program, Print, Identifier
    ast = Program(body=[Print(line=1, value=Identifier(line=1, name='nonexistent'))])
    interp = Interpreter()
    result = interp.execute(ast)
    assert_runtime_error(result, "Undefined variable")
    print("[PASS] Undefined variable caught at runtime")


# ─── Complex programs ────────────────────────────────────────────────────────

def test_fizzbuzz_style():
    """Interpreter: FizzBuzz-style program (modulo + if/elif/else)"""
    source = """i = 1
while i <= 10:
    if i % 3 == 0:
        print(0)
    elif i % 2 == 0:
        print(1)
    else:
        print(i)
    i = i + 1"""
    result = run(source)
    # i=1→1, i=2→1, i=3→0, i=4→1, i=5→5, i=6→0, i=7→7, i=8→1, i=9→0, i=10→1
    assert_output(result, ['1', '1', '0', '1', '5', '0', '7', '1', '0', '1'])
    print("[PASS] FizzBuzz-style program")


def test_full_pipeline():
    """Interpreter: complete end-to-end program"""
    source = """x = 10
y = 20
z = x + y * 2
if z > 30:
    print(z)
    z = z - 1
else:
    print(0)
print(z)"""
    result = run(source)
    # z = 10 + 20*2 = 50, 50 > 30 → print 50, z becomes 49, print 49
    assert_output(result, ['50', '49'])
    assert_var(result, 'z', 49)
    print("[PASS] Full end-to-end pipeline")


def test_power_of_two():
    """Interpreter: compute 2^8 via repeated multiplication"""
    source = """result = 1
i = 0
while i < 8:
    result = result * 2
    i = i + 1
print(result)"""
    result = run(source)
    assert_output(result, ['256'])
    print("[PASS] 2^8 = 256 via while loop")


# ─── Run all tests ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("BrailleCode Interpreter — Test Suite")
    print("=" * 60)

    tests = [
        # Basic assignments
        test_integer_assignment,
        test_string_assignment,
        test_boolean_assignment,
        test_none_assignment,
        test_variable_chain,
        # Arithmetic
        test_addition,
        test_subtraction,
        test_multiplication,
        test_division,
        test_modulo,
        test_operator_precedence,
        test_parentheses,
        test_unary_minus,
        test_complex_arithmetic,
        test_string_concatenation,
        # Print
        test_print_integer,
        test_print_string,
        test_print_variable,
        test_print_expression,
        test_print_boolean,
        test_print_none,
        test_multiple_prints,
        # Comparisons
        test_comparisons,
        # Boolean logic
        test_and_operator,
        test_or_operator,
        test_not_operator,
        test_short_circuit,
        # If / elif / else
        test_if_true,
        test_if_false,
        test_if_else,
        test_if_elif_else,
        test_nested_if,
        # While loop
        test_while_countdown,
        test_while_no_execute,
        test_while_single_iteration,
        test_while_accumulator,
        # Runtime errors
        test_division_by_zero,
        test_modulo_by_zero,
        test_type_error_add,
        test_undefined_variable,
        # Complex programs
        test_fizzbuzz_style,
        test_full_pipeline,
        test_power_of_two,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        print(f"\n▶ {test_fn.__doc__}")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
