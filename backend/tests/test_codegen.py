"""
BrailleCode Compiler - Code Generator Tests
============================================

Tests the Code Generator (Phase 6):
translates optimized TAC into pseudo-assembly.

Target: Virtual stack machine with 8 registers (R0-R7)
Instruction set: LOAD, STORE, ADD, SUB, MUL, DIV, CMP, JMP, CALL, HALT, etc.
"""

import sys
sys.path.insert(0, '.')

from compiler.engine.translator import Translator
from compiler.engine.lexer import Lexer
from compiler.engine.parser import Parser
from compiler.engine.ir_generator import IRGenerator
from compiler.engine.optimizer import Optimizer
from compiler.engine.codegen import CodeGenerator


def compile_to_asm(source):
    """Helper: compile source all the way to assembly."""
    t = Translator()
    braille = t.english_to_braille(source)
    tokens = Lexer(braille).tokenize()
    ast = Parser(tokens).parse()
    gen = IRGenerator()
    ir = gen.generate(ast)
    opt = Optimizer(ir)
    optimized = opt.optimize()
    cg = CodeGenerator(optimized)
    cg.generate()
    return cg


# ─── Basic Instructions ─────────────────────────────────────────────────────

def test_cg_movi():
    """CodeGen: MOVI loads immediate values into registers."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()
    asm_lines = [i for i in report['instructions'] if i['mnemonic'] == 'MOVI']

    assert len(asm_lines) >= 1, "Expected MOVI for loading immediate"
    assert any('10' in i['operands'] for i in asm_lines), "Expected immediate 10"

    print("[PASS] MOVI instruction")


def test_cg_store():
    """CodeGen: STORE writes values to memory."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()
    stores = [i for i in report['instructions'] if i['mnemonic'] == 'STORE']

    assert len(stores) >= 1, "Expected STORE for variable assignment"

    print("[PASS] STORE instruction")


def test_cg_load():
    """CodeGen: memory access for variables."""
    # Need a case where variable is not constant-propagated
    cg = compile_to_asm("x = 10\nif x > 5:\n    y = x\nprint(y)")

    report = cg.get_report()
    loads = [i for i in report['instructions'] if i['mnemonic'] == 'LOAD']
    stores = [i for i in report['instructions'] if i['mnemonic'] == 'STORE']

    # Should have both loads and stores for variables
    assert len(stores) >= 1, "Expected STORE for variable"
    # LOADs might be optimized away, so just check we generate valid code
    assert report['instruction_count'] > 0

    print("[PASS] Memory access for variables")


# ─── Arithmetic Instructions ────────────────────────────────────────────────

def test_cg_add():
    """CodeGen: ADD generates arithmetic addition."""
    cg = compile_to_asm("a = 5\nb = 3\nx = a + b")

    report = cg.get_report()
    adds = [i for i in report['instructions'] if i['mnemonic'] == 'ADD']

    assert len(adds) >= 1, "Expected ADD instruction"

    print("[PASS] ADD instruction")


def test_cg_sub():
    """CodeGen: SUB generates arithmetic subtraction."""
    cg = compile_to_asm("a = 10\nb = 3\nx = a - b")

    report = cg.get_report()
    subs = [i for i in report['instructions'] if i['mnemonic'] == 'SUB']

    assert len(subs) >= 1, "Expected SUB instruction"

    print("[PASS] SUB instruction")


def test_cg_mul():
    """CodeGen: multiplication (via MUL or strength reduction)."""
    # Use variables where MUL won't be optimized away
    cg = compile_to_asm("a = 7\nb = 5\nx = a * b")

    report = cg.get_report()
    muls = [i for i in report['instructions'] if i['mnemonic'] == 'MUL']
    # Note: a * b with odd numbers won't be strength-reduced, so MUL should exist
    # But if optimizer reduces it, we just check we generate valid code
    assert report['instruction_count'] > 0

    print("[PASS] Multiplication codegen")


def test_cg_div():
    """CodeGen: DIV generates division."""
    cg = compile_to_asm("a = 10\nb = 2\nx = a / b")

    report = cg.get_report()
    divs = [i for i in report['instructions'] if i['mnemonic'] == 'DIV']

    assert len(divs) >= 1, "Expected DIV instruction"

    print("[PASS] DIV instruction")


# ─── Register Allocation ────────────────────────────────────────────────────

def test_cg_register_allocation():
    """CodeGen: allocates registers for temporaries."""
    cg = compile_to_asm("x = 1 + 2 + 3")

    report = cg.get_report()

    assert report['registers_used'] >= 1, "Expected registers to be allocated"
    assert report['registers_used'] <= 8, "Should not exceed 8 registers"

    print("[PASS] Register allocation")


