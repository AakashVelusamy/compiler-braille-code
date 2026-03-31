"""
Tests for the Parser + AST
============================

Run from the project root:
    cd braillecode/backend
    python -m tests.test_parser
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser, ParseError
from compiler.engine.ast_nodes import (
    Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
    ast_to_dict, print_ast,
)


# ─── Helper ───────────────────────────────────────────────────────────────────

translator = Translator()


def parse(source: str) -> Program:
    """English source → Braille → tokens → AST."""
    braille = translator.english_to_braille(source)
    lexer = Lexer(braille)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_simple_assignment():
    """Parser: x = 10"""
    ast = parse("x = 10")
    print_ast(ast)

    assert len(ast.body) == 1
    stmt = ast.body[0]
    assert isinstance(stmt, Assign)
    assert stmt.name == 'x'
    assert isinstance(stmt.value, Number)
    assert stmt.value.value == 10
    print("[PASS] Simple assignment parsed correctly")


def test_string_assignment():
    """Parser: msg = "hello" """
    ast = parse('msg = "hello"')
    print_ast(ast)

    stmt = ast.body[0]
    assert isinstance(stmt, Assign)
    assert stmt.name == 'msg'
    assert isinstance(stmt.value, String)
    assert stmt.value.value == 'hello'
    print("[PASS] String assignment parsed correctly")


def test_boolean_assignment():
    """Parser: flag = True"""
    ast = parse("flag = True")
    stmt = ast.body[0]
    assert isinstance(stmt.value, Boolean)
    assert stmt.value.value is True

    ast2 = parse("flag = False")
    assert ast2.body[0].value.value is False
    print("[PASS] Boolean assignment parsed correctly")


def test_none_assignment():
    """Parser: x = None"""
    ast = parse("x = None")
    stmt = ast.body[0]
    assert isinstance(stmt.value, NoneValue)
    print("[PASS] None assignment parsed correctly")


def test_variable_to_variable():
    """Parser: y = x"""
    ast = parse("y = x")
    stmt = ast.body[0]
    assert isinstance(stmt, Assign)
    assert stmt.name == 'y'
    assert isinstance(stmt.value, Identifier)
    assert stmt.value.name == 'x'
    print("[PASS] Variable-to-variable assignment parsed correctly")


def test_arithmetic_precedence():
    """Parser: x = 2 + 3 * 4  → BinOp(+, 2, BinOp(*, 3, 4))"""
    ast = parse("x = 2 + 3 * 4")
    print_ast(ast)

    expr = ast.body[0].value
    # Should be: 2 + (3 * 4) due to precedence
    assert isinstance(expr, BinOp)
    assert expr.op == '+'
    assert isinstance(expr.left, Number) and expr.left.value == 2
    assert isinstance(expr.right, BinOp)
    assert expr.right.op == '*'
    assert expr.right.left.value == 3
    assert expr.right.right.value == 4
    print("[PASS] Arithmetic precedence (+ vs *) correct")


def test_parenthesized_expression():
    """Parser: x = (2 + 3) * 4  → BinOp(*, BinOp(+, 2, 3), 4)"""
    ast = parse("x = (2 + 3) * 4")
    print_ast(ast)

    expr = ast.body[0].value
    assert isinstance(expr, BinOp)
    assert expr.op == '*'
    assert isinstance(expr.left, BinOp)
    assert expr.left.op == '+'
    assert expr.left.left.value == 2
    assert expr.left.right.value == 3
    assert isinstance(expr.right, Number) and expr.right.value == 4
    print("[PASS] Parenthesized expression changes precedence")


def test_unary_minus():
    """Parser: x = -5"""
    ast = parse("x = -5")
    print_ast(ast)

    expr = ast.body[0].value
    assert isinstance(expr, UnaryOp)
    assert expr.op == '-'
    assert isinstance(expr.operand, Number)
    assert expr.operand.value == 5
    print("[PASS] Unary minus parsed correctly")


def test_comparison():
    """Parser: x = a > 5"""
    ast = parse("x = a > 5")
    print_ast(ast)

    expr = ast.body[0].value
    assert isinstance(expr, Compare)
    assert expr.op == '>'
    assert isinstance(expr.left, Identifier)
    assert isinstance(expr.right, Number)
    print("[PASS] Comparison parsed correctly")


def test_all_comparison_operators():
    """Parser: all 6 comparison operators"""
    ops = ['==', '!=', '<', '>', '<=', '>=']
    for op in ops:
        ast = parse(f"x = a {op} b")
        expr = ast.body[0].value
        assert isinstance(expr, Compare), f"Expected Compare for {op}"
        assert expr.op == op, f"Expected op '{op}', got '{expr.op}'"
        print(f"    {op} → Compare OK")
    print("[PASS] All comparison operators parsed correctly")


def test_boolean_and_or():
    """Parser: x = a and b or c"""
    ast = parse("x = a and b or c")
    print_ast(ast)

    # 'or' is lower precedence than 'and', so: (a and b) or c
    expr = ast.body[0].value
    assert isinstance(expr, BoolOp)
    assert expr.op == 'or'
    assert isinstance(expr.left, BoolOp)
    assert expr.left.op == 'and'
    print("[PASS] Boolean and/or precedence correct")


def test_not_operator():
    """Parser: x = not True"""
    ast = parse("x = not True")
    print_ast(ast)

    expr = ast.body[0].value
    assert isinstance(expr, UnaryOp)
    assert expr.op == 'not'
    assert isinstance(expr.operand, Boolean)
    print("[PASS] not operator parsed correctly")


def test_print_statement():
    """Parser: print(42)"""
    ast = parse("print(42)")
    print_ast(ast)

    stmt = ast.body[0]
    assert isinstance(stmt, Print)
    assert isinstance(stmt.value, Number)
    assert stmt.value.value == 42
    print("[PASS] Print statement parsed correctly")


def test_print_expression():
    """Parser: print(x + 1)"""
    ast = parse("print(x + 1)")
    print_ast(ast)

    stmt = ast.body[0]
    assert isinstance(stmt, Print)
    assert isinstance(stmt.value, BinOp)
    assert stmt.value.op == '+'
    print("[PASS] Print with expression parsed correctly")


def test_if_statement():
    """Parser: if x > 5: print(x)"""
    source = "if x > 5:\n    print(x)"
    ast = parse(source)
    print_ast(ast)

    stmt = ast.body[0]
    assert isinstance(stmt, If)
    assert isinstance(stmt.condition, Compare)
    assert len(stmt.body) == 1
    assert isinstance(stmt.body[0], Print)
    assert stmt.else_body is None
    print("[PASS] If statement parsed correctly")


def test_if_else():
    """Parser: if/else"""
    source = "if x > 0:\n    print(x)\nelse:\n    print(0)"
    ast = parse(source)
    print_ast(ast)

    stmt = ast.body[0]
    assert isinstance(stmt, If)
    assert len(stmt.body) == 1
    assert stmt.else_body is not None
    assert len(stmt.else_body) == 1
    assert isinstance(stmt.else_body[0], Print)
    print("[PASS] If/else parsed correctly")


def test_if_elif_else():
    """Parser: if/elif/else chain"""
    source = """x = 10
