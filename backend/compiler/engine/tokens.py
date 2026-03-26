"""
BrailleCode Compiler - Token Definitions
=========================================

Defines all token types produced by the lexer.
Each token carries a type, a value, and a line number for error reporting.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    """All token types recognized by the BrailleCode lexer."""

    # ─── Literals ─────────────────────────────────────────────────────────
    INTEGER     = auto()   # e.g. 10, 42, 0
    STRING      = auto()   # e.g. "hello"

    # ─── Identifiers & Keywords ───────────────────────────────────────────
    IDENTIFIER  = auto()   # e.g. x, result, my_var
    PRINT       = auto()
    IF          = auto()
    ELSE        = auto()
    ELIF        = auto()
    WHILE       = auto()
    TRUE        = auto()
    FALSE       = auto()
    AND         = auto()
    OR          = auto()
    NOT         = auto()
    NONE        = auto()

    # ─── Operators ────────────────────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    MULTIPLY    = auto()   # *
    DIVIDE      = auto()   # /
    MODULO      = auto()   # %
    ASSIGN      = auto()   # =
    EQUAL       = auto()   # ==
    NOT_EQUAL   = auto()   # !=
    LESS        = auto()   # <
    GREATER     = auto()   # >
    LESS_EQ     = auto()   # <=
    GREATER_EQ  = auto()   # >=

    # ─── Punctuation ──────────────────────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    COLON       = auto()   # :
    COMMA       = auto()   # ,

    # ─── Structure ────────────────────────────────────────────────────────
    INDENT      = auto()   # increase in indentation level
    DEDENT      = auto()   # decrease in indentation level
    NEWLINE     = auto()   # end of a logical line

    # ─── Special ──────────────────────────────────────────────────────────
    EOF         = auto()   # end of input


# Map keyword names → token types
KEYWORD_TOKEN_MAP = {
    'print': TokenType.PRINT,
    'if':    TokenType.IF,
    'else':  TokenType.ELSE,
    'elif':  TokenType.ELIF,
    'while': TokenType.WHILE,
    'True':  TokenType.TRUE,
    'False': TokenType.FALSE,
    'and':   TokenType.AND,
    'or':    TokenType.OR,
    'not':   TokenType.NOT,
    'None':  TokenType.NONE,
}


@dataclass
class Token:
    """
    A single token produced by the lexer.

    Attributes:
        type:  The TokenType category
        value: The actual value (int for INTEGER, str for STRING/IDENTIFIER, etc.)
        line:  The source line number (1-indexed) for error messages
    """
    type: TokenType
    value: Any
    line: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"
