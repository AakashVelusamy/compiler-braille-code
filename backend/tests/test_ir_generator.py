"""
BrailleCode Compiler - IR Generator Tests
==========================================

Tests the Intermediate Code Generator (Phase 4):
converts validated AST to Three-Address Code (TAC).
"""

import sys
sys.path.insert(0, '.')

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser
from compiler.engine.ir_generator import IRGenerator


def compile_to_ir(source):
    """Helper: compile English source to TAC instructions."""
    t = Translator()
    braille = t.english_to_braille(source)
    tokens = Lexer(braille).tokenize()
    ast = Parser(tokens).parse()
    gen = IRGenerator()
    ir = gen.generate(ast)
    return ir, gen


# ─── Simple Statements ──────────────────────────────────────────────────────

def test_ir_simple_assign():
    """IR: simple assignment generates copy instruction."""
    ir, _ = compile_to_ir("x = 10")
    assert len(ir) == 2  # assign + halt
    assert ir[0].op == '='
    assert ir[0].result == 'x'
    assert ir[0].arg1 == '10'
    print("[PASS] Simple assignment")


def test_ir_multiple_assigns():
    """IR: multiple assignments generate separate instructions."""
    ir, _ = compile_to_ir("x = 5\ny = 10\nz = 15")
    assigns = [i for i in ir if i.op == '=']
    assert len(assigns) == 3
    assert assigns[0].result == 'x'
    assert assigns[1].result == 'y'
    assert assigns[2].result == 'z'
    print("[PASS] Multiple assignments")


# ─── Arithmetic ─────────────────────────────────────────────────────────────

def test_ir_binop_addition():
    """IR: binary addition generates temp and operation."""
    ir, _ = compile_to_ir("x = 3 + 4")
    arith = [i for i in ir if i.op == '+']
    assert len(arith) == 1
    assert arith[0].op == '+'
    assert arith[0].arg1 == '3'
    assert arith[0].arg2 == '4'
    assert arith[0].result.startswith('t')
    print("[PASS] Binary addition")


def test_ir_binop_all_ops():
    """IR: all binary operators generate correct instructions."""
    for op, source in [
        ('+', "x = 1 + 2"),
        ('-', "x = 5 - 3"),
        ('*', "x = 2 * 3"),
        ('/', "x = 10 / 2"),
        ('%', "x = 7 % 3"),
    ]:
        ir, _ = compile_to_ir(source)
        ops = [i for i in ir if i.op == op]
        assert len(ops) == 1, f"Expected {op} operation"
        assert ops[0].arg1 and ops[0].arg2
    print("[PASS] All binary operators")


def test_ir_operator_precedence():
    """IR: operator precedence generates correct evaluation order."""
    ir, _ = compile_to_ir("x = 2 + 3 * 4")
    # Should be: t0 = 3 * 4, t1 = 2 + t0, x = t1
    muls = [i for i in ir if i.op == '*']
    adds = [i for i in ir if i.op == '+']
    assert len(muls) == 1
    assert len(adds) == 1
    # mul should come before add (by instruction order)
    mul_idx = ir.index(muls[0])
    add_idx = ir.index(adds[0])
    assert mul_idx < add_idx
    print("[PASS] Operator precedence")


def test_ir_unary_minus():
    """IR: unary negation generates neg instruction."""
    ir, _ = compile_to_ir("x = -5")
    negs = [i for i in ir if i.op == '-' and not i.arg2]
    assert len(negs) == 1
    assert negs[0].arg1 == '5'
    print("[PASS] Unary minus")


# ─── Comparisons ────────────────────────────────────────────────────────────

def test_ir_comparison_all():
    """IR: all comparison operators generate correct instructions."""
    for op, source in [
        ('==', "x = 1 == 2"),
        ('!=', "x = 1 != 2"),
        ('<',  "x = 1 < 2"),
        ('>',  "x = 1 > 2"),
        ('<=', "x = 1 <= 2"),
        ('>=', "x = 1 >= 2"),
    ]:
        ir, _ = compile_to_ir(source)
        cmps = [i for i in ir if i.op == op]
        assert len(cmps) == 1, f"Expected {op} comparison"
    print("[PASS] All comparison operators")


# ─── Boolean Logic ──────────────────────────────────────────────────────────

