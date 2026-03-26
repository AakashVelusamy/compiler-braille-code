"""
BrailleCode Compiler - Braille Mapping Table
=============================================

Maps English characters, keywords, operators, and special symbols
to six-dot Braille Unicode patterns (U+2800 - U+283F).

Braille Unicode block:
  Each character is a 6-dot cell:  dots 1-3 (left column), dots 4-6 (right column)
    ⠁ = dot 1      ⠂ = dot 2      ⠄ = dot 3
    ⠈ = dot 4      ⠐ = dot 5      ⠠ = dot 6

  The Unicode codepoint is U+2800 + (sum of dot bit values)
"""

# ─── Single-character mappings ────────────────────────────────────────────────

# Lowercase letters (standard Grade 1 Braille)
LETTERS = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
    'z': '⠵',
}

# Uppercase: Braille capital indicator (⠠) + letter
CAPITAL_PREFIX = '⠠'

# Digits use Braille number indicator (⠼) followed by a-j pattern
NUMBER_PREFIX = '⠼'
DIGITS = {
    '0': '⠚', '1': '⠁', '2': '⠃', '3': '⠉', '4': '⠙',
    '5': '⠑', '6': '⠋', '7': '⠛', '8': '⠓', '9': '⠊',
}

# ─── Operators and punctuation ────────────────────────────────────────────────

OPERATORS = {
    '+':  '⠬',   # plus
    '-':  '⠤',   # minus / hyphen
    '*':  '⠡',   # multiply
    '/':  '⠌',   # divide
    '%':  '⠒⠏',  # modulo (custom: dots-25 + p)
    '=':  '⠶',   # equals (assignment)
    '==': '⠶⠶',  # equality comparison
    '!=': '⠌⠶',  # not equal
    '<':  '⠣',   # less than
    '>':  '⠜',   # greater than
    '<=': '⠣⠶',  # less than or equal
    '>=': '⠜⠶',  # greater than or equal
}

PUNCTUATION = {
    '(':  '⠐⠣',  # left paren
    ')':  '⠐⠜',  # right paren
    ':':  '⠒',   # colon (used after if/else/while)
    ',':  '⠂',   # comma
    '"':  '⠦',   # double quote (opening)
    "'":  '⠄',   # single quote / apostrophe
}

# ─── Keywords ─────────────────────────────────────────────────────────────────
# Each keyword is mapped to a unique multi-cell Braille pattern
# We use the Braille letters for the keyword spelled out,
# but preceded by a keyword indicator (⠈⠼) to distinguish from identifiers.

KEYWORD_PREFIX = '⠈⠼'  # dots-4 + dots-3456 — signals "next token is a keyword"

KEYWORDS = {
    'print':  '⠏⠗⠊⠝⠞',
    'if':     '⠊⠋',
    'else':   '⠑⠇⠎⠑',
    'elif':   '⠑⠇⠊⠋',
    'while':  '⠺⠓⠊⠇⠑',
    'True':   '⠞⠗⠥⠑',
    'False':  '⠋⠁⠇⠎⠑',
    'and':    '⠁⠝⠙',
    'or':     '⠕⠗',
    'not':    '⠝⠕⠞',
    'None':   '⠝⠕⠝⠑',
}

# ─── Whitespace ───────────────────────────────────────────────────────────────

BRAILLE_SPACE = '⠀'       # U+2800 — Braille blank / space
BRAILLE_NEWLINE = '⠿'     # U+283F (all 6 dots) — unambiguous line separator
BRAILLE_INDENT = '⠀⠀'     # double space = one indent level

# ─── Reverse mappings (Braille → English) ────────────────────────────────────
# Built automatically for the lexer to use

REVERSE_LETTERS = {v: k for k, v in LETTERS.items()}
REVERSE_DIGITS = {v: k for k, v in DIGITS.items()}
REVERSE_OPERATORS = {v: k for k, v in OPERATORS.items()}
REVERSE_PUNCTUATION = {v: k for k, v in PUNCTUATION.items()}
REVERSE_KEYWORDS = {v: k for k, v in KEYWORDS.items()}


def get_full_mapping():
    """Return a combined dict of all English → Braille mappings for reference."""
    mapping = {}
    mapping['letters'] = LETTERS.copy()
    mapping['digits'] = DIGITS.copy()
    mapping['operators'] = OPERATORS.copy()
    mapping['punctuation'] = PUNCTUATION.copy()
    mapping['keywords'] = KEYWORDS.copy()
    mapping['prefixes'] = {
        'capital': CAPITAL_PREFIX,
        'number': NUMBER_PREFIX,
        'keyword': KEYWORD_PREFIX,
    }
    mapping['whitespace'] = {
        'space': BRAILLE_SPACE,
        'newline': BRAILLE_NEWLINE,
        'indent': BRAILLE_INDENT,
    }
    return mapping
