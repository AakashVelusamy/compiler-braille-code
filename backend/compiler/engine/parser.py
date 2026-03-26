"""
BrailleCode Compiler - Parser
===============================

Recursive descent parser that converts a token stream into an AST.

Grammar (informal):
    program     → statement*
    statement   → assign | print_stmt | if_stmt | while_stmt
    assign      → IDENTIFIER ASSIGN expression NEWLINE
    print_stmt  → PRINT LPAREN expression RPAREN NEWLINE
    if_stmt     → IF expression COLON NEWLINE INDENT block DEDENT
                   (ELIF expression COLON NEWLINE INDENT block DEDENT)*
                   (ELSE COLON NEWLINE INDENT block DEDENT)?
    while_stmt  → WHILE expression COLON NEWLINE INDENT block DEDENT
    block       → statement+

    expression  → or_expr
    or_expr     → and_expr (OR and_expr)*
    and_expr    → not_expr (AND not_expr)*
    not_expr    → NOT not_expr | comparison
    comparison  → arith_expr ((== | != | < | > | <= | >=) arith_expr)?
    arith_expr  → term ((+ | -) term)*
    term        → factor ((* | / | %) factor)*
    factor      → (+ | -) factor | atom
    atom        → INTEGER | STRING | TRUE | FALSE | NONE
               | IDENTIFIER | LPAREN expression RPAREN
"""

from typing import List, Optional

from .tokens import Token, TokenType
from .ast_nodes import (
    ASTNode, Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
)


class ParseError(Exception):
    """Raised when the parser encounters a syntax error."""

    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Line {token.line}: {message} (got {token.type.name} = {token.value!r})")


