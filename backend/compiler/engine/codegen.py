"""
BrailleCode Compiler - Code Generator (Backend Phase)
======================================================

Translates the optimized TAC (intermediate code) into target assembly-like
code, managing register allocation and memory layout.

This is a simplified educational code generator that produces a readable
pseudo-assembly targeting a virtual stack machine with 8 registers (R0-R7).

Instruction set:
    LOAD  Rd, addr       - load value from memory into register
    STORE addr, Rs       - store register value to memory
    MOVI  Rd, imm        - load immediate value into register
    ADD   Rd, Rs1, Rs2   - Rd = Rs1 + Rs2
    SUB   Rd, Rs1, Rs2   - Rd = Rs1 - Rs2
    MUL   Rd, Rs1, Rs2   - Rd = Rs1 * Rs2
    DIV   Rd, Rs1, Rs2   - Rd = Rs1 / Rs2
    MOD   Rd, Rs1, Rs2   - Rd = Rs1 % Rs2
    CMP   Rs1, Rs2       - compare and set flags
    JMP   label          - unconditional jump
    JE    label          - jump if equal
    JNE   label          - jump if not equal
    JL    label          - jump if less
    JG    label          - jump if greater
    JLE   label          - jump if less or equal
    JGE   label          - jump if greater or equal
    PUSH  Rs             - push register onto stack (for call args)
    CALL  func           - call function
    NEG   Rd, Rs         - Rd = -Rs
    NOT   Rd, Rs         - Rd = !Rs
    AND   Rd, Rs1, Rs2   - Rd = Rs1 && Rs2
    OR    Rd, Rs1, Rs2   - Rd = Rs1 || Rs2
    HALT                 - stop execution

Register allocation:
    Uses a simple linear-scan allocator with 8 registers (R0-R7).
    Spills to memory when registers are exhausted.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from .ir_generator import TACInstruction


# ─── Assembly Instruction ────────────────────────────────────────────────────

@dataclass
class AsmInstruction:
    """A single assembly instruction."""
    mnemonic: str        # e.g. 'LOAD', 'ADD', 'STORE'
    operands: str        # e.g. 'R0, [x]' or 'R0, R1, R2'
    comment: str = ''    # optional annotation
    label: str = ''      # label attached to this instruction
    line: int = 0        # source line reference

    def __str__(self):
        parts = []
        if self.label:
            parts.append(f"{self.label}:")
        indent = "    " if not self.label else "        "
        s = f"{indent}{self.mnemonic:<6} {self.operands}"
        if self.comment:
            s = f"{s:<35} ; {self.comment}"
        if self.label:
            return f"{self.label}:\n{s}"
        return s


# ─── Code Generator ──────────────────────────────────────────────────────────

class CodeGenerator:
    """
    Translates optimized TAC into target pseudo-assembly.

    Usage:
        cg = CodeGenerator(optimized_tac)
        assembly = cg.generate()
    """

    NUM_REGISTERS = 8  # R0 through R7

    def __init__(self, tac_instructions: List[TACInstruction]):
        self.tac = tac_instructions
        self.asm: List[AsmInstruction] = []
        # Register allocation state
        self._reg_map: Dict[str, str] = {}   # variable/temp → register
        self._reg_used: List[bool] = [False] * self.NUM_REGISTERS
        self._memory: Dict[str, str] = {}    # variable → memory address label
        self._mem_offset = 0
        # Data section for string literals
        self._data: List[Dict] = []
        self._string_counter = 0

    def _alloc_reg(self, name: str = '') -> str:
        """Allocate a free register. Spills oldest if none free."""
        # Already allocated?
        if name and name in self._reg_map:
            return self._reg_map[name]

        # Find free register
        for i in range(self.NUM_REGISTERS):
            if not self._reg_used[i]:
                reg = f"R{i}"
                self._reg_used[i] = True
                if name:
                    self._reg_map[name] = reg
                return reg

        # No free register - spill R7 (simplistic strategy)
        spill_reg = "R7"
        # Find who owns R7 and spill them
        for var, reg in list(self._reg_map.items()):
            if reg == spill_reg:
                addr = self._get_mem(var)
                self.asm.append(AsmInstruction(
                    'STORE', f'[{addr}], {spill_reg}',
                    comment=f'spill {var}', line=0
                ))
                del self._reg_map[var]
                break
        if name:
            self._reg_map[name] = spill_reg
        return spill_reg

    def _free_reg(self, name: str):
        """Release the register holding `name`."""
        if name in self._reg_map:
            reg = self._reg_map[name]
            idx = int(reg[1:])
            self._reg_used[idx] = False
            del self._reg_map[name]

    def _get_mem(self, name: str) -> str:
        """Get memory address for a variable, allocating if needed."""
        if name not in self._memory:
            self._memory[name] = f"M[{self._mem_offset}]"
            self._mem_offset += 4
        return self._memory[name]

    def _load_operand(self, arg: str, hint: str = '') -> str:
        """Load an operand into a register and return the register name."""
        if not arg:
            return 'R0'

        # Already in a register?
        if arg in self._reg_map:
            return self._reg_map[arg]

        reg = self._alloc_reg(hint or arg)

        # Immediate integer
        try:
            int(arg)
            self.asm.append(AsmInstruction('MOVI', f'{reg}, {arg}', comment=f'load immediate {arg}'))
            return reg
        except ValueError:
            pass

        # Boolean / null
        if arg in ('true', 'false', 'null'):
            val = {'true': '1', 'false': '0', 'null': '0'}[arg]
            self.asm.append(AsmInstruction('MOVI', f'{reg}, {val}', comment=f'load {arg}'))
            return reg

        # String literal
        if arg.startswith('"'):
            str_label = f"STR{self._string_counter}"
            self._string_counter += 1
            self._data.append({'label': str_label, 'value': arg})
            self.asm.append(AsmInstruction('LOAD', f'{reg}, [{str_label}]', comment=f'load string {arg}'))
            return reg

        # Variable from memory
        addr = self._get_mem(arg)
        self.asm.append(AsmInstruction('LOAD', f'{reg}, [{addr}]', comment=f'load {arg}'))
        return reg

    def generate(self) -> List[AsmInstruction]:
        """Generate assembly from TAC instructions."""
        # Emit data section header if there are string literals in TAC
        for inst in self.tac:
            self._gen_instruction(inst)

        return self.asm

    def _gen_instruction(self, inst: TACInstruction):
        """Translate one TAC instruction to assembly."""

        # Labels
        if inst.op == 'LABEL':
            self.asm.append(AsmInstruction('', '', label=inst.label, line=inst.line))
            return

        # HALT
        if inst.op == 'HALT':
            self.asm.append(AsmInstruction('HALT', '', comment='program end', line=inst.line))
            return

        # Unconditional jump
        if inst.op == 'GOTO':
            self.asm.append(AsmInstruction('JMP', inst.result, line=inst.line))
            return

        # Conditional jump
        if inst.op == 'IF_FALSE':
            r1 = self._load_operand(inst.arg1)
            self.asm.append(AsmInstruction('CMP', f'{r1}, 0', comment=f'test {inst.arg1}', line=inst.line))
            self.asm.append(AsmInstruction('JE', inst.result, comment=f'jump if false', line=inst.line))
            return

        if inst.op == 'IF_TRUE':
            r1 = self._load_operand(inst.arg1)
            self.asm.append(AsmInstruction('CMP', f'{r1}, 0', comment=f'test {inst.arg1}', line=inst.line))
            self.asm.append(AsmInstruction('JNE', inst.result, comment=f'jump if true', line=inst.line))
            return

        # PARAM + CALL (print)
        if inst.op == 'PARAM':
            r1 = self._load_operand(inst.arg1)
            self.asm.append(AsmInstruction('PUSH', r1, comment=f'arg: {inst.arg1}', line=inst.line))
            return

        if inst.op == 'CALL':
            self.asm.append(AsmInstruction('CALL', inst.arg1, comment=f'call {inst.arg1}({inst.arg2} args)', line=inst.line))
            return

        # Copy assignment: result = arg1
        if inst.op == '=' and not inst.arg2:
            r1 = self._load_operand(inst.arg1, hint=inst.result)
            if r1 != self._reg_map.get(inst.result):
                rd = self._alloc_reg(inst.result)
                if rd != r1:
                    self.asm.append(AsmInstruction('MOV', f'{rd}, {r1}',
                                                  comment=f'{inst.result} = {inst.arg1}', line=inst.line))
            # Store to memory for named variables (not temporaries)
            if not inst.result.startswith('t'):
                rd = self._reg_map.get(inst.result, r1)
                addr = self._get_mem(inst.result)
                self.asm.append(AsmInstruction('STORE', f'[{addr}], {rd}',
                                              comment=f'store {inst.result}', line=inst.line))
            return

        # Binary arithmetic / comparison
        OP_MAP = {
            '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
            '==': 'CMP_EQ', '!=': 'CMP_NE', '<': 'CMP_LT', '>': 'CMP_GT',
            '<=': 'CMP_LE', '>=': 'CMP_GE',
            'and': 'AND', 'or': 'OR',
        }

        if inst.op in OP_MAP and inst.arg2:
            r1 = self._load_operand(inst.arg1)
            r2 = self._load_operand(inst.arg2)
            rd = self._alloc_reg(inst.result)
            mnemonic = OP_MAP[inst.op]

            if mnemonic.startswith('CMP_'):
                # Comparison: CMP then set result
                self.asm.append(AsmInstruction('CMP', f'{r1}, {r2}',
                                              comment=f'{inst.arg1} {inst.op} {inst.arg2}', line=inst.line))
                suffix = mnemonic[4:]  # EQ, NE, LT, etc.
                self.asm.append(AsmInstruction(f'SET{suffix}', rd,
                                              comment=f'{inst.result} = result', line=inst.line))
            else:
                self.asm.append(AsmInstruction(mnemonic, f'{rd}, {r1}, {r2}',
                                              comment=f'{inst.result} = {inst.arg1} {inst.op} {inst.arg2}',
                                              line=inst.line))

            # Store named variables
            if not inst.result.startswith('t'):
                addr = self._get_mem(inst.result)
                self.asm.append(AsmInstruction('STORE', f'[{addr}], {rd}',
                                              comment=f'store {inst.result}', line=inst.line))
            return

        # Unary operations
        if inst.op == '-' and not inst.arg2:
            r1 = self._load_operand(inst.arg1)
            rd = self._alloc_reg(inst.result)
            self.asm.append(AsmInstruction('NEG', f'{rd}, {r1}',
                                          comment=f'{inst.result} = -{inst.arg1}', line=inst.line))
            return

        if inst.op == 'not' and not inst.arg2:
            r1 = self._load_operand(inst.arg1)
            rd = self._alloc_reg(inst.result)
            self.asm.append(AsmInstruction('NOT', f'{rd}, {r1}',
                                          comment=f'{inst.result} = not {inst.arg1}', line=inst.line))
            return

    # ─── Serialization ────────────────────────────────────────────────────

    def to_text(self) -> str:
        """Return assembly as a formatted string."""
        lines = []
        if self._data:
            lines.append("; ── Data Section ──")
            for d in self._data:
                lines.append(f"    {d['label']}: .string {d['value']}")
            lines.append("")
        lines.append("; ── Code Section ──")
        for inst in self.asm:
            lines.append(str(inst))
        return '\n'.join(lines)

    def get_report(self) -> dict:
        """Return the code generation report for the API response."""
        return {
            'assembly_text': self.to_text(),
            'instruction_count': len(self.asm),
            'registers_used': sum(1 for u in self._reg_used if u),
            'memory_locations': len(self._memory),
            'data_section': self._data,
            'memory_map': {k: v for k, v in self._memory.items()},
            'instructions': [
                {
                    'index': i,
                    'mnemonic': inst.mnemonic,
                    'operands': inst.operands,
                    'comment': inst.comment,
                    'label': inst.label,
                    'line': inst.line,
                    'text': str(inst).strip(),
                }
                for i, inst in enumerate(self.asm)
            ],
        }
