"""
Tests for the Semantic Analyzer
=================================

Run from the project root:
    cd braillecode/backend
    python -m tests.test_analyzer
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser
from compiler.engine.analyzer import SemanticAnalyzer, SemanticError, SymbolTable


# ─── Helper ───────────────────────────────────────────────────────────────────

translator = Translator()


def analyze(source: str) -> SemanticAnalyzer:
    """English source → Braille → tokens → AST → analyze. Returns the analyzer."""
    braille = translator.english_to_braille(source)
    tokens = Lexer(braille).tokenize()
    ast = Parser(tokens).parse()
    sa = SemanticAnalyzer()
    sa.analyze(ast)
    return sa


def assert_no_errors(sa: SemanticAnalyzer):
    """Assert analyzer has no errors."""
    assert len(sa.errors) == 0, (
        f"Expected no errors, got {len(sa.errors)}:\n"
        + '\n'.join(f"  {e}" for e in sa.errors)
    )


def assert_has_error(sa: SemanticAnalyzer, substring: str):
    """Assert analyzer has at least one error containing the given substring."""
    for e in sa.errors:
        if substring in str(e):
            return
    assert False, (
        f"Expected an error containing '{substring}', got:\n"
        + '\n'.join(f"  {e}" for e in sa.errors)
        + ('\n  (no errors)' if not sa.errors else '')
    )


def assert_has_warning(sa: SemanticAnalyzer, substring: str):
    """Assert analyzer has at least one warning containing the given substring."""
    for w in sa.warnings:
        if substring in w.message:
            return
    assert False, (
        f"Expected a warning containing '{substring}', got:\n"
        + '\n'.join(f"  {w}" for w in sa.warnings)
        + ('\n  (no warnings)' if not sa.warnings else '')
    )


# ─── Symbol Table unit tests ─────────────────────────────────────────────────

def test_symbol_table_declare_and_lookup():
    """SymbolTable: declare and lookup in global scope"""
    st = SymbolTable()
    st.declare('x', line=1, inferred_type='int')

    sym = st.lookup('x')
    assert sym is not None
    assert sym.name == 'x'
    assert sym.inferred_type == 'int'
    assert sym.scope_depth == 0

    assert st.lookup('y') is None
    print("[PASS] Symbol table declare and lookup works")


def test_symbol_table_nested_scopes():
    """SymbolTable: nested scope access and isolation"""
    st = SymbolTable()
    st.declare('x', line=1, inferred_type='int')

    # Enter inner scope
    st.push_scope()
    st.declare('y', line=2, inferred_type='str')

    # Inner scope can see both x and y
    assert st.is_declared('x')
    assert st.is_declared('y')

    # Exit inner scope
    st.pop_scope()

    # Outer scope can see x but not y
    assert st.is_declared('x')
    assert not st.is_declared('y')
    print("[PASS] Nested scope access and isolation correct")


def test_symbol_table_shadowing():
    """SymbolTable: inner scope can shadow outer variable"""
    st = SymbolTable()
    st.declare('x', line=1, inferred_type='int')

    st.push_scope()
    st.declare('x', line=5, inferred_type='str')

    # Lookup should find the inner 'x'
    sym = st.lookup('x')
    assert sym.inferred_type == 'str'
    assert sym.declared_line == 5

    st.pop_scope()

    # After exiting, should find the outer 'x'
    sym = st.lookup('x')
    assert sym.inferred_type == 'int'
    assert sym.declared_line == 1
    print("[PASS] Variable shadowing works correctly")


def test_symbol_table_depth():
    """SymbolTable: depth tracking"""
    st = SymbolTable()
    assert st.depth == 0
    st.push_scope()
    assert st.depth == 1
    st.push_scope()
    assert st.depth == 2
    st.pop_scope()
    assert st.depth == 1
    st.pop_scope()
    assert st.depth == 0
    print("[PASS] Scope depth tracked correctly")


# ─── Analyzer: valid programs ─────────────────────────────────────────────────

def test_valid_simple_assignment():
    """Analyzer: x = 10 (valid)"""
    sa = analyze("x = 10")
    assert_no_errors(sa)
    sym = sa.symbol_table.lookup('x')
    assert sym is not None
    assert sym.inferred_type == 'int'
    print("[PASS] Simple assignment analyzed with no errors")


def test_valid_variable_chain():
    """Analyzer: x = 10, y = x (valid - x declared before use)"""
    sa = analyze("x = 10\ny = x")
    assert_no_errors(sa)
    assert sa.symbol_table.is_declared('x')
    assert sa.symbol_table.is_declared('y')
    print("[PASS] Variable chain analyzed with no errors")


def test_valid_arithmetic():
    """Analyzer: x = 5, y = x + 3 * 2 (valid)"""
    sa = analyze("x = 5\ny = x + 3 * 2")
    assert_no_errors(sa)
    print("[PASS] Arithmetic expression analyzed with no errors")


def test_valid_if_else():
    """Analyzer: if/else with valid variable usage"""
    source = """x = 10