def test_ir_boolean_and():
    """IR: 'and' operator generates boolean instruction."""
    ir, _ = compile_to_ir("x = 1 and 2")
    ands = [i for i in ir if i.op == 'and']
    assert len(ands) == 1
    assert ands[0].arg1 == '1'
    assert ands[0].arg2 == '2'
    print("[PASS] Boolean AND")


def test_ir_boolean_or():
    """IR: 'or' operator generates boolean instruction."""
    ir, _ = compile_to_ir("x = 1 or 0")
    ors = [i for i in ir if i.op == 'or']
    assert len(ors) == 1
    assert ors[0].arg1 == '1'
    assert ors[0].arg2 == '0'
    print("[PASS] Boolean OR")


def test_ir_boolean_not():
    """IR: 'not' operator generates unary instruction."""
    ir, _ = compile_to_ir("x = not 1")
    nots = [i for i in ir if i.op == 'not' and not i.arg2]
    assert len(nots) == 1
    assert nots[0].arg1 == '1'
    print("[PASS] Boolean NOT")


# ─── Control Flow: If/Else ──────────────────────────────────────────────────

def test_ir_if_statement():
    """IR: if statement generates labels and conditional jump."""
    source = """if x > 0:
    y = 1
else:
    y = 2"""
    ir, _ = compile_to_ir(source)

    # Should have labels for else branch
    labels = [i for i in ir if i.op == 'LABEL']
    assert len(labels) >= 2, "Expected at least 2 labels (else start, end)"

    # Should have conditional jump
    jumps = [i for i in ir if i.op == 'IF_FALSE']
    assert len(jumps) >= 1, "Expected IF_FALSE jump"

    print("[PASS] If statement")


def test_ir_if_elif_else():
    """IR: if/elif/else generates multiple branch labels."""
    source = """if x > 10:
    y = 1
elif x > 5:
    y = 2
else:
    y = 3"""
    ir, _ = compile_to_ir(source)

    labels = [i for i in ir if i.op == 'LABEL']
    jumps = [i for i in ir if i.op == 'IF_FALSE']
    gotos = [i for i in ir if i.op == 'GOTO']

    # Should have multiple labels and jumps for elif
    assert len(labels) >= 3, "Expected labels for elif branches"
    assert len(jumps) >= 2, "Expected multiple conditional jumps"

    print("[PASS] If/elif/else")


# ─── Loops ──────────────────────────────────────────────────────────────────

def test_ir_while_loop():
    """IR: while loop generates loop label and jump back."""
    source = """x = 5
while x > 0:
    x = x - 1"""
    ir, _ = compile_to_ir(source)

    labels = [i for i in ir if i.op == 'LABEL']
    gotos = [i for i in ir if i.op == 'GOTO']

    # Should have at least 2 labels (loop start, after loop)
    assert len(labels) >= 2, "Expected loop labels"
    # Should have GOTO to jump back to loop start
    assert len(gotos) >= 1, "Expected GOTO to loop start"

    print("[PASS] While loop")


def test_ir_nested_while():
    """IR: nested while loops generate separate label scopes."""
    source = """x = 3
while x > 0:
    y = 2
    while y > 0:
        y = y - 1
    x = x - 1"""
    ir, _ = compile_to_ir(source)

    labels = [i for i in ir if i.op == 'LABEL']
    # Each while needs at least 2 labels (start, end)
    # nested = 4+ labels
    assert len(labels) >= 4, "Expected labels for nested loops"

    print("[PASS] Nested while loops")


# ─── Print Statements ───────────────────────────────────────────────────────

def test_ir_print_simple():
    """IR: print statement generates PARAM and CALL."""
    ir, _ = compile_to_ir("print(5)")

    params = [i for i in ir if i.op == 'PARAM']
    calls = [i for i in ir if i.op == 'CALL']

    assert len(params) == 1, "Expected PARAM instruction"
    assert len(calls) == 1, "Expected CALL instruction"
    assert params[0].arg1 == '5'
    assert calls[0].arg1 == 'print'

    print("[PASS] Print simple")