class Parser:
    """
    Recursive descent parser for BrailleCode.

    Usage:
        parser = Parser(tokens)
        ast = parser.parse()
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ─── Token navigation helpers ─────────────────────────────────────────

    def _current(self) -> Token:
        """Return the current token without advancing."""
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        """Look ahead by `offset` tokens."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _advance(self) -> Token:
        """Return the current token and move to the next."""
        token = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        """
        Assert the current token is of the given type.
        Consumes and returns it; raises ParseError if wrong type.
        """
        tok = self._current()
        if tok.type != token_type:
            raise ParseError(
                f"Expected {token_type.name}, got {tok.type.name}",
                tok,
            )
        return self._advance()

    def _match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types (no consume)."""
        return self._current().type in token_types

    def _skip_newlines(self):
        """Skip over any NEWLINE tokens."""
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    # ─── Entry point ──────────────────────────────────────────────────────

    def parse(self) -> Program:
        """Parse the full token stream and return a Program AST node."""
        program = Program(line=1, body=[])

        self._skip_newlines()

        while self._current().type != TokenType.EOF:
            stmt = self._parse_statement()
            program.body.append(stmt)
            self._skip_newlines()

        return program

    # ─── Statement parsing ────────────────────────────────────────────────

    def _parse_statement(self) -> ASTNode:
        """Parse a single statement."""
        tok = self._current()

        if tok.type == TokenType.PRINT:
            return self._parse_print()

        if tok.type == TokenType.IF:
            return self._parse_if()

        if tok.type == TokenType.WHILE:
            return self._parse_while()

        if tok.type == TokenType.IDENTIFIER:
            # Look ahead: if next token is ASSIGN, it's an assignment
            if self._peek().type == TokenType.ASSIGN:
                return self._parse_assign()
            # Otherwise fall through to expression statement
            # (not officially in our grammar, but handle gracefully)

        # Default: expression statement (shouldn't normally occur in our language)
        raise ParseError(
            f"Unexpected token at start of statement: {tok.type.name}",
            tok,
        )

    def _parse_assign(self) -> Assign:
        """Parse: IDENTIFIER = expression NEWLINE"""
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expression()
        self._expect(TokenType.NEWLINE)

        return Assign(line=name_tok.line, name=name_tok.value, value=value)

    def _parse_print(self) -> Print:
        """Parse: print(expression) NEWLINE"""
        tok = self._expect(TokenType.PRINT)
        self._expect(TokenType.LPAREN)
        value = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.NEWLINE)

        return Print(line=tok.line, value=value)

    def _parse_if(self) -> If:
        """
        Parse:
            if condition: NEWLINE INDENT block DEDENT
            (elif condition: NEWLINE INDENT block DEDENT)*
            (else: NEWLINE INDENT block DEDENT)?
        """
        tok = self._expect(TokenType.IF)
        condition = self._parse_expression()
        self._expect(TokenType.COLON)
        self._expect(TokenType.NEWLINE)
        body = self._parse_block()

        # Collect elif clauses
        elif_clauses = []
        while self._current().type == TokenType.ELIF:
            self._advance()  # consume ELIF
            elif_cond = self._parse_expression()
            self._expect(TokenType.COLON)
            self._expect(TokenType.NEWLINE)
            elif_body = self._parse_block()
            elif_clauses.append((elif_cond, elif_body))

        # Optional else
        else_body = None
        if self._current().type == TokenType.ELSE:
            self._advance()  # consume ELSE
            self._expect(TokenType.COLON)
            self._expect(TokenType.NEWLINE)
            else_body = self._parse_block()

        return If(
            line=tok.line,
            condition=condition,
            body=body,
            elif_clauses=elif_clauses,
            else_body=else_body,
        )

    def _parse_while(self) -> While:
        """Parse: while condition: NEWLINE INDENT block DEDENT"""
        tok = self._expect(TokenType.WHILE)
        condition = self._parse_expression()
        self._expect(TokenType.COLON)
        self._expect(TokenType.NEWLINE)
        body = self._parse_block()

        return While(line=tok.line, condition=condition, body=body)

    def _parse_block(self) -> List[ASTNode]:
        """Parse an indented block: INDENT statement+ DEDENT"""
        self._expect(TokenType.INDENT)
        statements = []

        while self._current().type not in (TokenType.DEDENT, TokenType.EOF):
            self._skip_newlines()
            if self._current().type in (TokenType.DEDENT, TokenType.EOF):
                break
            stmt = self._parse_statement()
            statements.append(stmt)

        self._expect(TokenType.DEDENT)

        if not statements:
            raise ParseError("Empty block — expected at least one statement", self._current())

        return statements

    # ─── Expression parsing (operator precedence) ─────────────────────────
    #
    #   Precedence (lowest → highest):
    #     or
    #     and
    #     not
    #     comparisons (==, !=, <, >, <=, >=)
    #     addition / subtraction (+, -)
    #     multiplication / division / modulo (*, /, %)
    #     unary (+, -)
    #     atoms (numbers, strings, booleans, identifiers, parenthesized)
    #

    def _parse_expression(self) -> ASTNode:
        """Parse an expression (entry: lowest precedence = or)."""
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """or_expr → and_expr (OR and_expr)*"""
        left = self._parse_and()

        while self._current().type == TokenType.OR:
            op_tok = self._advance()
            right = self._parse_and()
            left = BoolOp(line=op_tok.line, left=left, op='or', right=right)

        return left

    def _parse_and(self) -> ASTNode:
        """and_expr → not_expr (AND not_expr)*"""
        left = self._parse_not()

        while self._current().type == TokenType.AND:
            op_tok = self._advance()
            right = self._parse_not()
            left = BoolOp(line=op_tok.line, left=left, op='and', right=right)

        return left

    def _parse_not(self) -> ASTNode:
        """not_expr → NOT not_expr | comparison"""
        if self._current().type == TokenType.NOT:
            op_tok = self._advance()
            operand = self._parse_not()
            return UnaryOp(line=op_tok.line, op='not', operand=operand)

        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        """comparison → arith_expr ((== | != | < | > | <= | >=) arith_expr)?"""
        left = self._parse_arith()

        cmp_types = {
            TokenType.EQUAL:      '==',
            TokenType.NOT_EQUAL:  '!=',
            TokenType.LESS:       '<',
            TokenType.GREATER:    '>',
            TokenType.LESS_EQ:    '<=',
            TokenType.GREATER_EQ: '>=',
        }

        if self._current().type in cmp_types:
            op_tok = self._advance()
            op_str = cmp_types[op_tok.type]
            right = self._parse_arith()
            return Compare(line=op_tok.line, left=left, op=op_str, right=right)

        return left

    def _parse_arith(self) -> ASTNode:
        """arith_expr → term ((+ | -) term)*"""
        left = self._parse_term()

        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_term()
            left = BinOp(line=op_tok.line, left=left, op=op_tok.value, right=right)

        return left

    def _parse_term(self) -> ASTNode:
        """term → factor ((* | / | %) factor)*"""
        left = self._parse_factor()

        while self._current().type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op_tok = self._advance()
            right = self._parse_factor()
            left = BinOp(line=op_tok.line, left=left, op=op_tok.value, right=right)

        return left

    def _parse_factor(self) -> ASTNode:
        """factor → (+ | -) factor | atom"""
        if self._current().type == TokenType.MINUS:
            op_tok = self._advance()
            operand = self._parse_factor()
            return UnaryOp(line=op_tok.line, op='-', operand=operand)

        if self._current().type == TokenType.PLUS:
            self._advance()  # unary + is a no-op
            return self._parse_factor()

        return self._parse_atom()

    def _parse_atom(self) -> ASTNode:
        """atom → INTEGER | STRING | TRUE | FALSE | NONE | IDENTIFIER | LPAREN expr RPAREN"""
        tok = self._current()

        if tok.type == TokenType.INTEGER:
            self._advance()
            return Number(line=tok.line, value=tok.value)

        if tok.type == TokenType.STRING:
            self._advance()
            return String(line=tok.line, value=tok.value)

        if tok.type == TokenType.TRUE:
            self._advance()
            return Boolean(line=tok.line, value=True)

        if tok.type == TokenType.FALSE:
            self._advance()
            return Boolean(line=tok.line, value=False)

        if tok.type == TokenType.NONE:
            self._advance()
            return NoneValue(line=tok.line)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(line=tok.line, name=tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()  # consume (
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"Unexpected token in expression: {tok.type.name}", tok)