if x > 5:
    print(x)
else:
    print(0)"""
    sa = analyze(source)
    assert_no_errors(sa)
    print("[PASS] If/else analyzed with no errors")


def test_valid_while_loop():
    """Analyzer: while loop with valid variable usage"""
    source = """x = 5
while x > 0:
    print(x)
    x = x - 1"""
    sa = analyze(source)
    assert_no_errors(sa)
    print("[PASS] While loop analyzed with no errors")


def test_valid_boolean_logic():
    """Analyzer: x = True and False or not True (valid)"""
    sa = analyze("x = True\ny = x and False or not True")
    assert_no_errors(sa)
    print("[PASS] Boolean logic analyzed with no errors")


def test_valid_string_assignment():
    """Analyzer: msg = "hello" (valid, type inferred as str)"""
    sa = analyze('msg = "hello"')
    assert_no_errors(sa)
    sym = sa.symbol_table.lookup('msg')
    assert sym.inferred_type == 'str'
    print("[PASS] String assignment type inferred correctly")


def test_valid_none_assignment():
    """Analyzer: x = None (valid)"""
    sa = analyze("x = None")
    assert_no_errors(sa)
    sym = sa.symbol_table.lookup('x')
    assert sym.inferred_type == 'none'
    print("[PASS] None assignment type inferred correctly")


def test_valid_comparison_types():
    """Analyzer: comparisons return bool type"""
    sa = analyze("x = 5\ny = x > 3")
    assert_no_errors(sa)
    sym = sa.symbol_table.lookup('y')
    assert sym.inferred_type == 'bool'
    print("[PASS] Comparison inferred as bool")


def test_valid_complex_program():
    """Analyzer: full program with all features"""
    source = """x = 10
y = 20
z = x + y * 2
if z > 30:
    print(z)
    z = z - 1
elif z == 30:
    print(0)
else:
    print(1)
while x > 0:
    x = x - 1
print(x)"""
    sa = analyze(source)
    assert_no_errors(sa)
    print("[PASS] Complex program analyzed with no errors")


def test_valid_nested_if():
    """Analyzer: nested if blocks with outer variable access"""
    source = """x = 10
if x > 5:
    if x > 8:
        print(x)"""
    sa = analyze(source)
    assert_no_errors(sa)
    print("[PASS] Nested if with outer variable access - no errors")


# ─── Analyzer: errors ─────────────────────────────────────────────────────────

def test_error_undeclared_variable():
    """Analyzer: using undeclared variable produces error"""
    sa = analyze("print(x)")
    assert_has_error(sa, "used before assignment")
    print("[PASS] Undeclared variable detected")


def test_error_undeclared_in_expression():
    """Analyzer: undeclared variable in arithmetic expression"""
    sa = analyze("x = y + 1")
    assert_has_error(sa, "'y' used before assignment")
    print("[PASS] Undeclared variable in expression detected")


def test_error_undeclared_in_condition():
    """Analyzer: undeclared variable in if condition"""
    sa = analyze("if z > 0:\n    print(0)")
    assert_has_error(sa, "'z' used before assignment")
    print("[PASS] Undeclared variable in condition detected")


def test_error_undeclared_in_while():
    """Analyzer: undeclared variable in while condition"""
    sa = analyze("while n > 0:\n    print(0)")
    assert_has_error(sa, "'n' used before assignment")
    print("[PASS] Undeclared variable in while condition detected")


def test_error_scope_isolation():
    """Analyzer: variable declared inside if-block is not visible outside"""
    source = """x = 10
