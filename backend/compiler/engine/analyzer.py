"""
BrailleCode Compiler - Semantic Analyzer
==========================================

Walks the AST and performs static checks before execution:

  1. Symbol table management
     - Tracks all declared variables and their scope depth
     - Pushes a new scope on INDENT (if/while body), pops on exit
     - Variables declared in inner scopes are accessible in deeper scopes
       but not in outer scopes after the block ends

  2. Variable usage checks
     - Ensures variables are assigned before they are read
     - Reports the exact line number of the offending usage

  3. Type warnings (soft)
     - Flags operations that mix incompatible types at declaration
       (e.g. assigning a string then using it in arithmetic)
     - These are warnings, not hard errors, since our language is dynamic

The analyzer does NOT execute the program - it only validates structure.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .ast_nodes import (
    ASTNode, Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
)


# ─── Errors & Warnings ───────────────────────────────────────────────────────

class SemanticError(Exception):
    """Hard error - program cannot proceed."""

    def __init__(self, message: str, line: int):
        self.line = line
        super().__init__(f"Line {line}: {message}")


@dataclass
class SemanticWarning:
    """Soft warning - program can still run but something looks suspicious."""
    message: str
    line: int

    def __repr__(self):
        return f"Warning (line {self.line}): {self.message}"


# ─── Symbol Table ─────────────────────────────────────────────────────────────

@dataclass
class Symbol:
    """Information about a declared variable."""
    name: str
    declared_line: int
    scope_depth: int
    inferred_type: Optional[str] = None  # 'int', 'str', 'bool', 'none', 'unknown'


class SymbolTable:
    """
    Scoped symbol table implemented as a stack of dictionaries.

    Each scope is a dict mapping variable name → Symbol.
    Lookup searches from the innermost scope outward.
    """

    def __init__(self):
        # Start with a single global scope
        self._scopes: List[Dict[str, Symbol]] = [{}]

    @property
    def depth(self) -> int:
        """Current scope depth (0 = global)."""
        return len(self._scopes) - 1

    def push_scope(self):
        """Enter a new nested scope (e.g. inside an if/while block)."""
        self._scopes.append({})

    def pop_scope(self):
        """Exit the current scope, discarding its local symbols."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    def declare(self, name: str, line: int, inferred_type: str = 'unknown'):
        """
        Declare (or re-declare) a variable in the current scope.
        If it already exists in the current scope, update it.
        """
        self._scopes[-1][name] = Symbol(
            name=name,
            declared_line=line,
            scope_depth=self.depth,
            inferred_type=inferred_type,
        )

    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a variable by name, searching from innermost to outermost scope.
        Returns the Symbol if found, None otherwise.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def is_declared(self, name: str) -> bool:
        """Check if a variable is declared in any accessible scope."""
        return self.lookup(name) is not None

    def get_all_symbols(self) -> List[Symbol]:
        """Return all symbols across all scopes (for debugging)."""
        all_syms = []
        for scope in self._scopes:
            all_syms.extend(scope.values())
        return all_syms


# ─── Analyzer ─────────────────────────────────────────────────────────────────