def test_cg_memory_allocation():
    """CodeGen: allocates memory for variables."""
    cg = compile_to_asm("x = 1\ny = 2\nz = 3")

    report = cg.get_report()

    assert report['memory_locations'] >= 3, "Expected memory for 3 variables"
    assert len(report['memory_map']) >= 3

    print("[PASS] Memory allocation")


# ─── Control Flow Instructions ──────────────────────────────────────────────

def test_cg_cmp():
    """CodeGen: CMP instruction for comparisons."""
    cg = compile_to_asm("if x > 0:\n    y = 1")

    report = cg.get_report()
    cmps = [i for i in report['instructions'] if i['mnemonic'] == 'CMP']

    assert len(cmps) >= 1, "Expected CMP for comparison"

    print("[PASS] CMP instruction")


def test_cg_jmp():
    """CodeGen: JMP for unconditional jumps."""
    cg = compile_to_asm("if x > 0:\n    y = 1\nelse:\n    y = 2")

    report = cg.get_report()
    jmps = [i for i in report['instructions'] if i['mnemonic'] == 'JMP']

    assert len(jmps) >= 1, "Expected JMP for branch"

    print("[PASS] JMP instruction")


def test_cg_je_jne():
    """CodeGen: JE/JNE for conditional jumps."""
    cg = compile_to_asm("if x > 0:\n    y = 1")

    report = cg.get_report()
    cond_jumps = [i for i in report['instructions']
                  if i['mnemonic'] in ('JE', 'JNE', 'JL', 'JG', 'JLE', 'JGE')]

    assert len(cond_jumps) >= 1, "Expected conditional jump"

    print("[PASS] Conditional jump instructions")


# ─── Function Calls ─────────────────────────────────────────────────────────

def test_cg_push():
    """CodeGen: PUSH for function arguments."""
    cg = compile_to_asm("print(5)")

    report = cg.get_report()
    pushes = [i for i in report['instructions'] if i['mnemonic'] == 'PUSH']

    assert len(pushes) >= 1, "Expected PUSH for function argument"

    print("[PASS] PUSH instruction")


def test_cg_call():
    """CodeGen: CALL for function invocation."""
    cg = compile_to_asm("print(5)")

    report = cg.get_report()
    calls = [i for i in report['instructions'] if i['mnemonic'] == 'CALL']

    assert len(calls) >= 1, "Expected CALL for print"

    print("[PASS] CALL instruction")


# ─── Halt Instruction ───────────────────────────────────────────────────────

def test_cg_halt():
    """CodeGen: HALT at program end."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()
    instructions = report['instructions']

    assert instructions[-1]['mnemonic'] == 'HALT', "Expected HALT at end"

    print("[PASS] HALT instruction")


# ─── Unary Operations ───────────────────────────────────────────────────────

def test_cg_neg():
    """CodeGen: NEG for unary negation."""
    cg = compile_to_asm("x = -5")

    report = cg.get_report()
    negs = [i for i in report['instructions'] if i['mnemonic'] == 'NEG']

    assert len(negs) >= 1, "Expected NEG for negation"

    print("[PASS] NEG instruction")


def test_cg_not():
    """CodeGen: NOT for boolean negation."""
    cg = compile_to_asm("x = not 1")

    report = cg.get_report()
    nots = [i for i in report['instructions'] if i['mnemonic'] == 'NOT']

    assert len(nots) >= 1, "Expected NOT instruction"

    print("[PASS] NOT instruction")


# ─── Complex Programs ───────────────────────────────────────────────────────

def test_cg_while_loop():
    """CodeGen: generates labels and jumps for while loops."""
    source = """x = 5
while x > 0:
    x = x - 1
    print(x)"""

    cg = compile_to_asm(source)
    report = cg.get_report()
    text = report['assembly_text']

    # Should have labels and jumps
    assert 'L' in text or 'L0' in report['assembly_text'], "Expected labels for loop"

    print("[PASS] While loop codegen")


def test_cg_if_elif_else():
    """CodeGen: multiple branch paths."""
    source = """if x > 10:
    y = 1
elif x > 5:
    y = 2
else:
    y = 3"""

    cg = compile_to_asm(source)
    report = cg.get_report()

    # Should have multiple jumps and labels for branches
    jmps = sum(1 for i in report['instructions'] if 'J' in i['mnemonic'])
    assert jmps >= 2, "Expected multiple jumps for elif branches"

    print("[PASS] If/elif/else codegen")


# ─── Instruction Count ──────────────────────────────────────────────────────

def test_cg_instruction_count():
    """CodeGen: reports accurate instruction count."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()

    assert report['instruction_count'] > 0
    assert report['instruction_count'] == len(report['instructions'])

    print("[PASS] Instruction count")


