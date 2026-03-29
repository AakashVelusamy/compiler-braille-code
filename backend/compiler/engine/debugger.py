"""
BrailleCode Compiler - Step-by-Step Debugger
==============================================

Executes the program one statement at a time, recording a snapshot
of the full program state after each step:

  - Which line is executing
  - What statement type it is
  - All variable values at that point
  - Any output produced by that step
  - Which branch was taken (for if/elif/else)
  - Loop iteration count (for while)

The debugger returns a list of steps that the frontend can walk
through forwards and backwards.
"""

from typing import Any, Dict, List
from dataclasses import dataclass, field
import copy

from .ast_nodes import (
    ASTNode, Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
)
from .interpreter import Environment, RuntimeError_, MaxIterationsError


@dataclass
class DebugStep:
    """A single snapshot of program state after executing one statement."""
    step_number: int
    line: int
    statement_type: str     # 'Assign', 'Print', 'If', 'While', etc.
    description: str        # human-readable: "x = 10", "print(x) → 10"
    variables: Dict[str, Any] = field(default_factory=dict)
    output_line: str = ''   # what this step printed (if anything)
    total_output: List[str] = field(default_factory=list)
    branch_taken: str = ''  # 'if', 'elif', 'else', '' for non-branching
    loop_iteration: int = 0 # current iteration for while loops
    event: str = ''         # 'assign', 'print', 'branch', 'loop_start', 'loop_end', 'error'
    error: str = ''

    def to_dict(self) -> dict:
        return {
            'step_number': self.step_number,
            'line': self.line,
            'statement_type': self.statement_type,
            'description': self.description,
            'variables': self.variables,
            'output_line': self.output_line,
            'total_output': list(self.total_output),
            'branch_taken': self.branch_taken,
            'loop_iteration': self.loop_iteration,
            'event': self.event,
            'error': self.error,
        }


