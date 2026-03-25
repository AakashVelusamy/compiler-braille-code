"""
BrailleCode Compiler - Translator
==================================

Converts English-like source code → Braille representation
and Braille output → English text.

This is the development interface layer: users write in English,
and the translator converts it to Braille before the compiler pipeline begins.
"""

from .braille_map import (
    LETTERS, CAPITAL_PREFIX, NUMBER_PREFIX, DIGITS,
    OPERATORS, PUNCTUATION, KEYWORDS, KEYWORD_PREFIX,
    BRAILLE_SPACE, BRAILLE_NEWLINE, BRAILLE_INDENT,
    REVERSE_LETTERS, REVERSE_DIGITS, REVERSE_OPERATORS,
    REVERSE_PUNCTUATION, REVERSE_KEYWORDS,
)


class TranslationError(Exception):
    """Raised when the translator encounters an unmappable character."""
    pass


class Translator:
    """Bidirectional translator between English source code and Braille."""

    def __init__(self):
        # Sort keywords longest-first so 'elif' matches before 'el' + 'if'
        self._sorted_keywords = sorted(KEYWORDS.keys(), key=len, reverse=True)

        # Sort reverse operators longest-first for greedy matching
        self._sorted_rev_operators = sorted(
            REVERSE_OPERATORS.keys(), key=len, reverse=True
        )
        # Sort reverse punctuation longest-first
        self._sorted_rev_punctuation = sorted(
            REVERSE_PUNCTUATION.keys(), key=len, reverse=True
        )
        # Sort reverse keywords longest-first
        self._sorted_rev_keywords = sorted(
            REVERSE_KEYWORDS.keys(), key=len, reverse=True
        )

    # ─── English → Braille ────────────────────────────────────────────────

    def english_to_braille(self, source: str) -> str:
        """
        Convert English source code to Braille representation.

        Process:
          1. Split source into lines
          2. For each line, detect leading indentation
          3. Tokenize the line content: keywords, numbers, identifiers, operators
          4. Map each token to its Braille equivalent

        Args:
            source: English source code string

        Returns:
            Braille-encoded string ready for the compiler pipeline
        """
        lines = source.split('\n')
        braille_lines = []

        for line in lines:
            braille_line = self._translate_line(line)
            braille_lines.append(braille_line)

        # Join lines with Braille newline delimiter
        return BRAILLE_NEWLINE.join(braille_lines)

    def _translate_line(self, line: str) -> str:
        """Translate a single line of English source to Braille."""
        # Count leading spaces (4 spaces = 1 indent level, matching Python)
        stripped = line.lstrip(' ')
        num_spaces = len(line) - len(stripped)
        indent_level = num_spaces // 4

        # Build Braille indentation
        braille_parts = [BRAILLE_INDENT * indent_level]

        # Tokenize and translate the rest of the line
        content = stripped
        i = 0

        while i < len(content):
            ch = content[i]

            # Skip regular spaces between tokens — add Braille space
            if ch == ' ':
                braille_parts.append(BRAILLE_SPACE)
                i += 1
                continue

            # Check for string literals (double quotes)
            if ch == '"':
                end = content.index('"', i + 1)
                string_content = content[i + 1:end]
                braille_parts.append(PUNCTUATION['"'])  # opening quote
                for c in string_content:
                    if c in LETTERS:
                        braille_parts.append(LETTERS[c])
                    elif c.isupper() and c.lower() in LETTERS:
                        braille_parts.append(CAPITAL_PREFIX)
                        braille_parts.append(LETTERS[c.lower()])
                    elif c == ' ':
                        braille_parts.append(BRAILLE_SPACE)
                    elif c in DIGITS:
                        braille_parts.append(NUMBER_PREFIX)
                        braille_parts.append(DIGITS[c])
                    else:
                        # For characters without a mapping, keep as-is
                        braille_parts.append(c)
                braille_parts.append(PUNCTUATION['"'])  # closing quote
                i = end + 1
                continue

            # Check for multi-char operators first (==, !=, <=, >=)
            two_char = content[i:i + 2]
            if two_char in OPERATORS:
                braille_parts.append(OPERATORS[two_char])
                i += 2
                continue

            # Single-char operators
            if ch in OPERATORS:
                braille_parts.append(OPERATORS[ch])
                i += 1
                continue

            # Punctuation
            if ch in PUNCTUATION:
                braille_parts.append(PUNCTUATION[ch])
                i += 1
                continue

            # Numbers (consecutive digits form one number token)
            if ch.isdigit():
                braille_parts.append(NUMBER_PREFIX)
                while i < len(content) and content[i].isdigit():
                    braille_parts.append(DIGITS[content[i]])
                    i += 1
                continue

            # Words: could be keyword or identifier
            if ch.isalpha() or ch == '_':
                word = ''
                j = i
                while j < len(content) and (content[j].isalnum() or content[j] == '_'):
                    word += content[j]
                    j += 1

                if word in KEYWORDS:
                    # Keyword: prefix + Braille pattern
                    braille_parts.append(KEYWORD_PREFIX)
                    braille_parts.append(KEYWORDS[word])
                else:
                    # Identifier: letter by letter
                    for c in word:
                        if c == '_':
                            braille_parts.append('⠸')  # underscore indicator
                        elif c.isupper():
                            braille_parts.append(CAPITAL_PREFIX)
                            braille_parts.append(LETTERS[c.lower()])
                        elif c.isdigit():
                            braille_parts.append(NUMBER_PREFIX)
                            braille_parts.append(DIGITS[c])
                        elif c in LETTERS:
                            braille_parts.append(LETTERS[c])
                        else:
                            raise TranslationError(
                                f"Cannot translate character '{c}' in identifier '{word}'"
                            )

                i = j
                continue

            raise TranslationError(
                f"Unexpected character '{ch}' (U+{ord(ch):04X}) at position {i}"
            )

        return ''.join(braille_parts)

    # ─── Braille → English ────────────────────────────────────────────────

    def braille_to_english(self, braille: str) -> str:
        """
        Convert Braille representation back to English text.

        Used to display program output in readable English.

        Args:
            braille: Braille-encoded string

        Returns:
            English text
        """
        lines = braille.split(BRAILLE_NEWLINE)
        english_lines = []

        for line in lines:
            english_lines.append(self._reverse_translate_line(line))

        return '\n'.join(english_lines)

    def _reverse_translate_line(self, braille_line: str) -> str:
        """Translate a single Braille line back to English."""
        result = []
        i = 0

        # Count leading indentation (BRAILLE_INDENT = double space)
        indent_count = 0
        while braille_line[i:i + len(BRAILLE_INDENT)] == BRAILLE_INDENT if i < len(braille_line) else False:
            indent_count += 1
            i += len(BRAILLE_INDENT)
        result.append('    ' * indent_count)

        while i < len(braille_line):
            # Braille space → English space
            if braille_line[i] == BRAILLE_SPACE:
                result.append(' ')
                i += 1
                continue

            # Keyword prefix
            if braille_line[i:i + len(KEYWORD_PREFIX)] == KEYWORD_PREFIX:
                i += len(KEYWORD_PREFIX)
                # Try matching keyword patterns (longest first)
                matched = False
                for braille_kw in self._sorted_rev_keywords:
                    if braille_line[i:i + len(braille_kw)] == braille_kw:
                        result.append(REVERSE_KEYWORDS[braille_kw])
                        i += len(braille_kw)
                        matched = True
                        break
                if not matched:
                    result.append('??KEYWORD??')
                continue

            # Number prefix
            if braille_line[i] == NUMBER_PREFIX:
                i += 1  # skip prefix
                while i < len(braille_line) and braille_line[i] in REVERSE_DIGITS:
                    result.append(REVERSE_DIGITS[braille_line[i]])
                    i += 1
                continue

            # Capital prefix
            if braille_line[i] == CAPITAL_PREFIX:
                i += 1
                if i < len(braille_line) and braille_line[i] in REVERSE_LETTERS:
                    result.append(REVERSE_LETTERS[braille_line[i]].upper())
                    i += 1
                continue

            # Underscore indicator
            if braille_line[i] == '⠸':
                result.append('_')
                i += 1
                continue

            # Quote
            if braille_line[i] == PUNCTUATION['"']:
                result.append('"')
                i += 1
                continue

            # Try multi-char operators (longest first)
            matched = False
            for braille_op in self._sorted_rev_operators:
                if braille_line[i:i + len(braille_op)] == braille_op:
                    result.append(REVERSE_OPERATORS[braille_op])
                    i += len(braille_op)
                    matched = True
                    break
            if matched:
                continue

            # Try punctuation (longest first)
            for braille_punc in self._sorted_rev_punctuation:
                if braille_line[i:i + len(braille_punc)] == braille_punc:
                    result.append(REVERSE_PUNCTUATION[braille_punc])
                    i += len(braille_punc)
                    matched = True
                    break
            if matched:
                continue

            # Single letter
            if braille_line[i] in REVERSE_LETTERS:
                result.append(REVERSE_LETTERS[braille_line[i]])
                i += 1
                continue

            # Unknown — skip
            result.append(f'[?{braille_line[i]}]')
            i += 1

        return ''.join(result)