if x > 5:
    inner = 1
print(inner)"""
    sa = analyze(source)
    assert_has_error(sa, "'inner' used before assignment")
    print("[PASS] Scope isolation - inner variable not visible outside block")


def test_error_multiple_undeclared():
    """Analyzer: multiple undeclared variables produce multiple errors"""
    sa = analyze("x = a + b")
    assert len(sa.errors) == 2, f"Expected 2 errors, got {len(sa.errors)}"
    print("[PASS] Multiple undeclared variables produce multiple errors")


# ─── Analyzer: warnings ──────────────────────────────────────────────────────

def test_warning_type_mismatch():
    """Analyzer: string + int produces type mismatch warning"""
    source = 'x = "hello"\ny = 5\nz = x + y'
    sa = analyze(source)
    assert_has_warning(sa, "Type mismatch")
    print("[PASS] Type mismatch warning produced for str + int")


def test_no_warning_int_arithmetic():
    """Analyzer: int + int produces no warnings"""
    sa = analyze("x = 5\ny = 3\nz = x + y")
    assert len(sa.warnings) == 0, f"Expected 0 warnings, got {len(sa.warnings)}"
    print("[PASS] No spurious warnings for valid int arithmetic")


def test_no_warning_string_concat():
    """Analyzer: string + string produces no warnings"""
    source = 'a = "hello"\nb = "world"\nc = a + b'
    sa = analyze(source)
    assert len(sa.warnings) == 0, f"Expected 0 warnings, got {len(sa.warnings)}"
    print("[PASS] No warnings for valid string concatenation")


# ─── Analyzer: get_report ─────────────────────────────────────────────────────

def test_get_report_clean():
    """Analyzer: get_report on clean program"""
    sa = analyze("x = 10\nprint(x)")
    report = sa.get_report()
    assert report['success'] is True
    assert len(report['errors']) == 0
    assert isinstance(report['symbols'], list)
    assert any(s['name'] == 'x' for s in report['symbols'])
    print(f"    Report: {report}")
    print("[PASS] get_report returns clean report")


def test_get_report_with_errors():
    """Analyzer: get_report includes errors"""
    sa = analyze("print(y)")
    report = sa.get_report()
    assert report['success'] is False
    assert len(report['errors']) == 1
    assert 'used before assignment' in report['errors'][0]['message']
    print(f"    Report: {report}")
    print("[PASS] get_report includes error details")


# ─── Run all tests ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("BrailleCode Semantic Analyzer - Test Suite")
    print("=" * 60)

    tests = [
        # Symbol table unit tests
        test_symbol_table_declare_and_lookup,
        test_symbol_table_nested_scopes,
        test_symbol_table_shadowing,
        test_symbol_table_depth,
        # Valid programs
        test_valid_simple_assignment,
        test_valid_variable_chain,
        test_valid_arithmetic,
        test_valid_if_else,
        test_valid_while_loop,
        test_valid_boolean_logic,
        test_valid_string_assignment,
        test_valid_none_assignment,
        test_valid_comparison_types,
        test_valid_complex_program,
        test_valid_nested_if,
        # Errors
        test_error_undeclared_variable,
        test_error_undeclared_in_expression,
        test_error_undeclared_in_condition,
        test_error_undeclared_in_while,
        test_error_scope_isolation,
        test_error_multiple_undeclared,
        # Warnings
        test_warning_type_mismatch,
        test_no_warning_int_arithmetic,
        test_no_warning_string_concat,
        # Report
        test_get_report_clean,
        test_get_report_with_errors,
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
