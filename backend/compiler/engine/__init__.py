"""BrailleCode Compiler Engine — core compiler pipeline modules."""

from .braille_map import get_full_mapping
from .translator import Translator, TranslationError
from .tokens import Token, TokenType
from .lexer import Lexer, LexerError
from .parser import Parser, ParseError
from .ast_nodes import (
    Program, Assign, Print, If, While,
    BinOp, UnaryOp, Compare, BoolOp,
    Number, String, Boolean, NoneValue, Identifier,
    ast_to_dict, print_ast,
)
from .analyzer import SemanticAnalyzer, SemanticError, SymbolTable
from .interpreter import Interpreter, RuntimeError_, MaxIterationsError
from .tokens import Token, TokenType
from .lexer import Lexer, LexerError