class Debugger:
    """
    Executes a program and records every step for playback.

    Usage:
        debugger = Debugger()
        result = debugger.run(ast)
        # result['steps'] is a list of DebugStep dicts
    """

    MAX_STEPS = 500        # safety limit
    MAX_ITERATIONS = 10000

    def __init__(self):
        self.env = Environment()
        self.steps: List[DebugStep] = []
        self.output: List[str] = []
        self.step_count = 0
        self.errors: List[dict] = []

    def run(self, program: Program) -> dict:
        """Execute the full program, recording each step."""
        try:
            for stmt in program.body:
                self._exec_statement(stmt)
        except RuntimeError_ as e:
            self._record_step(
                line=e.line,
                statement_type='Error',
                description=str(e),
                event='error',
                error=str(e),
            )
        except Exception as e:
            self._record_step(
                line=0,
                statement_type='Error',
                description=f'Internal error: {e}',
                event='error',
                error=str(e),
            )

        return {
            'steps': [s.to_dict() for s in self.steps],
            'total_steps': len(self.steps),
            'final_output': list(self.output),
            'final_variables': self.env.get_all(),
            'success': len(self.errors) == 0,
        }

    def _record_step(self, line, statement_type, description,
                     event='', output_line='', branch_taken='',
                     loop_iteration=0, error=''):
        """Snapshot the current state and record a step."""
        self.step_count += 1

        if self.step_count > self.MAX_STEPS:
            raise RuntimeError_("Program exceeded maximum debug steps (500)", line)

        step = DebugStep(
            step_number=self.step_count,
            line=line,
            statement_type=statement_type,
            description=description,
            variables=self._serialize_vars(),
            output_line=output_line,
            total_output=list(self.output),
            branch_taken=branch_taken,
            loop_iteration=loop_iteration,
            event=event or statement_type.lower(),
            error=error,
        )
        self.steps.append(step)

        if error:
            self.errors.append({'message': error, 'line': line})

    def _serialize_vars(self) -> dict:
        """Get a serializable snapshot of all current variables."""
        raw = self.env.get_all()
        result = {}
        for k, v in raw.items():
            if v is None:
                result[k] = {'value': None, 'type': 'none', 'display': 'None'}
            elif isinstance(v, bool):
                result[k] = {'value': v, 'type': 'bool', 'display': str(v)}
            elif isinstance(v, int):
                result[k] = {'value': v, 'type': 'int', 'display': str(v)}
            elif isinstance(v, str):
                result[k] = {'value': v, 'type': 'str', 'display': f'"{v}"'}
            else:
                result[k] = {'value': str(v), 'type': type(v).__name__, 'display': str(v)}
        return result

    # ─── Statement execution (mirrors interpreter but records steps) ──────

    def _exec_statement(self, node: ASTNode):
        if isinstance(node, Assign):
            self._exec_assign(node)
        elif isinstance(node, Print):
            self._exec_print(node)
        elif isinstance(node, If):
            self._exec_if(node)
        elif isinstance(node, While):
            self._exec_while(node)
        else:
            raise RuntimeError_(f"Unknown statement: {type(node).__name__}", node.line)

    def _exec_assign(self, node: Assign):
        value = self._eval(node.value)
        self.env.set(node.name, value)
        display = self._display_value(value)
        self._record_step(
            line=node.line,
            statement_type='Assign',
            description=f'{node.name} = {display}',
            event='assign',
        )

    def _exec_print(self, node: Print):
        value = self._eval(node.value)
        display = self._display_value(value)
        self.output.append(display)
        self._record_step(
            line=node.line,
            statement_type='Print',
            description=f'print({display})',
            event='print',
            output_line=display,
        )

    def _exec_if(self, node: If):
        cond_val = self._eval(node.condition)
        cond_display = self._display_value(cond_val)

        if self._is_truthy(cond_val):
            self._record_step(
                line=node.line,
                statement_type='If',
                description=f'if {cond_display} → True',
                event='branch',
                branch_taken='if',
            )
            self.env.push_scope()
            for stmt in node.body:
                self._exec_statement(stmt)
            self.env.pop_scope()
            return

        # Check elif clauses
        for i, (elif_cond, elif_body) in enumerate(node.elif_clauses):
            elif_val = self._eval(elif_cond)
            elif_display = self._display_value(elif_val)

            if self._is_truthy(elif_val):
                self._record_step(
                    line=elif_cond.line,
                    statement_type='Elif',
                    description=f'elif {elif_display} → True',
                    event='branch',
                    branch_taken='elif',
                )
                self.env.push_scope()
                for stmt in elif_body:
                    self._exec_statement(stmt)
                self.env.pop_scope()
                return
            else:
                self._record_step(
                    line=elif_cond.line,
                    statement_type='Elif',
                    description=f'elif {elif_display} → False (skipped)',
                    event='branch',
                    branch_taken='',
                )

        # Else
        if node.else_body is not None:
            self._record_step(
                line=node.line,
                statement_type='Else',
                description='else → entered',
                event='branch',
                branch_taken='else',
            )
            self.env.push_scope()
            for stmt in node.else_body:
                self._exec_statement(stmt)
            self.env.pop_scope()
        else:
            self._record_step(
                line=node.line,
                statement_type='If',
                description=f'if {cond_display} → False (no else)',
                event='branch',
                branch_taken='',
            )

    def _exec_while(self, node: While):
        iteration = 0

        while True:
            cond_val = self._eval(node.condition)
            cond_display = self._display_value(cond_val)

            if not self._is_truthy(cond_val):
                self._record_step(
                    line=node.line,
                    statement_type='While',
                    description=f'while {cond_display} → False (exit loop)',
                    event='loop_end',
                    loop_iteration=iteration,
                )
                break

            iteration += 1
            if iteration > self.MAX_ITERATIONS:
                raise MaxIterationsError(
                    f"While loop exceeded {self.MAX_ITERATIONS} iterations", node.line
                )

            self._record_step(
                line=node.line,
                statement_type='While',
                description=f'while {cond_display} → True (iteration {iteration})',
                event='loop_start',
                loop_iteration=iteration,
            )

            self.env.push_scope()
            for stmt in node.body:
                self._exec_statement(stmt)
            self.env.pop_scope()

    # ─── Expression evaluation (same as interpreter) ──────────────────────

    def _eval(self, node: ASTNode) -> Any:
        if isinstance(node, Number):
            return node.value
        if isinstance(node, String):
            return node.value
        if isinstance(node, Boolean):
            return node.value
        if isinstance(node, NoneValue):
            return None
        if isinstance(node, Identifier):
            try:
                return self.env.get(node.name)
            except KeyError:
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line)
        if isinstance(node, BinOp):
            return self._eval_binop(node)
        if isinstance(node, UnaryOp):
            return self._eval_unaryop(node)
        if isinstance(node, Compare):
            return self._eval_compare(node)
        if isinstance(node, BoolOp):
            return self._eval_boolop(node)
        raise RuntimeError_(f"Unknown expression: {type(node).__name__}", node.line)

    def _eval_binop(self, node: BinOp) -> Any:
        left = self._eval(node.left)
        right = self._eval(node.right)
        try:
            if node.op == '+':
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                raise RuntimeError_(f"Cannot add {type(left).__name__} and {type(right).__name__}", node.line)
            if node.op == '-': return left - right
            if node.op == '*': return left * right
            if node.op == '/':
                if right == 0: raise RuntimeError_("Division by zero", node.line)
                return left // right
            if node.op == '%':
                if right == 0: raise RuntimeError_("Modulo by zero", node.line)
                return left % right
        except TypeError as e:
            raise RuntimeError_(f"Type error in '{node.op}': {e}", node.line)
        raise RuntimeError_(f"Unknown operator '{node.op}'", node.line)

    def _eval_unaryop(self, node: UnaryOp) -> Any:
        operand = self._eval(node.operand)
        if node.op == '-':
            if not isinstance(operand, (int, float)):
                raise RuntimeError_(f"Cannot negate {type(operand).__name__}", node.line)
            return -operand
        if node.op == 'not':
            return not self._is_truthy(operand)
        raise RuntimeError_(f"Unknown unary operator '{node.op}'", node.line)

    def _eval_compare(self, node: Compare) -> bool:
        left = self._eval(node.left)
        right = self._eval(node.right)
        try:
            if node.op == '==': return left == right
            if node.op == '!=': return left != right
            if node.op == '<':  return left < right
            if node.op == '>':  return left > right
            if node.op == '<=': return left <= right
            if node.op == '>=': return left >= right
        except TypeError as e:
            raise RuntimeError_(f"Cannot compare with '{node.op}': {e}", node.line)
        raise RuntimeError_(f"Unknown comparison '{node.op}'", node.line)

    def _eval_boolop(self, node: BoolOp) -> Any:
        left = self._eval(node.left)
        if node.op == 'and':
            return self._eval(node.right) if self._is_truthy(left) else left
        if node.op == 'or':
            return left if self._is_truthy(left) else self._eval(node.right)
        raise RuntimeError_(f"Unknown boolean operator '{node.op}'", node.line)

    def _is_truthy(self, value: Any) -> bool:
        if value is None: return False
        if isinstance(value, bool): return value
        if isinstance(value, int): return value != 0
        if isinstance(value, str): return len(value) > 0
        return True

    def _display_value(self, value: Any) -> str:
        if value is None: return 'None'
        if isinstance(value, bool): return 'True' if value else 'False'
        if isinstance(value, str): return f'"{value}"' if '"' not in value else f"'{value}'"
        return str(value)