class SemanticAnalyzer:
    """
    Walks the AST and performs semantic checks.

    Usage:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        # Check analyzer.errors and analyzer.warnings
    """

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticWarning] = []

    def analyze(self, program: Program) -> bool:
        """
        Analyze the full program AST.

        Returns:
            True if no errors were found, False otherwise.
            Warnings don't count as failures.
        """
        for stmt in program.body:
            self._analyze_statement(stmt)

        return len(self.errors) == 0

    # ─── Statement analysis ───────────────────────────────────────────────

    def _analyze_statement(self, node: ASTNode):
        """Dispatch to the appropriate statement analyzer."""

        if isinstance(node, Assign):
            self._analyze_assign(node)
        elif isinstance(node, Print):
            self._analyze_print(node)
        elif isinstance(node, If):
            self._analyze_if(node)
        elif isinstance(node, While):
            self._analyze_while(node)
        else:
            self._add_error(f"Unknown statement type: {type(node).__name__}", node.line)

    def _analyze_assign(self, node: Assign):
        """Analyze: name = value. Check the value expression, then declare the variable."""
        # First, analyze the right-hand side (value might reference other variables)
        self._analyze_expression(node.value)

        # Infer the type from the value
        inferred = self._infer_type(node.value)

        # Declare the variable in the current scope
        self.symbol_table.declare(node.name, node.line, inferred)

    def _analyze_print(self, node: Print):
        """Analyze: print(expr). Just check the expression."""
        self._analyze_expression(node.value)

    def _analyze_if(self, node: If):
        """Analyze if/elif/else with scoped blocks."""
        # Check the condition expression
        self._analyze_expression(node.condition)

        # Analyze the if-body in a new scope
        self.symbol_table.push_scope()
        for stmt in node.body:
            self._analyze_statement(stmt)
        self.symbol_table.pop_scope()

        # Analyze each elif clause
        for elif_cond, elif_body in node.elif_clauses:
            self._analyze_expression(elif_cond)
            self.symbol_table.push_scope()
            for stmt in elif_body:
                self._analyze_statement(stmt)
            self.symbol_table.pop_scope()

        # Analyze else body if present
        if node.else_body is not None:
            self.symbol_table.push_scope()
            for stmt in node.else_body:
                self._analyze_statement(stmt)
            self.symbol_table.pop_scope()

    def _analyze_while(self, node: While):
        """Analyze while loop with scoped body."""
        self._analyze_expression(node.condition)

        self.symbol_table.push_scope()
        for stmt in node.body:
            self._analyze_statement(stmt)
        self.symbol_table.pop_scope()

    # ─── Expression analysis ──────────────────────────────────────────────

    def _analyze_expression(self, node: ASTNode):
        """Recursively check all variable references in an expression."""

        if isinstance(node, Number):
            pass  # Literal - nothing to check

        elif isinstance(node, String):
            pass

        elif isinstance(node, Boolean):
            pass

        elif isinstance(node, NoneValue):
            pass

        elif isinstance(node, Identifier):
            # Variable reference - must be declared
            if not self.symbol_table.is_declared(node.name):
                self._add_error(
                    f"Variable '{node.name}' used before assignment",
                    node.line,
                )

        elif isinstance(node, BinOp):
            self._analyze_expression(node.left)
            self._analyze_expression(node.right)
            self._check_binop_types(node)

        elif isinstance(node, UnaryOp):
            self._analyze_expression(node.operand)

        elif isinstance(node, Compare):
            self._analyze_expression(node.left)
            self._analyze_expression(node.right)

        elif isinstance(node, BoolOp):
            self._analyze_expression(node.left)
            self._analyze_expression(node.right)

        else:
            self._add_error(
                f"Unknown expression type: {type(node).__name__}",
                node.line,
            )

    # ─── Type inference & checks ──────────────────────────────────────────

    def _infer_type(self, node: ASTNode) -> str:
        """
        Infer the type of an expression (best effort).
        Returns: 'int', 'str', 'bool', 'none', or 'unknown'
        """
        if isinstance(node, Number):
            return 'int'
        elif isinstance(node, String):
            return 'str'
        elif isinstance(node, Boolean):
            return 'bool'
        elif isinstance(node, NoneValue):
            return 'none'
        elif isinstance(node, Identifier):
            sym = self.symbol_table.lookup(node.name)
            if sym:
                return sym.inferred_type
            return 'unknown'
        elif isinstance(node, BinOp):
            left_type = self._infer_type(node.left)
            right_type = self._infer_type(node.right)
            if left_type == 'int' and right_type == 'int':
                return 'int'
            if left_type == 'str' and right_type == 'str' and node.op == '+':
                return 'str'
            return 'unknown'
        elif isinstance(node, UnaryOp):
            if node.op == '-':
                return 'int'
            if node.op == 'not':
                return 'bool'
            return 'unknown'
        elif isinstance(node, Compare):
            return 'bool'
        elif isinstance(node, BoolOp):
            return 'bool'
        else:
            return 'unknown'

    def _check_binop_types(self, node: BinOp):
        """Warn if a binary operation mixes incompatible types."""
        left_type = self._infer_type(node.left)
        right_type = self._infer_type(node.right)

        # Skip if either side is unknown
        if left_type == 'unknown' or right_type == 'unknown':
            return

        # String + String is fine (concatenation)
        if left_type == 'str' and right_type == 'str' and node.op == '+':
            return

        # Int op Int is fine
        if left_type == 'int' and right_type == 'int':
            return

        # Anything else is a type mismatch warning
        if left_type != right_type:
            self._add_warning(
                f"Type mismatch in '{node.op}' operation: "
                f"left is {left_type}, right is {right_type}",
                node.line,
            )

    # ─── Error / warning helpers ──────────────────────────────────────────

    def _add_error(self, message: str, line: int):
        """Record a semantic error."""
        self.errors.append(SemanticError(message, line))

    def _add_warning(self, message: str, line: int):
        """Record a semantic warning."""
        self.warnings.append(SemanticWarning(message, line))

    def get_report(self) -> dict:
        """
        Return a summary of the analysis for the API response.
        """
        return {
            'success': len(self.errors) == 0,
            'errors': [
                {'message': e.args[0], 'line': e.line}
                for e in self.errors
            ],
            'warnings': [
                {'message': w.message, 'line': w.line}
                for w in self.warnings
            ],
            'symbols': [
                {
                    'name': s.name,
                    'declared_line': s.declared_line,
                    'scope_depth': s.scope_depth,
                    'inferred_type': s.inferred_type,
                }
                for s in self.symbol_table.get_all_symbols()
            ],
        }