def test_ir_print_expression():
    """IR: print with expression generates temp evaluation."""
    ir, _ = compile_to_ir("print(x + 5)")

    params = [i for i in ir if i.op == 'PARAM']
    calls = [i for i in ir if i.op == 'CALL']

    assert len(params) == 1, "Expected PARAM instruction"
    assert len(calls) == 1, "Expected CALL instruction"
    # PARAM should reference a temp or variable
    assert params[0].arg1 and (params[0].arg1.startswith('t') or params[0].arg1.isalpha())

    print("[PASS] Print expression")


# ─── Complex Programs ───────────────────────────────────────────────────────

def test_ir_fizzbuzz():
    """IR: FizzBuzz program generates complete TAC."""
    source = """n = 15
i = 1
while i <= n:
    if i % 3 == 0:
        print(i)
    i = i + 1"""
    ir, _ = compile_to_ir(source)

    assert len(ir) > 0
    # Should have assignments, comparisons, modulo, jumps, calls
    assert any(i.op == '=' for i in ir)
    assert any(i.op == '%' for i in ir)
    assert any(i.op == 'LABEL' for i in ir)
    assert any(i.op == 'IF_FALSE' for i in ir)
    assert any(i.op == 'CALL' for i in ir)

    print("[PASS] FizzBuzz program")


# ─── Temporaries ────────────────────────────────────────────────────────────

def test_ir_temp_generation():
    """IR: temporaries are numbered sequentially."""
    ir, gen = compile_to_ir("x = 1 + 2 + 3 + 4")

    temps = [i.result for i in ir if i.result.startswith('t')]

    # Should have multiple temporaries
    assert len(temps) >= 3, "Expected multiple temporaries for nested ops"

    # Extract numbers and verify they're sequential
    temp_nums = [int(t[1:]) for t in temps]
    assert temp_nums == sorted(temp_nums), "Temporaries should be sequential"

    print("[PASS] Temporary generation")


def test_ir_label_generation():
    """IR: labels are numbered sequentially."""
    source = """if x > 0:
    y = 1
else:
    y = 2
if z > 0:
    w = 1
else:
    w = 2"""
    ir, gen = compile_to_ir(source)

    labels = [i.label for i in ir if i.op == 'LABEL']

    # Should have multiple labels
    assert len(labels) >= 2, "Expected multiple labels"

    # Extract numbers and verify they're sequential
    label_nums = [int(l[1:]) for l in labels]
    assert label_nums == sorted(label_nums), "Labels should be sequential"

    print("[PASS] Label generation")


# ─── Halt Instruction ───────────────────────────────────────────────────────

def test_ir_halt():
    """IR: every program ends with HALT."""
    for source in ["x = 1", "print(1)", "if x > 0:\n    y = 1"]:
        ir, _ = compile_to_ir(source)
        assert ir[-1].op == 'HALT', f"Expected HALT at end of program: {source}"

    print("[PASS] HALT instruction")


# ─── Text Representation ────────────────────────────────────────────────────

def test_ir_text_format():
    """IR: to_text() produces readable output."""
    ir, gen = compile_to_ir("x = 10")
    text = gen.to_text()

    assert isinstance(text, str)
    assert "=" in text or "x" in text
    assert "HALT" in text

    print("[PASS] Text format")


def test_ir_list_format():
    """IR: to_list() produces JSON-serializable structure."""
    ir, gen = compile_to_ir("x = 10")
    lst = gen.to_list()

    assert isinstance(lst, list)
    assert len(lst) > 0

    for item in lst:
        assert 'op' in item
        assert 'result' in item
        assert 'arg1' in item
        assert 'arg2' in item
        assert 'index' in item
        assert 'text' in item

    print("[PASS] List format")


# ─── Entry Point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BrailleCode IR Generator – Test Suite")
    print("="*60 + "\n")

    passed = failed = 0

    tests = [
        test_ir_simple_assign,
        test_ir_multiple_assigns,
        test_ir_binop_addition,
        test_ir_binop_all_ops,
        test_ir_operator_precedence,
        test_ir_unary_minus,
        test_ir_comparison_all,
        test_ir_boolean_and,
        test_ir_boolean_or,
        test_ir_boolean_not,
        test_ir_if_statement,
        test_ir_if_elif_else,
        test_ir_while_loop,
        test_ir_nested_while,
        test_ir_print_simple,
        test_ir_print_expression,
        test_ir_fizzbuzz,
        test_ir_temp_generation,
        test_ir_label_generation,
        test_ir_halt,
        test_ir_text_format,
        test_ir_list_format,
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
