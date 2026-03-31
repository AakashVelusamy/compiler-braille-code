"""
Tests for the Lexer
====================

Run from the project root:
    cd braillecode/backend
    python -m tests.test_lexer
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer, LexerError
from compiler.engine.tokens import Token, TokenType


# Helper: translate English → Braille → tokenize
t = Translator()


def lex(source: str):
    """Shortcut: English source → Braille → token list."""
    braille = t.english_to_braille(source)
    lexer = Lexer(braille)
    return lexer.tokenize()


def token_types(tokens):
    """Extract just the TokenType list (excluding EOF)."""
    return [tok.type for tok in tokens if tok.type != TokenType.EOF]


def print_tokens(tokens):
    """Pretty-print a token list for debugging."""
    for tok in tokens:
        print(f"    {tok}")


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_simple_assignment():
    """Lexer: x = 10"""
    tokens = lex("x = 10")
    print_tokens(tokens)

    types = token_types(tokens)
    assert TokenType.IDENTIFIER in types, "Missing IDENTIFIER"
    assert TokenType.ASSIGN in types, "Missing ASSIGN"
    assert TokenType.INTEGER in types, "Missing INTEGER"

    # Check values
    id_tok = [t for t in tokens if t.type == TokenType.IDENTIFIER][0]
    int_tok = [t for t in tokens if t.type == TokenType.INTEGER][0]
    assert id_tok.value == 'x'
    assert int_tok.value == 10
    print("[PASS] Simple assignment tokenized correctly")


def test_arithmetic():
    """Lexer: result = a + b * 2"""
    tokens = lex("result = a + b * 2")
    print_tokens(tokens)

    types = token_types(tokens)
    assert types.count(TokenType.IDENTIFIER) == 3  # result, a, b
    assert TokenType.PLUS in types
    assert TokenType.MULTIPLY in types
    assert TokenType.ASSIGN in types
    assert TokenType.INTEGER in types
    print("[PASS] Arithmetic expression tokenized correctly")


def test_comparison_operators():
    """Lexer: x == 5, y != 3, a <= b, c >= d, e < f, g > h"""
    tests = [
        ("x == 5",  TokenType.EQUAL),
        ("y != 3",  TokenType.NOT_EQUAL),
        ("a <= b",  TokenType.LESS_EQ),
        ("c >= d",  TokenType.GREATER_EQ),
        ("e < f",   TokenType.LESS),
        ("g > h",   TokenType.GREATER),
    ]
    for source, expected_op in tests:
        tokens = lex(source)
        types = token_types(tokens)
        assert expected_op in types, f"Missing {expected_op.name} in '{source}'"
        print(f"    '{source}' → {expected_op.name} OK")

    print("[PASS] All comparison operators tokenized correctly")


def test_keywords():
    """Lexer: all keywords produce correct token types"""
    keyword_tests = [
        ("print(x)",  TokenType.PRINT),
        ("if x:",     TokenType.IF),
        ("else:",     TokenType.ELSE),
        ("elif x:",   TokenType.ELIF),
        ("while x:",  TokenType.WHILE),
        ("x = True",  TokenType.TRUE),
        ("x = False", TokenType.FALSE),
        ("x and y",   TokenType.AND),
        ("x or y",    TokenType.OR),
        ("not x",     TokenType.NOT),
        ("x = None",  TokenType.NONE),
    ]
    for source, expected_kw in keyword_tests:
        tokens = lex(source)
        types = token_types(tokens)
        assert expected_kw in types, f"Missing {expected_kw.name} in '{source}'"
        print(f"    '{source}' → {expected_kw.name} OK")

    print("[PASS] All keywords tokenized correctly")


def test_string_literal():
    """Lexer: print("hello world")"""
    tokens = lex('print("hello world")')
    print_tokens(tokens)

    str_tok = [t for t in tokens if t.type == TokenType.STRING][0]
    assert str_tok.value == "hello world", f"Expected 'hello world', got '{str_tok.value}'"
    print("[PASS] String literal tokenized correctly")


def test_parentheses():
    """Lexer: parentheses produce LPAREN and RPAREN"""
    tokens = lex("print(x)")
    types = token_types(tokens)
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    print("[PASS] Parentheses tokenized correctly")


def test_single_indent():
    """Lexer: one level of indentation produces INDENT"""
    source = "if True:\n    x = 1"
    tokens = lex(source)
    print_tokens(tokens)

    types = token_types(tokens)
    assert TokenType.INDENT in types, "Missing INDENT token"
    print("[PASS] Single indent level detected")


def test_indent_dedent():
    """Lexer: indent then dedent back to base level"""
    source = "if True:\n    x = 1\ny = 2"
    tokens = lex(source)
    print_tokens(tokens)

    types = token_types(tokens)
    assert TokenType.INDENT in types, "Missing INDENT"
    assert TokenType.DEDENT in types, "Missing DEDENT"
    print("[PASS] INDENT + DEDENT pair detected")


def test_nested_indent():
    """Lexer: two levels of nested indentation"""
    source = "if True:\n    if False:\n        x = 1\ny = 2"
    tokens = lex(source)
    print_tokens(tokens)

    types = token_types(tokens)
    indent_count = types.count(TokenType.INDENT)
    dedent_count = types.count(TokenType.DEDENT)
    assert indent_count == 2, f"Expected 2 INDENTs, got {indent_count}"
    assert dedent_count == 2, f"Expected 2 DEDENTs, got {dedent_count}"
    print("[PASS] Nested indentation (2 levels) handled correctly")


def test_multiline_program():
    """Lexer: complete multi-line program with if/else"""
    source = """x = 10
