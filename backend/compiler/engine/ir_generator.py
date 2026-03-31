"""
BrailleCode Compiler - Intermediate Code Generator
====================================================

Translates the validated AST into Three-Address Code (TAC), a
machine-independent intermediate representation that acts as a
bridge between the high-level source and the final target code.

Each TAC instruction is a simple operation with at most three
operands (hence "three-address").  Temporaries (t0, t1, ...) hold
intermediate results.  Labels (L0, L1, ...) mark branch targets.

Instruction forms:
    t0 = a + b          (binary operation)
    t0 = -a             (unary operation)
    t0 = a              (copy / assignment)
    PARAM t0             (push argument for call)
    CALL print, 1        (function call with arg count)
    IF t0 GOTO L1        (conditional jump)
    GOTO L2              (unconditional jump)
    LABEL L1             (label definition)
"""

from typing import List, Optional
from dataclasses import dataclass, field

from .ast_nodes import (
    ASTNode, Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
)


# ─── TAC Instruction ─────────────────────────────────────────────────────────

@dataclass
class TACInstruction:
    """A single three-address code instruction."""
    op: str            # operation: '=', '+', '-', '*', '/', '%', '<', '>', etc.
    result: str        # destination variable or ''
    arg1: str = ''     # first operand
    arg2: str = ''     # second operand (empty for unary/copy)
    line: int = 0      # source line number
    label: str = ''    # label if this is a LABEL instruction
    comment: str = ''  # optional comment for readability

    def __str__(self):
        if self.op == 'HALT':
            return "    HALT"
        if self.op == 'LABEL':
            return f"{self.label}:"
        if self.op == 'GOTO':
            return f"    GOTO {self.result}"
        if self.op == 'IF_TRUE':
            return f"    IF {self.arg1} GOTO {self.result}"
        if self.op == 'IF_FALSE':
            return f"    IF_FALSE {self.arg1} GOTO {self.result}"
        if self.op == 'PARAM':
            return f"    PARAM {self.arg1}"
        if self.op == 'CALL':
            return f"    CALL {self.arg1}, {self.arg2}"
        if self.op == '=':
            return f"    {self.result} = {self.arg1}"
        if self.arg2:
            return f"    {self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op in ('-', 'not'):
            return f"    {self.result} = {self.op} {self.arg1}"
        return f"    {self.result} = {self.arg1}"


# ─── IR Generator ────────────────────────────────────────────────────────────