if x > 20:
    print(3)
elif x > 5:
    print(2)
else:
    print(1)"""
    ast = parse(source)
    print_ast(ast)

    if_stmt = ast.body[1]
    assert isinstance(if_stmt, If)
    assert len(if_stmt.elif_clauses) == 1
    assert if_stmt.else_body is not None
    # elif condition
    elif_cond, elif_body = if_stmt.elif_clauses[0]
    assert isinstance(elif_cond, Compare)
    assert len(elif_body) == 1
    print("[PASS] If/elif/else chain parsed correctly")


def test_while_loop():
    """Parser: while loop"""
    source = """x = 5
while x > 0:
    print(x)
    x = x - 1"""
    ast = parse(source)
    print_ast(ast)

    assert len(ast.body) == 2
    while_stmt = ast.body[1]
    assert isinstance(while_stmt, While)
    assert isinstance(while_stmt.condition, Compare)
    assert len(while_stmt.body) == 2  # print + assignment
    print("[PASS] While loop parsed correctly")


def test_nested_if():
    """Parser: nested if inside if"""
    source = """if True:
    if False:
        x = 1"""
    ast = parse(source)
    print_ast(ast)

    outer = ast.body[0]
    assert isinstance(outer, If)
    inner = outer.body[0]
    assert isinstance(inner, If)
    print("[PASS] Nested if parsed correctly")


def test_modulo_divide():
    """Parser: x = 10 % 3 + 8 / 2"""
    ast = parse("x = 10 % 3 + 8 / 2")
    print_ast(ast)

    expr = ast.body[0].value
    # Should be: (10 % 3) + (8 / 2) - same precedence for %, /, and *, left-assoc within +
    assert isinstance(expr, BinOp)
    assert expr.op == '+'
    assert isinstance(expr.left, BinOp) and expr.left.op == '%'
    assert isinstance(expr.right, BinOp) and expr.right.op == '/'
    print("[PASS] Modulo and divide precedence correct")


def test_complex_program():
    """Parser: multi-statement program with all features"""
    source = """x = 10
y = 20
z = x + y * 2
if z > 30:
    print(z)
    z = z - 1
elif z == 30:
    print(0)
else:
    print(-1)
while x > 0:
    x = x - 1
print(x)"""
    ast = parse(source)
    print_ast(ast)

    assert len(ast.body) == 6  # 3 assigns + if + while + print
    assert isinstance(ast.body[0], Assign)
    assert isinstance(ast.body[3], If)
    assert isinstance(ast.body[4], While)
    assert isinstance(ast.body[5], Print)
    print("[PASS] Complex multi-statement program parsed correctly")


def test_ast_to_dict():
    """Parser: ast_to_dict produces valid JSON-serializable structure"""
    ast = parse("x = 2 + 3")
    d = ast_to_dict(ast)
    json_str = json.dumps(d, indent=2)
    print(f"    JSON output ({len(json_str)} chars):")
    print(f"    {json_str[:200]}...")
    assert d['type'] == 'Program'
    assert len(d['body']) == 1
    assert d['body'][0]['type'] == 'Assign'
    print("[PASS] ast_to_dict produces valid JSON structure")


def test_line_numbers_in_ast():
    """Parser: AST nodes carry correct line numbers"""
    source = "x = 1\ny = 2\nprint(x)"
    ast = parse(source)

    assert ast.body[0].line == 1  # x = 1
    assert ast.body[1].line == 2  # y = 2
    assert ast.body[2].line == 3  # print(x)
    print("[PASS] Line numbers correct in AST nodes")


# ─── Run all tests ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("BrailleCode Parser - Test Suite")
    print("=" * 60)

    tests = [
        test_simple_assignment,
        test_string_assignment,
        test_boolean_assignment,
        test_none_assignment,
        test_variable_to_variable,
        test_arithmetic_precedence,
        test_parenthesized_expression,
        test_unary_minus,
        test_comparison,
        test_all_comparison_operators,
        test_boolean_and_or,
        test_not_operator,
        test_print_statement,
        test_print_expression,
        test_if_statement,
        test_if_else,
        test_if_elif_else,
        test_while_loop,
        test_nested_if,
        test_modulo_divide,
        test_complex_program,
        test_ast_to_dict,
        test_line_numbers_in_ast,
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
