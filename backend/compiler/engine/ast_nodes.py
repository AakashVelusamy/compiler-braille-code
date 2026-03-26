"""
BrailleCode Compiler - AST Node Definitions
=============================================

Defines all Abstract Syntax Tree node types.
The parser builds a tree of these nodes from the token stream.
The semantic analyzer and interpreter then walk this tree.

Node hierarchy:
  Program         — root node, contains a list of statements
  ├── Assign      — variable assignment:  x = expr
  ├── Print       — print statement:      print(expr)
  ├── If          — if / elif / else:     if cond: block [elif cond: block] [else: block]
  ├── While       — while loop:           while cond: block
  ├── BinOp       — binary operation:     expr op expr
  ├── UnaryOp     — unary operation:      not expr, -expr
  ├── Compare     — comparison:           expr cmp_op expr
  ├── BoolOp      — boolean logic:        expr and/or expr
  ├── Number      — integer literal:      42
  ├── String      — string literal:       "hello"
  ├── Boolean     — True / False
  ├── NoneValue   — None
  └── Identifier  — variable reference:   x
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ─── Base class ───────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    """Base class for all AST nodes. Carries a line number for error reporting."""
    line: int = 0


# ─── Program (root) ──────────────────────────────────────────────────────────

@dataclass
class Program(ASTNode):
    """Root node: a program is a sequence of statements."""
    body: List[ASTNode] = field(default_factory=list)


# ─── Statements ───────────────────────────────────────────────────────────────

@dataclass
class Assign(ASTNode):
    """Variable assignment: name = value"""
    name: str = ''
    value: ASTNode = None


@dataclass
class Print(ASTNode):
    """Print statement: print(expression)"""
    value: ASTNode = None


@dataclass
class If(ASTNode):
    """
    If / elif / else statement.

    condition:  the test expression
    body:       list of statements in the if-block
    elif_clauses: list of (condition, body) tuples for elif branches
    else_body:  list of statements in the else-block (or None)
    """
    condition: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)
    elif_clauses: List[tuple] = field(default_factory=list)  # [(condition, [stmts]), ...]
    else_body: Optional[List[ASTNode]] = None


@dataclass
class While(ASTNode):
    """While loop: while condition: body"""
    condition: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)


# ─── Expressions ──────────────────────────────────────────────────────────────

@dataclass
class BinOp(ASTNode):
    """Binary operation: left op right (arithmetic: +, -, *, /, %)"""
    left: ASTNode = None
    op: str = ''
    right: ASTNode = None


@dataclass
class UnaryOp(ASTNode):
    """Unary operation: op operand (e.g. not x, -x)"""
    op: str = ''
    operand: ASTNode = None


@dataclass
class Compare(ASTNode):
    """Comparison: left op right (==, !=, <, >, <=, >=)"""
    left: ASTNode = None
    op: str = ''
    right: ASTNode = None


@dataclass
class BoolOp(ASTNode):
    """Boolean operation: left op right (and, or)"""
    left: ASTNode = None
    op: str = ''       # 'and' or 'or'
    right: ASTNode = None


# ─── Literals ─────────────────────────────────────────────────────────────────

@dataclass
class Number(ASTNode):
    """Integer literal."""
    value: int = 0


@dataclass
class String(ASTNode):
    """String literal."""
    value: str = ''


@dataclass
class Boolean(ASTNode):
    """Boolean literal: True or False."""
    value: bool = False


@dataclass
class NoneValue(ASTNode):
    """None literal."""
    pass


# ─── Identifier ───────────────────────────────────────────────────────────────

@dataclass
class Identifier(ASTNode):
    """Variable reference by name."""
    name: str = ''


# ─── AST pretty printer (for debugging & visualization) ──────────────────────

def ast_to_dict(node: ASTNode) -> dict:
    """
    Convert an AST tree to a nested dictionary for JSON serialization.
    Useful for the /api/ast endpoint and debugging.
    """
    if isinstance(node, Program):
        return {
            'type': 'Program',
            'body': [ast_to_dict(stmt) for stmt in node.body],
        }
    elif isinstance(node, Assign):
        return {
            'type': 'Assign',
            'name': node.name,
            'value': ast_to_dict(node.value),
            'line': node.line,
        }
    elif isinstance(node, Print):
        return {
            'type': 'Print',
            'value': ast_to_dict(node.value),
            'line': node.line,
        }
    elif isinstance(node, If):
        result = {
            'type': 'If',
            'condition': ast_to_dict(node.condition),
            'body': [ast_to_dict(s) for s in node.body],
            'line': node.line,
        }
        if node.elif_clauses:
            result['elif_clauses'] = [
                {
                    'condition': ast_to_dict(cond),
                    'body': [ast_to_dict(s) for s in body],
                }
                for cond, body in node.elif_clauses
            ]
        if node.else_body is not None:
            result['else_body'] = [ast_to_dict(s) for s in node.else_body]
        return result
    elif isinstance(node, While):
        return {
            'type': 'While',
            'condition': ast_to_dict(node.condition),
            'body': [ast_to_dict(s) for s in node.body],
            'line': node.line,
        }
    elif isinstance(node, BinOp):
        return {
            'type': 'BinOp',
            'left': ast_to_dict(node.left),
            'op': node.op,
            'right': ast_to_dict(node.right),
            'line': node.line,
        }
    elif isinstance(node, UnaryOp):
        return {
            'type': 'UnaryOp',
            'op': node.op,
            'operand': ast_to_dict(node.operand),
            'line': node.line,
        }
    elif isinstance(node, Compare):
        return {
            'type': 'Compare',
            'left': ast_to_dict(node.left),
            'op': node.op,
            'right': ast_to_dict(node.right),
            'line': node.line,
        }
    elif isinstance(node, BoolOp):
        return {
            'type': 'BoolOp',
            'left': ast_to_dict(node.left),
            'op': node.op,
            'right': ast_to_dict(node.right),
            'line': node.line,
        }
    elif isinstance(node, Number):
        return {'type': 'Number', 'value': node.value, 'line': node.line}
    elif isinstance(node, String):
        return {'type': 'String', 'value': node.value, 'line': node.line}
    elif isinstance(node, Boolean):
        return {'type': 'Boolean', 'value': node.value, 'line': node.line}
    elif isinstance(node, NoneValue):
        return {'type': 'NoneValue', 'line': node.line}
    elif isinstance(node, Identifier):
        return {'type': 'Identifier', 'name': node.name, 'line': node.line}
    else:
        return {'type': 'Unknown', 'repr': repr(node)}


def print_ast(node: ASTNode, indent: int = 0):
    """Pretty-print an AST tree to stdout for debugging."""
    prefix = '  ' * indent

    if isinstance(node, Program):
        print(f"{prefix}Program")
        for stmt in node.body:
            print_ast(stmt, indent + 1)

    elif isinstance(node, Assign):
        print(f"{prefix}Assign [{node.name}] =")
        print_ast(node.value, indent + 1)

    elif isinstance(node, Print):
        print(f"{prefix}Print")
        print_ast(node.value, indent + 1)

    elif isinstance(node, If):
        print(f"{prefix}If")
        print(f"{prefix}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  body:")
        for s in node.body:
            print_ast(s, indent + 2)
        for cond, body in node.elif_clauses:
            print(f"{prefix}  elif:")
            print(f"{prefix}    condition:")
            print_ast(cond, indent + 3)
            print(f"{prefix}    body:")
            for s in body:
                print_ast(s, indent + 3)
        if node.else_body is not None:
            print(f"{prefix}  else:")
            for s in node.else_body:
                print_ast(s, indent + 2)

    elif isinstance(node, While):
        print(f"{prefix}While")
        print(f"{prefix}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  body:")
        for s in node.body:
            print_ast(s, indent + 2)

    elif isinstance(node, BinOp):
        print(f"{prefix}BinOp [{node.op}]")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{prefix}UnaryOp [{node.op}]")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, Compare):
        print(f"{prefix}Compare [{node.op}]")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, BoolOp):
        print(f"{prefix}BoolOp [{node.op}]")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, Number):
        print(f"{prefix}Number({node.value})")

    elif isinstance(node, String):
        print(f"{prefix}String({node.value!r})")

    elif isinstance(node, Boolean):
        print(f"{prefix}Boolean({node.value})")

    elif isinstance(node, NoneValue):
        print(f"{prefix}None")

    elif isinstance(node, Identifier):
        print(f"{prefix}Identifier({node.name})")

    else:
        print(f"{prefix}??? {repr(node)}")
