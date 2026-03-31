"""
BrailleCode Compiler - Code Optimizer
======================================

Analyzes the intermediate code (TAC) and applies classical optimization
techniques to eliminate unnecessary, redundant, or slow instructions.

Optimizations performed:
  1. Constant Folding   - evaluate operations on constants at compile time
  2. Constant Propagation - replace variables with their known constant values
  3. Dead Code Elimination - remove assignments whose results are never used
  4. Strength Reduction   - replace expensive operations with cheaper ones
                            (e.g., x * 2 → x + x, x * 1 → x, x + 0 → x)

Each optimization pass produces a log entry describing what was changed
and why, so the frontend can show every decision the optimizer makes.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from copy import deepcopy

from .ir_generator import TACInstruction


# ─── Optimization Log ────────────────────────────────────────────────────────

@dataclass
class OptimizationEntry:
    """Record of a single optimization applied."""
    pass_name: str       # e.g. "Constant Folding"
    index: int           # instruction index that was optimized
    original: str        # original instruction text
    optimized: str       # new instruction text (or "REMOVED")
    description: str     # human-readable explanation


# ─── Optimizer ────────────────────────────────────────────────────────────────

class Optimizer:
    """
    Multi-pass optimizer for TAC instructions.

    Usage:
        opt = Optimizer(instructions)
        optimized = opt.optimize()
        log = opt.log
    """

    def __init__(self, instructions: List[TACInstruction]):
        self.original = instructions
        self.instructions = deepcopy(instructions)
        self.log: List[OptimizationEntry] = []
        self.stats = {
            'constant_folding': 0,
            'constant_propagation': 0,
            'dead_code_elimination': 0,
            'strength_reduction': 0,
        }

    def optimize(self) -> List[TACInstruction]:
        """Run all optimization passes in sequence."""
        self._constant_folding()
        self._constant_propagation()
        self._strength_reduction()
        self._dead_code_elimination()
        return self.instructions

    # ─── Pass 1: Constant Folding ─────────────────────────────────────────

    def _constant_folding(self):
        """Evaluate operations where both operands are known constants."""
        for i, inst in enumerate(self.instructions):
            if inst.op in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='):
                a, b = self._try_int(inst.arg1), self._try_int(inst.arg2)
                if a is not None and b is not None:
                    result = self._eval_op(inst.op, a, b)
                    if result is not None:
                        original = str(inst)
                        inst.arg1 = str(result)
                        inst.arg2 = ''
                        inst.op = '='
                        inst.comment = f'folded: {original.strip()}'
                        self.log.append(OptimizationEntry(
                            pass_name='Constant Folding', index=i,
                            original=original.strip(),
                            optimized=str(inst).strip(),
                            description=f"Both operands are constants - computed {result} at compile time",
                        ))
                        self.stats['constant_folding'] += 1

    # ─── Pass 2: Constant Propagation ────────────────────────────────────

    def _constant_propagation(self):
        """
        Track which temporaries hold constant values and substitute
        those constants into later uses.
        """
        constants: Dict[str, str] = {}

        for i, inst in enumerate(self.instructions):
            # If this is a simple copy of a constant value
            if inst.op == '=' and not inst.arg2 and inst.result:
                val = self._try_int(inst.arg1)
                if val is not None:
                    constants[inst.result] = inst.arg1
                elif inst.arg1.startswith('"'):
                    constants[inst.result] = inst.arg1
                elif inst.arg1 in ('true', 'false', 'null'):
                    constants[inst.result] = inst.arg1

            # Substitute constants into operands
            changed = False
            original = str(inst)

            if inst.arg1 in constants and inst.op not in ('LABEL', 'HALT'):
                inst.arg1 = constants[inst.arg1]
                changed = True

            if inst.arg2 in constants:
                inst.arg2 = constants[inst.arg2]
                changed = True

            if changed and str(inst) != original:
                self.log.append(OptimizationEntry(
                    pass_name='Constant Propagation', index=i,
                    original=original.strip(),
                    optimized=str(inst).strip(),
                    description=f"Replaced variable with its known constant value",
                ))
                self.stats['constant_propagation'] += 1

            # Invalidate if variable is reassigned
            if inst.op in ('+', '-', '*', '/', '%', '=', '==', '!=', '<', '>',
                           '<=', '>=', 'and', 'or', 'not'):
                if inst.result in constants and inst.op != '=':
                    del constants[inst.result]

    # ─── Pass 3: Strength Reduction ──────────────────────────────────────

    def _strength_reduction(self):
        """Replace expensive operations with cheaper equivalents."""
        for i, inst in enumerate(self.instructions):
            original = str(inst)

            # x * 2 → x + x
            if inst.op == '*':
                if self._try_int(inst.arg2) == 2:
                    inst.op = '+'
                    inst.arg2 = inst.arg1
                    self._log_strength(i, original, inst, "Replaced multiply by 2 with addition")
                elif self._try_int(inst.arg1) == 2:
                    inst.op = '+'
                    inst.arg1 = inst.arg2
                    self._log_strength(i, original, inst, "Replaced multiply by 2 with addition")
                # x * 1 → x
                elif self._try_int(inst.arg2) == 1:
                    inst.op = '='
                    inst.arg2 = ''
                    self._log_strength(i, original, inst, "Multiply by 1 is identity - removed")
                elif self._try_int(inst.arg1) == 1:
                    inst.op = '='
                    inst.arg1 = inst.arg2
                    inst.arg2 = ''
                    self._log_strength(i, original, inst, "Multiply by 1 is identity - removed")
                # x * 0 → 0
                elif self._try_int(inst.arg2) == 0 or self._try_int(inst.arg1) == 0:
                    inst.op = '='
                    inst.arg1 = '0'
                    inst.arg2 = ''
                    self._log_strength(i, original, inst, "Multiply by 0 is always 0")

            # x + 0 → x, x - 0 → x
            elif inst.op in ('+', '-') and self._try_int(inst.arg2) == 0:
                inst.op = '='
                inst.arg2 = ''
                self._log_strength(i, original, inst, f"{'Add' if inst.op == '+' else 'Subtract'} 0 is identity - removed")

            # 0 + x → x
            elif inst.op == '+' and self._try_int(inst.arg1) == 0:
                inst.op = '='
                inst.arg1 = inst.arg2
                inst.arg2 = ''
                self._log_strength(i, original, inst, "Add 0 is identity - removed")

            # x / 1 → x
            elif inst.op == '/' and self._try_int(inst.arg2) == 1:
                inst.op = '='
                inst.arg2 = ''
                self._log_strength(i, original, inst, "Divide by 1 is identity - removed")

    def _log_strength(self, i, original, inst, desc):
        self.log.append(OptimizationEntry(
            pass_name='Strength Reduction', index=i,
            original=original.strip(),
            optimized=str(inst).strip(),
            description=desc,
        ))
        self.stats['strength_reduction'] += 1

    # ─── Pass 4: Dead Code Elimination ───────────────────────────────────

    def _dead_code_elimination(self):
        """Remove assignments to temporaries that are never read later."""
        # Collect all used operands (variables/temps read by any instruction)
        used: Set[str] = set()
        for inst in self.instructions:
            if inst.op in ('LABEL', 'HALT'):
                continue
            if inst.arg1 and not self._is_literal(inst.arg1):
                used.add(inst.arg1)
            if inst.arg2 and not self._is_literal(inst.arg2):
                used.add(inst.arg2)

        # Mark dead assignments to temporaries
        removed_indices = []
        for i, inst in enumerate(self.instructions):
            if (inst.result and inst.result.startswith('t')
                    and inst.result not in used
                    and inst.op not in ('LABEL', 'GOTO', 'IF_TRUE', 'IF_FALSE',
                                        'PARAM', 'CALL', 'HALT')):
                removed_indices.append(i)
                self.log.append(OptimizationEntry(
                    pass_name='Dead Code Elimination', index=i,
                    original=str(inst).strip(),
                    optimized='REMOVED',
                    description=f"Temporary {inst.result} is never used - instruction removed",
                ))
                self.stats['dead_code_elimination'] += 1

        # Remove in reverse order to preserve indices
        for i in reversed(removed_indices):
            self.instructions.pop(i)

    # ─── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _try_int(val: str) -> Optional[int]:
        """Try to parse a value as an integer. Returns None on failure."""
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _is_literal(val: str) -> bool:
        """Check if a value is a literal (number, string, boolean, null)."""
        if not val:
            return True
        if val in ('true', 'false', 'null'):
            return True
        if val.startswith('"'):
            return True
        try:
            int(val)
            return True
        except ValueError:
            return False

    @staticmethod
    def _eval_op(op: str, a: int, b: int) -> Optional[int]:
        """Evaluate a binary operation on two integer constants."""
        try:
            if op == '+':
                return a + b
            if op == '-':
                return a - b
            if op == '*':
                return a * b
            if op == '/' and b != 0:
                return a // b
            if op == '%' and b != 0:
                return a % b
            if op == '==':
                return 1 if a == b else 0
            if op == '!=':
                return 1 if a != b else 0
            if op == '<':
                return 1 if a < b else 0
            if op == '>':
                return 1 if a > b else 0
            if op == '<=':
                return 1 if a <= b else 0
            if op == '>=':
                return 1 if a >= b else 0
        except Exception:
            return None
        return None

    # ─── Serialization ────────────────────────────────────────────────────

    def get_report(self) -> dict:
        """Return the optimization report for the API response."""
        return {
            'original_count': len(self.original),
            'optimized_count': len(self.instructions),
            'eliminated': len(self.original) - len(self.instructions),
            'stats': self.stats,
            'log': [
                {
                    'pass': e.pass_name,
                    'index': e.index,
                    'original': e.original,
                    'optimized': e.optimized,
                    'description': e.description,
                }
                for e in self.log
            ],
            'instructions': [
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
            ],
        }
