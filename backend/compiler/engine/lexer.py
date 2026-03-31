"""
BrailleCode Compiler - Lexer
==============================

Scans Braille-encoded source code and produces a stream of tokens.

The lexer handles:
  - Keyword recognition (via keyword prefix ⠈⠼ followed by keyword pattern)
  - Number literals (via number prefix ⠼ followed by digit patterns)
  - String literals (between Braille quote markers ⠦)
  - Identifiers (sequences of Braille letter patterns, with capital prefix ⠠
    and underscore indicator ⠸)
  - Operators and punctuation (single and multi-cell patterns)
  - Indentation-based scoping: emits INDENT / DEDENT tokens like Python
  - Line structure: emits NEWLINE tokens between logical lines
"""

from typing import List

from .braille_map import (
    BRAILLE_SPACE, BRAILLE_NEWLINE, BRAILLE_INDENT,
    KEYWORD_PREFIX, NUMBER_PREFIX, CAPITAL_PREFIX,
    REVERSE_LETTERS, REVERSE_DIGITS, REVERSE_KEYWORDS,
    REVERSE_OPERATORS, REVERSE_PUNCTUATION,
    OPERATORS, PUNCTUATION,
)
from .tokens import Token, TokenType, KEYWORD_TOKEN_MAP


class LexerError(Exception):
    """Raised when the lexer encounters an unrecognized Braille pattern."""

    def __init__(self, message: str, line: int):
        self.line = line
        super().__init__(f"Line {line}: {message}")


