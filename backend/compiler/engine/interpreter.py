"""
BrailleCode Compiler - Tree-Walk Interpreter
==============================================

Walks the AST produced by the parser and executes the program.

Responsibilities:
  - Maintain a runtime environment (variable bindings per scope)
  - Evaluate expressions (arithmetic, comparisons, boolean logic)
  - Execute statements (assignments, print, if/elif/else, while)
  - Collect printed output into a list for the API response
  - Enforce a maximum iteration limit to prevent infinite loops

The interpreter shares the same scoping model as the semantic analyzer:
variables declared in inner blocks are discarded on block exit, but
inner blocks can read and write variables from enclosing scopes.
"""

from typing import Any, Dict, List, Optional

from .ast_nodes import (
    ASTNode, Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
)


# ─── Errors ───────────────────────────────────────────────────────────────────

class RuntimeError_(Exception):
    """Raised when the interpreter encounters a runtime error."""

    def __init__(self, message: str, line: int):
        self.line = line
        super().__init__(f"Line {line}: {message}")


class MaxIterationsError(RuntimeError_):
    """Raised when a while loop exceeds the iteration limit."""
    pass


# ─── Runtime Environment ─────────────────────────────────────────────────────

class Environment:
    """
    Runtime variable storage with lexical scoping.

    Similar to the SymbolTable but stores actual runtime values
    instead of type metadata. Inner scopes can read and WRITE
    variables from enclosing scopes (unlike the analyzer which
    only tracks declarations).
    """

    def __init__(self):
        self._scopes: List[Dict[str, Any]] = [{}]

    def push_scope(self):
        """Enter a new block scope."""
        self._scopes.append({})

    def pop_scope(self):
        """Exit the current block scope."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    def get(self, name: str) -> Any:
        """
        Look up a variable's value, searching from innermost to outermost scope.
        Raises KeyError if not found.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        raise KeyError(name)

    def set(self, name: str, value: Any):
        """
        Set a variable's value.

        If the variable already exists in any enclosing scope, update it there
        (this allows `x = x - 1` inside a while loop to modify the outer x).
        Otherwise, create it in the current (innermost) scope.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                scope[name] = value
                return
        # New variable - declare in current scope
        self._scopes[-1][name] = value

    def get_all(self) -> Dict[str, Any]:
        """Return a flat dict of all visible variables (for debugging)."""
        merged = {}
        for scope in self._scopes:
            merged.update(scope)
        return merged


# ─── Interpreter ──────────────────────────────────────────────────────────────

class Interpreter:
    """
    Tree-walk interpreter for BrailleCode.

    Usage:
        interp = Interpreter()
        result = interp.execute(ast)
        print(result['output'])   # list of printed lines
    """

    MAX_ITERATIONS = 10000  # safety limit for while loops

    def __init__(self):
        self.env = Environment()
        self.output: List[str] = []
        self.errors: List[dict] = []

    def execute(self, program: Program) -> dict:
        """
        Execute a full program and return the result.

        Returns:
            {
                'output':    list of printed strings,
                'variables': dict of final variable states,
                'errors':    list of runtime errors (if any),
                'success':   bool
            }
        """
        try:
            for stmt in program.body:
                self._exec_statement(stmt)
        except RuntimeError_ as e:
            self.errors.append({'message': str(e), 'line': e.line})
        except Exception as e:
            self.errors.append({'message': f"Internal error: {e}", 'line': 0})

        return {
            'output': self.output,
            'variables': self.env.get_all(),
            'errors': self.errors,
            'success': len(self.errors) == 0,
        }

    # ─── Statement execution ──────────────────────────────────────────────

    def _exec_statement(self, node: ASTNode):
        """Dispatch to the appropriate statement executor."""

        if isinstance(node, Assign):
            self._exec_assign(node)
        elif isinstance(node, Print):
            self._exec_print(node)
        elif isinstance(node, If):
            self._exec_if(node)
        elif isinstance(node, While):
            self._exec_while(node)
        else:
            raise RuntimeError_(
                f"Unknown statement type: {type(node).__name__}", node.line
            )

    def _exec_assign(self, node: Assign):
        """Execute: name = value"""
        value = self._eval_expression(node.value)
        self.env.set(node.name, value)

    def _exec_print(self, node: Print):
        """Execute: print(expression) - appends the string representation to output."""
        value = self._eval_expression(node.value)
        self.output.append(self._to_display_string(value))

    def _exec_if(self, node: If):
        """Execute: if / elif / else"""
        # Evaluate the if condition
        if self._is_truthy(self._eval_expression(node.condition)):
            self.env.push_scope()
            for stmt in node.body:
                self._exec_statement(stmt)
            self.env.pop_scope()
            return

        # Check elif clauses
        for elif_cond, elif_body in node.elif_clauses:
            if self._is_truthy(self._eval_expression(elif_cond)):
                self.env.push_scope()
                for stmt in elif_body:
                    self._exec_statement(stmt)
                self.env.pop_scope()
                return

        # Else block
        if node.else_body is not None:
            self.env.push_scope()
            for stmt in node.else_body:
                self._exec_statement(stmt)
            self.env.pop_scope()

    def _exec_while(self, node: While):
        """Execute: while condition: body (with iteration limit)."""
        iterations = 0

        while self._is_truthy(self._eval_expression(node.condition)):
            iterations += 1
            if iterations > self.MAX_ITERATIONS:
                raise MaxIterationsError(
                    f"While loop exceeded maximum iterations ({self.MAX_ITERATIONS})",
                    node.line,
                )

            self.env.push_scope()
            for stmt in node.body:
                self._exec_statement(stmt)
            self.env.pop_scope()

    # ─── Expression evaluation ────────────────────────────────────────────

    def _eval_expression(self, node: ASTNode) -> Any:
        """Evaluate an expression node and return its Python value."""

        if isinstance(node, Number):
            return node.value

        if isinstance(node, String):
            return node.value

        if isinstance(node, Boolean):
            return node.value

        if isinstance(node, NoneValue):
            return None

        if isinstance(node, Identifier):
            return self._eval_identifier(node)

        if isinstance(node, BinOp):
            return self._eval_binop(node)

        if isinstance(node, UnaryOp):
            return self._eval_unaryop(node)

        if isinstance(node, Compare):
            return self._eval_compare(node)

        if isinstance(node, BoolOp):
            return self._eval_boolop(node)

        raise RuntimeError_(
            f"Unknown expression type: {type(node).__name__}", node.line
        )

    def _eval_identifier(self, node: Identifier) -> Any:
        """Look up a variable's value."""
        try:
            return self.env.get(node.name)
        except KeyError:
            raise RuntimeError_(
                f"Undefined variable '{node.name}'", node.line
            )

    def _eval_binop(self, node: BinOp) -> Any:
        """Evaluate a binary operation: left op right."""
        left = self._eval_expression(node.left)
        right = self._eval_expression(node.right)

        try:
            if node.op == '+':
                # Support both int addition and string concatenation
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                raise RuntimeError_(
                    f"Cannot add {type(left).__name__} and {type(right).__name__}",
                    node.line,
                )

            if node.op == '-':
                return left - right

            if node.op == '*':
                return left * right

            if node.op == '/':
                if right == 0:
                    raise RuntimeError_("Division by zero", node.line)
                # Integer division (like Python's //)
                return left // right

            if node.op == '%':
                if right == 0:
                    raise RuntimeError_("Modulo by zero", node.line)
                return left % right

        except TypeError as e:
            raise RuntimeError_(
                f"Type error in '{node.op}' operation: {e}", node.line
            )

        raise RuntimeError_(f"Unknown operator '{node.op}'", node.line)

    def _eval_unaryop(self, node: UnaryOp) -> Any:
        """Evaluate a unary operation: op operand."""
        operand = self._eval_expression(node.operand)

        if node.op == '-':
            if not isinstance(operand, (int, float)):
                raise RuntimeError_(
                    f"Cannot negate {type(operand).__name__}", node.line
                )
            return -operand

        if node.op == 'not':
            return not self._is_truthy(operand)

        raise RuntimeError_(f"Unknown unary operator '{node.op}'", node.line)

    def _eval_compare(self, node: Compare) -> bool:
        """Evaluate a comparison: left op right."""
        left = self._eval_expression(node.left)
        right = self._eval_expression(node.right)

        try:
            if node.op == '==':
                return left == right
            if node.op == '!=':
                return left != right
            if node.op == '<':
                return left < right
            if node.op == '>':
                return left > right
            if node.op == '<=':
                return left <= right
            if node.op == '>=':
                return left >= right
        except TypeError as e:
            raise RuntimeError_(
                f"Cannot compare {type(left).__name__} and {type(right).__name__} "
                f"with '{node.op}'",
                node.line,
            )

        raise RuntimeError_(f"Unknown comparison operator '{node.op}'", node.line)

    def _eval_boolop(self, node: BoolOp) -> Any:
        """
        Evaluate boolean logic: left and/or right.
        Uses short-circuit evaluation like Python.
        """
        left = self._eval_expression(node.left)

        if node.op == 'and':
            # Short-circuit: if left is falsy, return left without evaluating right
            if not self._is_truthy(left):
                return left
            return self._eval_expression(node.right)

        if node.op == 'or':
            # Short-circuit: if left is truthy, return left without evaluating right
            if self._is_truthy(left):
                return left
            return self._eval_expression(node.right)

        raise RuntimeError_(f"Unknown boolean operator '{node.op}'", node.line)

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _is_truthy(self, value: Any) -> bool:
        """
        Determine truthiness (Python-compatible rules):
          False, 0, None, "" → falsy
          Everything else → truthy
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def _to_display_string(self, value: Any) -> str:
        """Convert a runtime value to its display string for print output."""
        if value is None:
            return 'None'
        if isinstance(value, bool):
            return 'True' if value else 'False'
        return str(value)
