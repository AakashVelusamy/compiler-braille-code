# BrailleCode Compiler — Step 1: Braille Mapping + Translator

## Project Structure

```
braillecode/
├── backend/
│   ├── compiler/
│   │   ├── __init__.py
│   │   └── engine/
│   │       ├── __init__.py
│   │       ├── braille_map.py    ← Braille ↔ English mapping table
│   │       └── translator.py     ← English ↔ Braille converter
│   └── tests/
│       ├── __init__.py
│       └── test_translator.py    ← Test suite
└── README.md
```

## Setup & Run

### Prerequisites
- Python 3.8+

### Run the tests

```bash
cd braillecode/backend
python -m tests.test_translator
```

This runs 12 tests covering:
- Mapping completeness (26 letters, 10 digits)
- Reverse mapping correctness
- No pattern collisions
- Simple assignments, keywords, operators
- Indentation handling
- Round-trip (English → Braille → English)
- Full multi-line program translation

### Quick interactive demo

```bash
cd braillecode/backend
python3 -c "
from compiler.engine.translator import Translator
t = Translator()

code = '''x = 10
if x > 5:
    print(x)
else:
    print(0)'''

braille = t.english_to_braille(code)
print('=== English Source ===')
print(code)
print()
print('=== Braille Output ===')
print(braille)
print()
print('=== Back to English ===')
print(t.braille_to_english(braille))
"
```

## What's in this step

| File | Purpose |
|------|---------|
| `braille_map.py` | Complete mapping table: 26 lowercase letters, 10 digits, 11 operators, 6 punctuation marks, 10 keywords, whitespace rules, and auto-generated reverse mappings |
| `translator.py` | `Translator` class with `english_to_braille()` and `braille_to_english()` methods. Handles keywords, identifiers, numbers, operators, string literals, and indentation |

## Next step
Lexer — takes the Braille string from the translator and produces a token stream.