class Lexer:
    """
    Converts a Braille string into a list of Tokens.

    Usage:
        lexer = Lexer(braille_string)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str):
        """
        Args:
            source: Braille-encoded source string (output of Translator.english_to_braille)
        """
        self.source = source
        self.tokens: List[Token] = []
        self.line = 1

        # Indentation tracking - a stack of indent levels (in number of BRAILLE_INDENT units)
        # Starts at 0 (no indentation)
        self.indent_stack: List[int] = [0]

        # Pre-sort reverse maps for longest-first greedy matching
        self._sorted_rev_operators = sorted(
            REVERSE_OPERATORS.keys(), key=len, reverse=True
        )
        self._sorted_rev_punctuation = sorted(
            REVERSE_PUNCTUATION.keys(), key=len, reverse=True
        )
        self._sorted_rev_keywords = sorted(
            REVERSE_KEYWORDS.keys(), key=len, reverse=True
        )

        # Operator English → TokenType mapping
        self._op_token_map = {
            '+':  TokenType.PLUS,
            '-':  TokenType.MINUS,
            '*':  TokenType.MULTIPLY,
            '/':  TokenType.DIVIDE,
            '%':  TokenType.MODULO,
            '=':  TokenType.ASSIGN,
            '==': TokenType.EQUAL,
            '!=': TokenType.NOT_EQUAL,
            '<':  TokenType.LESS,
            '>':  TokenType.GREATER,
            '<=': TokenType.LESS_EQ,
            '>=': TokenType.GREATER_EQ,
        }

        # Punctuation English → TokenType mapping
        self._punc_token_map = {
            '(':  TokenType.LPAREN,
            ')':  TokenType.RPAREN,
            ':':  TokenType.COLON,
            ',':  TokenType.COMMA,
        }

    def tokenize(self) -> List[Token]:
        """
        Scan the entire Braille source and return a list of tokens.

        Returns:
            List of Token objects, ending with an EOF token.
        """
        # Split into lines using the Braille newline delimiter
        lines = self.source.split(BRAILLE_NEWLINE)

        for line_idx, braille_line in enumerate(lines):
            self.line = line_idx + 1

            # Skip completely empty lines
            if not braille_line:
                continue

            # ── Step 1: Measure indentation ──────────────────────────────
            indent_level = 0
            pos = 0
            indent_unit = BRAILLE_INDENT  # ⠀⠀ (double Braille space)

            while braille_line[pos:pos + len(indent_unit)] == indent_unit:
                indent_level += 1
                pos += len(indent_unit)

            # ── Step 2: Emit INDENT / DEDENT tokens ──────────────────────
            current_indent = self.indent_stack[-1]

            if indent_level > current_indent:
                # Indentation increased - push new level, emit INDENT
                self.indent_stack.append(indent_level)
                self.tokens.append(Token(TokenType.INDENT, indent_level, self.line))

            elif indent_level < current_indent:
                # Indentation decreased - pop levels, emit DEDENT for each
                while (self.indent_stack
                       and self.indent_stack[-1] > indent_level):
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, indent_level, self.line))

                # Verify we landed on a valid indent level
                if self.indent_stack[-1] != indent_level:
                    raise LexerError(
                        f"Indentation level {indent_level} does not match any outer block "
                        f"(expected one of {self.indent_stack})",
                        self.line,
                    )

            # ── Step 3: Tokenize the line content ────────────────────────
            self._tokenize_line(braille_line, pos)

            # Emit NEWLINE at end of each logical line
            self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line))

        # ── Step 4: Close remaining indentation at EOF ───────────────────
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line))

        # Final EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line))

        return self.tokens

    def _tokenize_line(self, braille_line: str, start: int):
        """
        Tokenize a single line starting from position `start` (after indentation).
        """
        i = start
        length = len(braille_line)

        while i < length:
            # ── Skip Braille spaces between tokens ───────────────────────
            if braille_line[i] == BRAILLE_SPACE:
                i += 1
                continue

            # ── Keyword prefix (⠈⠼) ─────────────────────────────────────
            kp_len = len(KEYWORD_PREFIX)
            if braille_line[i:i + kp_len] == KEYWORD_PREFIX:
                i += kp_len
                matched = False

                for braille_kw in self._sorted_rev_keywords:
                    if braille_line[i:i + len(braille_kw)] == braille_kw:
                        keyword_name = REVERSE_KEYWORDS[braille_kw]
                        token_type = KEYWORD_TOKEN_MAP[keyword_name]
                        self.tokens.append(Token(token_type, keyword_name, self.line))
                        i += len(braille_kw)
                        matched = True
                        break

                if not matched:
                    raise LexerError(
                        f"Unrecognized keyword pattern after keyword prefix at position {i}",
                        self.line,
                    )
                continue

            # ── Number prefix (⠼) ────────────────────────────────────────
            if braille_line[i] == NUMBER_PREFIX:
                i += 1  # skip prefix
                num_str = ''

                while i < length and braille_line[i] in REVERSE_DIGITS:
                    num_str += REVERSE_DIGITS[braille_line[i]]
                    i += 1

                if not num_str:
                    raise LexerError(
                        f"Number prefix without digits at position {i}",
                        self.line,
                    )

                self.tokens.append(Token(TokenType.INTEGER, int(num_str), self.line))
                continue

            # ── String literal (between ⠦ quote markers) ────────────────
            if braille_line[i] == PUNCTUATION['"']:
                i += 1  # skip opening quote
                string_chars = []

                while i < length and braille_line[i] != PUNCTUATION['"']:
                    ch = braille_line[i]

                    if ch == BRAILLE_SPACE:
                        string_chars.append(' ')
                        i += 1
                    elif ch == CAPITAL_PREFIX:
                        i += 1
                        if i < length and braille_line[i] in REVERSE_LETTERS:
                            string_chars.append(REVERSE_LETTERS[braille_line[i]].upper())
                            i += 1
                    elif ch == NUMBER_PREFIX:
                        i += 1
                        while i < length and braille_line[i] in REVERSE_DIGITS:
                            string_chars.append(REVERSE_DIGITS[braille_line[i]])
                            i += 1
                    elif ch in REVERSE_LETTERS:
                        string_chars.append(REVERSE_LETTERS[ch])
                        i += 1
                    else:
                        # Unknown char inside string - keep raw
                        string_chars.append(ch)
                        i += 1

                if i >= length:
                    raise LexerError("Unterminated string literal", self.line)

                i += 1  # skip closing quote
                self.tokens.append(Token(TokenType.STRING, ''.join(string_chars), self.line))
                continue

            # ── Operators (longest match first) ──────────────────────────
            matched = False
            for braille_op in self._sorted_rev_operators:
                if braille_line[i:i + len(braille_op)] == braille_op:
                    eng_op = REVERSE_OPERATORS[braille_op]
                    token_type = self._op_token_map[eng_op]
                    self.tokens.append(Token(token_type, eng_op, self.line))
                    i += len(braille_op)
                    matched = True
                    break
            if matched:
                continue

            # ── Punctuation (longest match first) ────────────────────────
            for braille_punc in self._sorted_rev_punctuation:
                if braille_line[i:i + len(braille_punc)] == braille_punc:
                    eng_punc = REVERSE_PUNCTUATION[braille_punc]
                    if eng_punc in self._punc_token_map:
                        token_type = self._punc_token_map[eng_punc]
                        self.tokens.append(Token(token_type, eng_punc, self.line))
                    # skip quote chars - handled in string literal section
                    i += len(braille_punc)
                    matched = True
                    break
            if matched:
                continue

            # ── Capital prefix (⠠) - start of uppercase identifier char ──
            if braille_line[i] == CAPITAL_PREFIX:
                # This is a capital letter in an identifier - collect full identifier
                ident = self._read_identifier(braille_line, i)
                i = ident['end_pos']
                self.tokens.append(Token(TokenType.IDENTIFIER, ident['name'], self.line))
                continue

            # ── Underscore indicator (⠸) - identifier starts with _ ──────
            if braille_line[i] == '⠸':
                ident = self._read_identifier(braille_line, i)
                i = ident['end_pos']
                self.tokens.append(Token(TokenType.IDENTIFIER, ident['name'], self.line))
                continue

            # ── Braille letter - start of identifier ─────────────────────
            if braille_line[i] in REVERSE_LETTERS:
                ident = self._read_identifier(braille_line, i)
                i = ident['end_pos']
                self.tokens.append(Token(TokenType.IDENTIFIER, ident['name'], self.line))
                continue

            # ── Unknown character ─────────────────────────────────────────
            raise LexerError(
                f"Unrecognized Braille character '{braille_line[i]}' "
                f"(U+{ord(braille_line[i]):04X}) at position {i}",
                self.line,
            )

    def _read_identifier(self, braille_line: str, start: int) -> dict:
        """
        Read a complete identifier starting at `start`.

        Identifiers can contain:
          - Braille letters (REVERSE_LETTERS)
          - Capital prefix (⠠) + letter
          - Underscore indicator (⠸)
          - Number prefix (⠼) + digit (for identifiers like var1)

        Returns:
            dict with 'name' (str) and 'end_pos' (int)
        """
        chars = []
        i = start
        length = len(braille_line)

        while i < length:
            ch = braille_line[i]

            # Lowercase letter
            if ch in REVERSE_LETTERS:
                chars.append(REVERSE_LETTERS[ch])
                i += 1
                continue

            # Capital prefix → uppercase letter
            if ch == CAPITAL_PREFIX:
                i += 1
                if i < length and braille_line[i] in REVERSE_LETTERS:
                    chars.append(REVERSE_LETTERS[braille_line[i]].upper())
                    i += 1
                continue

            # Underscore
            if ch == '⠸':
                chars.append('_')
                i += 1
                continue

            # Digit in identifier (e.g. x1, var2)
            if ch == NUMBER_PREFIX:
                i += 1
                while i < length and braille_line[i] in REVERSE_DIGITS:
                    chars.append(REVERSE_DIGITS[braille_line[i]])
                    i += 1
                continue

            # Anything else → end of identifier
            break

        return {'name': ''.join(chars), 'end_pos': i}