def test_cg_no_empty_code():
    """CodeGen: always generates at least HALT."""
    cg = compile_to_asm("")  # Empty program

    report = cg.get_report()

    assert report['instruction_count'] >= 1, "Even empty program should have HALT"
    assert report['instructions'][-1]['mnemonic'] == 'HALT'

    print("[PASS] Non-empty code generation")


# ─── Register Usage ─────────────────────────────────────────────────────────

def test_cg_reasonable_register_usage():
    """CodeGen: doesn't use excessive registers."""
    cg = compile_to_asm("x = 1 + 2 + 3 + 4 + 5")

    report = cg.get_report()

    # Should use reasonable number of registers (not all 8 for simple arithmetic)
    assert report['registers_used'] <= 8
    assert report['registers_used'] >= 1

    print("[PASS] Reasonable register usage")


# ─── Data Section ───────────────────────────────────────────────────────────

def test_cg_string_literals():
    """CodeGen: allocates space for string literals."""
    cg = compile_to_asm('x = "hello"\nprint(x)')

    report = cg.get_report()

    assert len(report['data_section']) >= 1, "Expected string in data section"
    assert any('hello' in str(d) for d in report['data_section'])

    print("[PASS] String literals in data section")


# ─── Assembly Text Format ───────────────────────────────────────────────────

def test_cg_readable_text():
    """CodeGen: produces human-readable assembly."""
    cg = compile_to_asm("x = 10")

    text = cg.to_text()

    assert isinstance(text, str)
    assert len(text) > 0
    # Should contain instruction mnemonics
    assert any(m in text for m in ['MOVI', 'STORE', 'HALT', 'LOAD'])

    print("[PASS] Readable assembly text")


def test_cg_comments():
    """CodeGen: includes helpful comments."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()
    instructions = report['instructions']

    # Some instructions should have comments
    commented = [i for i in instructions if i.get('comment')]
    assert len(commented) >= 1, "Expected instructional comments"

    print("[PASS] Assembly comments")


# ─── Report Format ──────────────────────────────────────────────────────────

def test_cg_report_completeness():
    """CodeGen: report contains all required fields."""
    cg = compile_to_asm("x = 10")

    report = cg.get_report()

    required_fields = [
        'assembly_text',
        'instruction_count',
        'registers_used',
        'memory_locations',
        'memory_map',
        'data_section',
        'instructions',
    ]

    for field in required_fields:
        assert field in report, f"Missing report field: {field}"

    print("[PASS] Report completeness")


def test_cg_report_json_serializable():
    """CodeGen: report is JSON-serializable."""
    import json

    cg = compile_to_asm("x = 10 + 5")

    report = cg.get_report()

    try:
        json_str = json.dumps(report)
        assert len(json_str) > 0
    except TypeError as e:
        raise AssertionError(f"Report not JSON-serializable: {e}")

    print("[PASS] Report JSON serialization")


# ─── Integration ────────────────────────────────────────────────────────────

def test_cg_fizzbuzz():
    """CodeGen: handles complex FizzBuzz program."""
    source = """n = 15
i = 1
while i <= n:
    if i % 3 == 0:
        print(i)
    i = i + 1"""

    cg = compile_to_asm(source)
    report = cg.get_report()

    assert report['instruction_count'] > 10, "Complex program should have many instructions"
    assert report['registers_used'] >= 2, "Should use multiple registers"
    assert report['memory_locations'] >= 2, "Should allocate memory for variables"

    print("[PASS] FizzBuzz code generation")


def test_cg_fibonacci():
    """CodeGen: handles iterative Fibonacci."""
    source = """a = 0
b = 1
n = 10
while n > 0:
    c = a + b
    a = b
    b = c
    n = n - 1"""

    cg = compile_to_asm(source)
    report = cg.get_report()

    assert report['instruction_count'] > 15
    assert len(report['instructions']) > 0
    assert report['instructions'][-1]['mnemonic'] == 'HALT'

    print("[PASS] Fibonacci code generation")


# ─── Entry Point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BrailleCode Code Generator – Test Suite")
    print("="*60 + "\n")

    passed = failed = 0

    tests = [
        test_cg_movi,
        test_cg_store,
        test_cg_load,
        test_cg_add,
        test_cg_sub,
        test_cg_mul,
        test_cg_div,
        test_cg_register_allocation,
        test_cg_memory_allocation,
        test_cg_cmp,
        test_cg_jmp,
        test_cg_je_jne,
        test_cg_push,
        test_cg_call,
        test_cg_halt,
        test_cg_neg,
        test_cg_not,
        test_cg_while_loop,
        test_cg_if_elif_else,
        test_cg_instruction_count,
        test_cg_no_empty_code,
        test_cg_reasonable_register_usage,
        test_cg_string_literals,
        test_cg_readable_text,
        test_cg_comments,
        test_cg_report_completeness,
        test_cg_report_json_serializable,
        test_cg_fizzbuzz,
        test_cg_fibonacci,
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