class IRGenerator:
    """
    Walks the AST and produces a list of TACInstruction objects.

    Usage:
        gen = IRGenerator()
        instructions = gen.generate(ast)
    """

    def __init__(self):
        self._temp_counter = 0
        self._label_counter = 0
        self.instructions: List[TACInstruction] = []

    def _new_temp(self) -> str:
        """Generate a fresh temporary variable name."""
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        """Generate a fresh label name."""
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, op: str, result: str = '', arg1: str = '', arg2: str = '',
              line: int = 0, label: str = '', comment: str = ''):
        """Append an instruction to the instruction list."""
        self.instructions.append(TACInstruction(
            op=op, result=result, arg1=arg1, arg2=arg2,
            line=line, label=label, comment=comment,
        ))

    def generate(self, program: Program) -> List[TACInstruction]:
        """Generate TAC for the full program."""
        for stmt in program.body:
            self._gen_statement(stmt)
        self._emit('HALT', line=0, comment='End of program')
        return self.instructions

    # ─── Statements ───────────────────────────────────────────────────────

    def _gen_statement(self, node: ASTNode):
        if isinstance(node, Assign):
            self._gen_assign(node)
        elif isinstance(node, Print):
            self._gen_print(node)
        elif isinstance(node, If):
            self._gen_if(node)
        elif isinstance(node, While):
            self._gen_while(node)

    def _gen_assign(self, node: Assign):
        val = self._gen_expression(node.value)
        self._emit('=', result=node.name, arg1=val,
                   line=node.line, comment=f'{node.name} = {val}')

    def _gen_print(self, node: Print):
        val = self._gen_expression(node.value)
        self._emit('PARAM', arg1=val, line=node.line)
        self._emit('CALL', arg1='print', arg2='1',
                   line=node.line, comment=f'print({val})')

    def _gen_if(self, node: If):
        # Evaluate condition
        cond = self._gen_expression(node.condition)

        # Labels
        labels_elif = []
        for _ in node.elif_clauses:
            labels_elif.append(self._new_label())
        label_else = self._new_label()
        label_end = self._new_label()

        first_false_target = labels_elif[0] if labels_elif else (label_else if node.else_body else label_end)

        # if condition is false, jump to first elif / else / end
        self._emit('IF_FALSE', result=first_false_target, arg1=cond,
                   line=node.condition.line, comment='if-test')

        # if body
        for stmt in node.body:
            self._gen_statement(stmt)
        self._emit('GOTO', result=label_end, line=node.line)

        # elif clauses
        for i, (elif_cond, elif_body) in enumerate(node.elif_clauses):
            self._emit('LABEL', label=labels_elif[i], line=elif_cond.line)
            cond_res = self._gen_expression(elif_cond)
            next_target = labels_elif[i+1] if i+1 < len(labels_elif) else (label_else if node.else_body else label_end)
            self._emit('IF_FALSE', result=next_target, arg1=cond_res,
                       line=elif_cond.line, comment='elif-test')
            for stmt in elif_body:
                self._gen_statement(stmt)
            self._emit('GOTO', result=label_end, line=elif_cond.line)

        # else body
        if node.else_body:
            self._emit('LABEL', label=label_else, line=node.line)
            for stmt in node.else_body:
                self._gen_statement(stmt)

        self._emit('LABEL', label=label_end, line=node.line)

    def _gen_while(self, node: While):
        label_start = self._new_label()
        label_end = self._new_label()

        self._emit('LABEL', label=label_start, line=node.line, comment='while-start')
        cond = self._gen_expression(node.condition)
        self._emit('IF_FALSE', result=label_end, arg1=cond,
                   line=node.condition.line, comment='while-test')

        for stmt in node.body:
            self._gen_statement(stmt)

        self._emit('GOTO', result=label_start, line=node.line)
        self._emit('LABEL', label=label_end, line=node.line, comment='while-end')

    # ─── Expressions ──────────────────────────────────────────────────────

    def _gen_expression(self, node: ASTNode) -> str:
        """Generate TAC for an expression. Returns the result temp/variable name."""
        if isinstance(node, Number):
            return str(node.value)

        if isinstance(node, String):
            return f'"{node.value}"'

        if isinstance(node, Boolean):
            return 'true' if node.value else 'false'

        if isinstance(node, NoneValue):
            return 'null'

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, BinOp):
            left = self._gen_expression(node.left)
            right = self._gen_expression(node.right)
            temp = self._new_temp()
            self._emit(node.op, result=temp, arg1=left, arg2=right, line=node.line)
            return temp

        if isinstance(node, UnaryOp):
            operand = self._gen_expression(node.operand)
            temp = self._new_temp()
            self._emit(node.op, result=temp, arg1=operand, line=node.line)
            return temp

        if isinstance(node, Compare):
            left = self._gen_expression(node.left)
            right = self._gen_expression(node.right)
            temp = self._new_temp()
            self._emit(node.op, result=temp, arg1=left, arg2=right, line=node.line)
            return temp

        if isinstance(node, BoolOp):
            left = self._gen_expression(node.left)
            right = self._gen_expression(node.right)
            temp = self._new_temp()
            self._emit(node.op, result=temp, arg1=left, arg2=right, line=node.line)
            return temp

        return '?'

    # ─── Serialization ────────────────────────────────────────────────────

    def to_text(self) -> str:
        """Return TAC as a human-readable string."""
        return '\n'.join(str(inst) for inst in self.instructions)

    def to_list(self) -> list:
        """Return TAC as a list of dicts for JSON serialization."""
        return [
            {
                'index': i,
                'op': inst.op,
                'result': inst.result,
                'arg1': inst.arg1,
                'arg2': inst.arg2,
                'line': inst.line,
                'label': inst.label,
                'comment': inst.comment,
                'text': str(inst),
            }
            for i, inst in enumerate(self.instructions)
        ]
