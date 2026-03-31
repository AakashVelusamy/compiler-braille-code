"""
Tests for braille_map.py and translator.py
===========================================

Run from the project root:
    cd braillecode/backend
    python -m pytest tests/ -v

Or without pytest:
    cd braillecode/backend
    python -m tests.test_translator
"""

import sys
import os

# Add parent directory so imports work when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compiler.engine.braille_map import (
    LETTERS, DIGITS, OPERATORS, KEYWORDS, PUNCTUATION,
    NUMBER_PREFIX, KEYWORD_PREFIX, CAPITAL_PREFIX,
    REVERSE_LETTERS, REVERSE_DIGITS, REVERSE_KEYWORDS,
    get_full_mapping,
)
from compiler.engine.translator import Translator


def test_braille_map_completeness():
    """All 26 letters and 10 digits must be mapped."""
    assert len(LETTERS) == 26, f"Expected 26 letters, got {len(LETTERS)}"
    assert len(DIGITS) == 10, f"Expected 10 digits, got {len(DIGITS)}"
    print("[PASS] Braille map has all 26 letters and 10 digits")


def test_reverse_maps_match():
    """Reverse maps must be exact inverses of forward maps."""
    for eng, brl in LETTERS.items():
        assert REVERSE_LETTERS[brl] == eng, f"Reverse mismatch: {brl} -> {REVERSE_LETTERS[brl]} != {eng}"
    for eng, brl in DIGITS.items():
        assert REVERSE_DIGITS[brl] == eng
    for eng, brl in KEYWORDS.items():
        assert REVERSE_KEYWORDS[brl] == eng
    print("[PASS] All reverse mappings are correct inverses")


def test_no_collisions():
    """No two different characters should map to the same Braille pattern."""
    all_braille = list(LETTERS.values())
    assert len(all_braille) == len(set(all_braille)), "Collision found in letter mappings!"

    all_operators = list(OPERATORS.values())
    assert len(all_operators) == len(set(all_operators)), "Collision found in operator mappings!"

    all_keywords = list(KEYWORDS.values())
    assert len(all_keywords) == len(set(all_keywords)), "Collision found in keyword mappings!"
    print("[PASS] No Braille pattern collisions detected")


def test_translate_simple_assignment():
    """Test: x = 10"""
    t = Translator()
    braille = t.english_to_braille("x = 10")
    print(f"  'x = 10' → '{braille}'")

    # x is a letter, = is operator, 10 is number
    assert LETTERS['x'] in braille
    assert OPERATORS['='] in braille
    assert NUMBER_PREFIX in braille
    print("[PASS] Simple assignment translates correctly")


def test_translate_keyword_print():
    """Test: print("hello")"""
    t = Translator()
    braille = t.english_to_braille('print("hello")')
    print(f'  \'print("hello")\' → \'{braille}\'')

    assert KEYWORD_PREFIX in braille
    assert KEYWORDS['print'] in braille
    print("[PASS] print keyword translates correctly")


def test_translate_if_statement():
    """Test: if x > 5:"""
    t = Translator()
    braille = t.english_to_braille("if x > 5:")
    print(f"  'if x > 5:' → '{braille}'")

    assert KEYWORD_PREFIX in braille
    assert KEYWORDS['if'] in braille
    assert OPERATORS['>'] in braille
    print("[PASS] if-statement translates correctly")


def test_translate_indented_block():
    """Test indentation handling."""
    t = Translator()
    source = "if True:\n    x = 1"
    braille = t.english_to_braille(source)
    print(f"  Multi-line indented block → '{braille}'")

    # The second line should contain Braille indent characters
    assert '⠀⠀' in braille  # BRAILLE_INDENT present
    print("[PASS] Indentation translates correctly")


def test_round_trip_simple():
    """Translate English → Braille → English and verify it matches."""
    t = Translator()

    test_cases = [
        "x = 10",
        "y = 5",
        "print(x)",
    ]

    for source in test_cases:
        braille = t.english_to_braille(source)
        back = t.braille_to_english(braille)
        # Normalize whitespace for comparison
        source_norm = source.strip()
        back_norm = back.strip()
        assert source_norm == back_norm, (
            f"Round-trip failed:\n"
            f"  Original:    '{source_norm}'\n"
            f"  Braille:     '{braille}'\n"
            f"  Back:        '{back_norm}'"
        )
        print(f"  Round-trip OK: '{source_norm}' → '{braille}' → '{back_norm}'")

    print("[PASS] All round-trip tests passed")


def test_translate_while_loop():
    """Test: while x > 0:"""
    t = Translator()
    braille = t.english_to_braille("while x > 0:")
    print(f"  'while x > 0:' → '{braille}'")

    assert KEYWORD_PREFIX in braille
    assert KEYWORDS['while'] in braille
    print("[PASS] while-loop translates correctly")


def test_translate_arithmetic():
    """Test: result = a + b * 2"""
    t = Translator()
    braille = t.english_to_braille("result = a + b * 2")
    print(f"  'result = a + b * 2' → '{braille}'")

    assert OPERATORS['+'] in braille
    assert OPERATORS['*'] in braille
    assert OPERATORS['='] in braille
    print("[PASS] Arithmetic expression translates correctly")


def test_get_full_mapping():
    """get_full_mapping() should return all categories."""
    m = get_full_mapping()
    assert 'letters' in m
    assert 'digits' in m
    assert 'operators' in m
    assert 'keywords' in m
    assert 'prefixes' in m
    assert 'whitespace' in m
    print("[PASS] get_full_mapping() returns all categories")


def test_multiline_program():
    """Test a complete multi-line program."""
    t = Translator()
    program = """x = 10
if x > 5:
    print(x)
else:
    print(0)"""

    braille = t.english_to_braille(program)
    print(f"\n  Full program translated ({len(braille)} Braille chars)")
    print(f"  Preview: {braille[:80]}...")

    # Verify it contains the right keywords
    assert KEYWORDS['if'] in braille
    assert KEYWORDS['else'] in braille
    assert KEYWORDS['print'] in braille
    print("[PASS] Multi-line program translates correctly")


# ─── Run all tests ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("BrailleCode Translator - Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_braille_map_completeness,
        test_reverse_maps_match,
        test_no_collisions,
        test_translate_simple_assignment,
        test_translate_keyword_print,
        test_translate_if_statement,
        test_translate_indented_block,
        test_round_trip_simple,
        test_translate_while_loop,
        test_translate_arithmetic,
        test_get_full_mapping,
        test_multiline_program,
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
            failed += 1

    print()
    print("=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