if x > 5:
    print(x)
else:
    print(0)"""
    tokens = lex(source)
    print_tokens(tokens)

    types = token_types(tokens)
    assert TokenType.IF in types
    assert TokenType.ELSE in types
    assert types.count(TokenType.PRINT) == 2
    assert TokenType.INDENT in types
    assert TokenType.DEDENT in types
    print("[PASS] Multi-line program tokenized correctly")


def test_while_loop():
    """Lexer: while loop with decrement"""
    source = """x = 5
while x > 0:
    print(x)
    x = x - 1"""
    tokens = lex(source)
    print_tokens(tokens)

    types = token_types(tokens)
    assert TokenType.WHILE in types
    assert TokenType.MINUS in types
    assert TokenType.INDENT in types
    print("[PASS] While loop tokenized correctly")


def test_identifier_with_underscore():
    """Lexer: identifier with underscore like my_var"""
    tokens = lex("my_var = 42")
    print_tokens(tokens)

    id_tok = [t for t in tokens if t.type == TokenType.IDENTIFIER][0]
    assert id_tok.value == "my_var", f"Expected 'my_var', got '{id_tok.value}'"
    print("[PASS] Underscore identifier tokenized correctly")


def test_line_numbers():
    """Lexer: tokens carry correct line numbers"""
    source = "x = 1\ny = 2\nz = 3"
    tokens = lex(source)

    # Find tokens on each line
    line1_toks = [t for t in tokens if t.line == 1 and t.type != TokenType.NEWLINE]
    line2_toks = [t for t in tokens if t.line == 2 and t.type != TokenType.NEWLINE]
    line3_toks = [t for t in tokens if t.line == 3 and t.type not in (TokenType.NEWLINE, TokenType.EOF)]

    assert len(line1_toks) > 0, "No tokens on line 1"
    assert len(line2_toks) > 0, "No tokens on line 2"
    assert len(line3_toks) > 0, "No tokens on line 3"
    print("[PASS] Line numbers tracked correctly")


def test_eof_token():
    """Lexer: token stream always ends with EOF"""
    tokens = lex("x = 1")
    assert tokens[-1].type == TokenType.EOF, "Last token must be EOF"
    print("[PASS] EOF token present at end")


def test_modulo_operator():
    """Lexer: modulo operator %"""
    tokens = lex("x = 10 % 3")
    print_tokens(tokens)
    types = token_types(tokens)
    assert TokenType.MODULO in types
    print("[PASS] Modulo operator tokenized correctly")


def test_divide_operator():
    """Lexer: divide operator /"""
    tokens = lex("x = 10 / 2")
    types = token_types(tokens)
    assert TokenType.DIVIDE in types
    print("[PASS] Divide operator tokenized correctly")


def test_boolean_operators():
    """Lexer: and, or, not"""
    tokens = lex("x and y or not z")
    print_tokens(tokens)
    types = token_types(tokens)
    assert TokenType.AND in types
    assert TokenType.OR in types
    assert TokenType.NOT in types
    print("[PASS] Boolean operators tokenized correctly")


def test_comma_in_print():
    """Lexer: comma separator"""
    # We don't support multi-arg print yet in the grammar,
    # but the lexer should still produce COMMA tokens
    tokens = lex("print(x)")
    # Just verify no crash; comma test with actual comma:
    # For now, ensure print + parens work cleanly
    types = token_types(tokens)
    assert TokenType.PRINT in types
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    print("[PASS] Print with parentheses tokenized correctly")


# ─── Run all tests ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("BrailleCode Lexer - Test Suite")
    print("=" * 60)

    tests = [
        test_simple_assignment,
        test_arithmetic,
        test_comparison_operators,
        test_keywords,
        test_string_literal,
        test_parentheses,
        test_single_indent,
        test_indent_dedent,
        test_nested_indent,
        test_multiline_program,
        test_while_loop,
        test_identifier_with_underscore,
        test_line_numbers,
        test_eof_token,
        test_modulo_operator,
        test_divide_operator,
        test_boolean_operators,
        test_comma_in_print,
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
