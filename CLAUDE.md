# CLAUDE.md - BrailleCode Compiler Project Context

## Project Overview

**BrailleCode Compiler** is a full-stack compiler that treats six-dot Braille Unicode patterns (U+2800–U+283F) as the native source code. Users write programs in an English-like Python subset, the system translates it to Braille, then compiles and executes through a classical compiler pipeline. Built for the **23XT67 Compiler Design Lab** course.

**Team**: 23PT01 - Aakash Velusamy | 23PT11 - Harshil Bhavik Momaya

**Tech stack**: Django 4.2 + Django REST Framework (backend), React 18 + Monaco Editor (frontend), pure Python compiler engine (no parser generators).

---

## Architecture

```
English source code
       │
       ▼
┌─────────────────┐
│   Translator    │  English ↔ Braille (Unicode mapping table)
│  translator.py  │  Bidirectional: english_to_braille() / braille_to_english()
└────────┬────────┘
         │  Braille string (⠭⠀⠶⠀⠼⠁⠚)
         ▼
┌─────────────────┐
│     Lexer       │  Braille → Token stream
│    lexer.py     │  Handles INDENT/DEDENT, keywords, numbers, strings
└────────┬────────┘
         │  [Token(IDENTIFIER,'x'), Token(ASSIGN,'='), Token(INTEGER,10), ...]
         ▼
┌─────────────────┐
│     Parser      │  Recursive descent, 7-level operator precedence
│    parser.py    │  Produces Abstract Syntax Tree
└────────┬────────┘
         │  Program(body=[Assign(name='x', value=Number(10)), ...])
         ▼
┌─────────────────┐
│    Analyzer     │  Symbol table, scope tracking, type inference
│   analyzer.py   │  Catches undeclared variables, type mismatches
└────────┬────────┘
         │  Validated AST (unchanged structure, errors/warnings collected)
         ▼
┌─────────────────┐
│   Interpreter   │  Tree-walk executor
│ interpreter.py  │  Evaluates AST, collects print output
└────────┬────────┘
         │
         ▼
    Program output: ['50', '49']
    Final variables: {x: 0, y: 20, z: 49}
```

### Alternative path: Debugger

The `debugger.py` module mirrors the interpreter but records a `DebugStep` snapshot after every statement execution, capturing line number, statement type, variable states, output, branch taken, and loop iteration count. Used by the `/api/debug/` endpoint.

---

## File Structure

```
braillecode/
├── backend/
│   ├── manage.py                          # Django entry point
│   ├── requirements.txt                   # django, djangorestframework, django-cors-headers
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                    # Django config (no database, CORS enabled)
│   │   ├── urls.py                        # Root URL: includes compiler.urls at /api/
│   │   └── wsgi.py
│   ├── compiler/                          # Django app
│   │   ├── __init__.py
│   │   ├── apps.py                        # AppConfig
│   │   ├── urls.py                        # 4 endpoints: compile, translate, ast, debug
│   │   ├── views.py                       # DRF @api_view functions
│   │   ├── serializers.py                 # Request/response serializers
│   │   └── engine/                        # Pure Python compiler pipeline
│   │       ├── __init__.py                # Re-exports all public classes
│   │       ├── braille_map.py             # Unicode mapping tables + reverse maps
│   │       ├── translator.py              # Translator class (English ↔ Braille)
│   │       ├── tokens.py                  # TokenType enum (30 types) + Token dataclass
│   │       ├── lexer.py                   # Lexer class → token stream
│   │       ├── ast_nodes.py               # 13 AST node dataclasses + ast_to_dict + ast_to_tree
│   │       ├── parser.py                  # Parser class (recursive descent)
│   │       ├── analyzer.py                # SemanticAnalyzer + SymbolTable + Symbol
│   │       ├── ir_generator.py            # Generates Three-Address Code (TAC) from AST
│   │       ├── optimizer.py               # Optimizes IR (constant folding, dead code elimination)
│   │       ├── codegen.py                 # Generates Target Machine Assembly from optimized IR
│   │       ├── interpreter.py             # Interpreter + Environment
│   │       └── debugger.py                # Debugger + DebugStep (step-by-step executor)
│   └── tests/                             # 122+ tests total
│       ├── __init__.py
│       ├── test_translator.py             # 12 tests
│       ├── test_lexer.py                  # 18 tests
│       ├── test_parser.py                 # 23 tests
│       ├── test_analyzer.py               # 26 tests
│       ├── test_ir_generator.py           # IR Generation tests
│       ├── test_optimizer.py              # Optimizations passes tests
│       ├── test_codegen.py                # Target machine code generation tests
│       └── test_interpreter.py            # 43 tests
├── frontend/
│   ├── package.json                       # React 18, @monaco-editor/react
│   ├── public/index.html
│   └── src/
│       ├── index.js                       # React entry point
│       ├── App.jsx                        # Main app, all state management
│       ├── App.css                        # Complete UI theme (indigo/slate palette)
│       ├── api/
│       │   └── compilerApi.js             # axios client: compileCode, translateCode, debugCode, getAST
│       └── components/
│           ├── CodeEditor.jsx             # Monaco Editor + debug line highlighting + error markers
│           ├── BrailleDisplay.jsx         # Braille Unicode panel + live preview badge
│           ├── OutputPanel.jsx            # Multi-tab routing for phase visualizers
│           ├── TokenVisualizer.jsx        # Colored pills (6 categories) + table view toggle
│           ├── ASTTreeVisualizer.jsx      # Interactive collapsible tree (3 color categories)
│           ├── SemanticVisualizer.jsx     # Symbols table, errors and warnings banner
│           ├── IRVisualizer.jsx           # Intermediate representation (TAC) visualizer
│           ├── OptimizationVisualizer.jsx # Before/After diffs for optimizations
│           ├── CodeGenVisualizer.jsx      # Assembly output and memory mapping
│           ├── DebuggerPanel.jsx          # Play/pause/step controls + variable watch + timeline
│           ├── PipelineTimeline.jsx       # Pipeline stepper (Translate→Lex→Parse→Analyze→Execute)
│           ├── ExamplesGallery.jsx        # Modal with sample programs
│           ├── ExportButtons.jsx          # Download files and full report
│           └── Icons.jsx                  # Lucide React icons wrapper
└── README.md
```

---

## Backend Implementation Details

### braille_map.py - Mapping Table

Contains all mappings between English characters and Braille Unicode:

- **26 lowercase letters**: Standard Grade 1 Braille (a=⠁ through z=⠵)
- **Uppercase**: Capital prefix ⠠ + lowercase letter pattern
- **10 digits**: Number prefix ⠼ + a-j Braille pattern (0=⠚, 1=⠁, ..., 9=⠊)
- **11 operators**: +⠬ -⠤ *⠡ /⠌ %⠒⠏ =⠶ ==⠶⠶ !=⠌⠶ <⠣ >⠜ <=⠣⠶ >=⠜⠶
- **6 punctuation**: (⠐⠣ )⠐⠜ :⠒ ,⠂ "⠦ '⠄
- **10 keywords**: print, if, else, elif, while, True, False, and, or, not, None - each preceded by keyword prefix ⠈⠼
- **Whitespace**: Space=⠀ (U+2800), Newline=⠿ (U+283F, all 6 dots), Indent=⠀⠀ (double space)
- **Auto-generated reverse maps**: REVERSE_LETTERS, REVERSE_DIGITS, REVERSE_OPERATORS, REVERSE_PUNCTUATION, REVERSE_KEYWORDS

**Key design decision**: The newline delimiter was changed from triple-space (⠀⠀⠀) to ⠿ (U+283F) because triple-space overlapped with indent patterns (double-space) and caused nested indentation to break.

### translator.py - English ↔ Braille Converter

`Translator` class with two main methods:

- `english_to_braille(source)`: Splits into lines, counts leading spaces (4 spaces = 1 indent level), tokenizes each line recognizing keywords (longest-first matching), numbers (consecutive digits with number prefix), identifiers (letter by letter, capitals get prefix, underscores get ⠸ indicator), operators (2-char first for greedy matching), string literals (between " marks), and punctuation.
- `braille_to_english(braille)`: Reverse process, splits by ⠿ newline delimiter, counts indent units, then matches patterns in reverse maps (keywords, numbers, capitals, operators, punctuation, letters) longest-first.

### tokens.py - Token Types

`TokenType` enum with 30 values across 6 categories:

- Literals: INTEGER, STRING
- Keywords: PRINT, IF, ELSE, ELIF, WHILE, TRUE, FALSE, AND, OR, NOT, NONE
- Operators: PLUS, MINUS, MULTIPLY, DIVIDE, MODULO, ASSIGN, EQUAL, NOT_EQUAL, LESS, GREATER, LESS_EQ, GREATER_EQ
- Punctuation: LPAREN, RPAREN, COLON, COMMA
- Structure: INDENT, DEDENT, NEWLINE
- Special: EOF

`Token` dataclass carries `type`, `value`, and `line` (1-indexed).

`KEYWORD_TOKEN_MAP` dict maps keyword name strings to their TokenType.

### lexer.py - Tokenizer

`Lexer` class takes a Braille string and produces a `List[Token]`:

1. Splits input by ⠿ (BRAILLE_NEWLINE)
2. For each line, counts leading BRAILLE_INDENT units (⠀⠀)
3. Compares indent level to `indent_stack` (initialized to [0]):
   - Level increased → push to stack, emit INDENT token
   - Level decreased → pop stack entries, emit DEDENT for each
   - Mismatched level → LexerError
4. Tokenizes line content: keyword prefix → keyword lookup, number prefix → digit collection, quote marks → string literal collection, operators (longest-first greedy), punctuation, capital prefix → uppercase identifier char, underscore indicator, Braille letters → identifier
5. Emits NEWLINE at end of each logical line
6. At EOF: pops remaining indent levels, emits DEDENTs, then EOF token

`_read_identifier()` helper collects consecutive Braille letters, capital-prefixed letters, underscore indicators, and number-prefixed digits to form a complete identifier name.

### ast_nodes.py - AST Node Types

13 node dataclasses, all inheriting from `ASTNode(line: int)`:

**Statements:**

- `Program(body: List[ASTNode])` - root node
- `Assign(name: str, value: ASTNode)` - variable assignment
- `Print(value: ASTNode)` - print statement
- `If(condition, body, elif_clauses: List[tuple], else_body)` - if/elif/else
- `While(condition, body)` - while loop

**Expressions:**

- `BinOp(left, op: str, right)` - binary arithmetic: +, -, *, /, %
- `UnaryOp(op: str, operand)` - unary: -, not
- `Compare(left, op: str, right)` - comparisons: ==, !=, <, >, <=, >=
- `BoolOp(left, op: str, right)` - boolean: and, or

**Literals:**

- `Number(value: int)`, `String(value: str)`, `Boolean(value: bool)`, `NoneValue()`
- `Identifier(name: str)` - variable reference

**Serialization:**

- `ast_to_dict(node)` - nested dict for JSON (used by /api/compile/ and /api/ast/)
- `ast_to_tree(node)` - uniform `{id, label, type, category, children, line}` structure for the frontend tree visualizer. Categories: 'program', 'statement', 'operator', 'literal'
- `print_ast(node, indent)` - pretty-print to stdout for debugging

### parser.py - Recursive Descent Parser

`Parser` class consumes a token list and produces a `Program` AST.

**Grammar** (7-level operator precedence, lowest to highest):

```
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
atom        → INTEGER | STRING | TRUE | FALSE | NONE | IDENTIFIER | LPAREN expression RPAREN
```

Helper methods: `_current()`, `_peek(offset)`, `_advance()`, `_expect(type)`, `_match(*types)`, `_skip_newlines()`.

`_parse_block()` expects INDENT, collects statements until DEDENT or EOF, expects DEDENT. Raises ParseError on empty blocks.

### analyzer.py - Semantic Analyzer

**SymbolTable** class: stack of dicts (`List[Dict[str, Symbol]]`), starting with one global scope.

- `push_scope()` / `pop_scope()` - enter/exit block scopes (if/while bodies)
- `declare(name, line, inferred_type)` - add to current scope
- `lookup(name)` - search innermost to outermost, returns `Symbol` or None
- `is_declared(name)` - bool check across all scopes

**Symbol** dataclass: `name`, `declared_line`, `scope_depth`, `inferred_type` ('int'|'str'|'bool'|'none'|'unknown')

**SemanticAnalyzer** class walks the AST:

- `_analyze_assign()`: analyze RHS expression first, infer type, then declare variable
- `_analyze_if()` / `_analyze_while()`: push scope for each block, pop on exit
- `_analyze_expression()`: recursively check all Identifier references are declared
- `_infer_type()`: best-effort static inference (int+int→int, str+str→str for +, compare→bool, etc.)
- `_check_binop_types()`: warns on incompatible types (str + int)

Produces: `errors` (hard, block execution) and `warnings` (soft, don't block).
`get_report()` returns `{success, errors, warnings, symbols}` for the API.

### interpreter.py - Tree-Walk Interpreter

**Environment** class: like SymbolTable but stores actual runtime values.

- `set(name, value)`: searches enclosing scopes first (so `x = x - 1` in a while loop modifies the outer `x`), creates in current scope if not found
- `get(name)`: searches innermost to outermost, raises KeyError

**Interpreter** class:

- `_exec_assign()`: evaluate RHS, store in environment
- `_exec_print()`: evaluate expression, append `_to_display_string(value)` to `self.output` list
- `_exec_if()`: evaluate condition, execute matching branch in new scope
- `_exec_while()`: loop with `MAX_ITERATIONS = 10000` safety limit, new scope per iteration
- `_eval_binop()`: handles + for both int addition and string concatenation, / uses integer division (//)
- `_eval_boolop()`: short-circuit evaluation (and returns left if falsy, or returns left if truthy)
- `_is_truthy()`: Python-compatible: None/False/0/"" are falsy

Returns `{output: List[str], variables: dict, errors: List[dict], success: bool}`

### debugger.py - Step-by-Step Executor

Mirrors the interpreter but records a `DebugStep` after every statement:

**DebugStep** dataclass: `step_number`, `line`, `statement_type`, `description` (human-readable like "x = 5" or "while True → True (iteration 3)"), `variables` (full snapshot with type info), `output_line`, `total_output`, `branch_taken` ('if'|'elif'|'else'|''), `loop_iteration`, `event` ('assign'|'print'|'branch'|'loop_start'|'loop_end'|'error'), `error`

Safety limits: `MAX_STEPS = 500`, `MAX_ITERATIONS = 10000`

### views.py - API Endpoints

4 DRF function-based views:

1. `POST /api/translate/` - `{source}` → `{braille, english}` (round-trip)
2. `POST /api/compile/` - Full pipeline: translate → lex → parse → analyze → execute → `{success, braille, output, variables, ast, ast_tree, analysis, errors, tokens}`
   - Errors include `phase` field ('translation'|'lexer'|'parser'|'semantic'|'runtime')
   - Pipeline short-circuits on first error phase
3. `POST /api/ast/` - `{source}` → `{ast, ast_tree, braille}` (no execution)
4. `POST /api/debug/` - `{source}` → `{steps, total_steps, final_output, final_variables, success}`

Django settings: no database (stateless compiler), CORS allow all origins, JSON-only renderer/parser.

---

## Frontend Implementation Details

### UI Design - Indigo/Slate Dark Theme

Not a generic gray dark theme. Custom palette:

- Base: `#0b0e14` (near-black with blue undertone)
- Surface: `#10141c`, Raised: `#161b27`, Hover: `#1c2333`
- Text: primary `#e8eaf0`, secondary `#9ca3b4`, muted `#636d83`
- Accent: `#6c8cff` (periwinkle blue) with glow effects (`box-shadow`, `drop-shadow`)
- Semantic: green `#4ade80`, red `#f87171`, amber `#fbbf24`, purple `#c084fc`, teal `#2dd4bf`

Key visual distinctions:

- Header has gradient fade, not flat bar
- Compile button has blue glow shadow
- Debug button uses translucent amber
- Braille text glows with accent color drop-shadow
- Code editor has macOS-style traffic light dots
- Pipeline timeline sits centered in the header
- Examples gallery cards have hover glow effect
- All badges use translucent colored backgrounds

### App.jsx - State Management

All state lives in App.jsx (no Redux/Context needed for this scale):

- `source` - editor content
- `result` - compilation result from /api/compile/
- `braille` - compiled Braille output
- `loading` - compile in progress
- `debugMode`, `debugSteps`, `debugLoading`, `activeDebugLine` - debugger state
- `showExamples` - examples modal visibility
- `liveBraille`, `isLive` - live preview state

**Live Braille preview**: `useEffect` watches `source`, debounces 500ms, calls `/api/translate/`, updates `liveBraille`. The `isLive` flag shows a pulsing green "LIVE" badge. After compilation, compiled Braille takes priority.

### Component Details

**CodeEditor.jsx**: Monaco Editor wrapper.

- `onMount` stores editor and monaco refs
- `useEffect` for `highlightLine`: applies `deltaDecorations` with yellow background + glyph marker, scrolls to line
- `useEffect` for `errors`: sets `monaco.editor.setModelMarkers` with red squiggly underlines
- Options: JetBrains Mono font, 14px, no minimap, glyph margin enabled, Python language mode

**BrailleDisplay.jsx**: Shows Braille Unicode with `letter-spacing: 3px` and accent color glow. Displays "LIVE" pulsing badge during real-time preview.

**OutputPanel.jsx**: 5 tabs managed by local state.

- Output tab: error box (red), program output lines (green, numbered), warnings (amber)
- Variables tab: table with name (accent blue), value (mono), type (italic gray)
- Tokens tab: delegates to TokenVisualizer component
- AST Tree tab: delegates to ASTTreeVisualizer component
- AST JSON tab: formatted JSON in monospace

**TokenVisualizer.jsx**: Two views toggleable via pills/table buttons.

- Pills view: tokens grouped by source line, each as a colored rounded pill. 6 color categories: keyword (blue), operator (red), literal (green), identifier (amber), punctuation (gray), structure (dark gray). Legend at top.
- Table view: traditional line/type/value table with colored type column.

**ASTTreeVisualizer.jsx**: Recursive `Node` component.

- 3 color categories: statement (dark blue), operator (dark purple), literal (dark green) - each with matching border and text colors
- Nodes auto-collapse at depth > 3
- Click to expand/collapse, hover highlights all nodes on same source line
- Shows: expand arrow, label (mono), type badge, line number
- Vertical connector lines on the left edge of children groups

**DebuggerPanel.jsx**: Full playback UI.

- Controls: ⏮ ⏪ ▶/⏸ ⏩ ⏭ + step counter + speed dropdown (0.5x/1x/2x/4x)
- Progress bar: amber fill, width proportional to current step
- Detail panel: event icon (colored), description, variable chips, cumulative output pills (latest highlighted)
- Timeline: scrollable list of all steps, active step has amber left border, past steps dimmed, click to jump
- Auto-play via `setInterval`, auto-scroll to active step

**PipelineTimeline.jsx**: 5-phase horizontal stepper.

- Phases: Translate (⠃), Lex (⚡), Parse (🌳), Analyze (🔎), Execute (▶)
- States: ok (green + ✓), fail (red + ✗), skip (grayed out), running (pulsing), idle
- Failure detection: reads first error's `phase` field, phases before it are ok, the phase is fail, phases after are skip
- Connected by → arrows (dimmed after failure)

**ExamplesGallery.jsx**: Modal overlay with blur backdrop.

- 10 programs: Hello World, Arithmetic, If/Elif/Else, Countdown, Sum 1..N, FizzBuzz, Power of 2, Fibonacci, Factorial, Boolean Logic
- Each card shows name, description, 4-line code preview
- Click loads into editor, closes modal

**ExportButtons.jsx**: Horizontal bar with download buttons.

- `.bcc` - source code file
- `.brl` - Braille Unicode file (UTF-8)
- `AST` - ast.json
- `Output` - output.txt
- `Full report` - compilation_report.json containing source, braille, ast, ast_tree, tokens, output, variables, analysis, errors
- Uses Blob + createObjectURL + programmatic anchor click

---

## Key Design Decisions

1. **No parser generators (ANTLR/PLY)**: Hand-written recursive descent parser - this is a compiler design lab, writing the parser by hand is the point. The grammar is small enough that recursive descent is clean.
2. **Python for the compiler engine**: Fitting since the language being compiled is Python-like. Keeps the codebase uniform and easy to understand for an academic project.
3. **Newline delimiter changed from ⠀⠀⠀ to ⠿**: Triple Braille space overlapped with indent patterns (double Braille space). Using ⠿ (U+283F, all 6 dots raised) as an unambiguous line separator fixed nested indentation.
4. **Integer division only**: Division uses `//` (floor division) to avoid floating-point complexity. The language only has an INTEGER type, no floats.
5. **Scoping model**: Inner scopes can read AND write outer variables (Environment.set searches enclosing scopes first). This allows `x = x - 1` inside a while loop to modify the outer x. The semantic analyzer tracks declarations per scope but the interpreter allows cross-scope writes.
6. **No database**: The compiler is entirely stateless. Django's DATABASES setting is empty. Each API request is self-contained.
7. **Debugger as separate module**: Rather than adding debug hooks to the interpreter, the debugger is a parallel implementation that records snapshots. This avoids cluttering the interpreter with debug logic and keeps both independently testable.
8. **Token categorization for UI**: The frontend maps all 30 token types to 6 visual categories (keyword/operator/literal/identifier/punctuation/structure) for consistent color coding across the token visualizer and other components.

---

## Test Coverage

122 tests across 5 test files, all runnable without pytest:

```bash
cd braillecode/backend
python -m tests.test_translator      # 12 tests
python -m tests.test_lexer           # 18 tests
python -m tests.test_parser          # 23 tests
python -m tests.test_analyzer        # 26 tests
python -m tests.test_interpreter     # 43 tests
```

**test_translator** (12): mapping completeness, reverse map correctness, no collisions, simple assignment, keywords, if-statement, indentation, round-trip (English→Braille→English), while loop, arithmetic, get_full_mapping, multi-line program.

**test_lexer** (18): simple assignment, arithmetic, all 6 comparison operators, all 11 keywords, string literals, parentheses, single indent, indent+dedent, nested indent (2 levels), multi-line program, while loop, underscore identifiers, line numbers, EOF, modulo, divide, boolean operators, comma.

**test_parser** (23): simple assignment, string/boolean/none/variable assignment, arithmetic precedence (2+3*4=14), parenthesized override ((2+3)*4=20), unary minus, comparisons (all 6), boolean and/or precedence, not operator, print statement, print expression, if, if/else, if/elif/else, while loop, nested if, modulo/divide precedence, complex multi-statement program, ast_to_dict JSON, line numbers.

**test_analyzer** (26): 4 symbol table unit tests (declare/lookup, nested scopes, shadowing, depth tracking) + 11 valid program tests + 6 error detection tests (undeclared variable, undeclared in expression/condition/while, scope isolation, multiple undeclared) + 3 warning tests (type mismatch, no false warnings) + 2 report tests.

**test_interpreter** (43): 5 assignment types + 11 arithmetic (add/sub/mul/div/mod/precedence/parens/unary/complex/string concat) + 7 print (int/string/var/expression/bool/none/multiple) + 8 comparisons + 4 boolean (and/or/not/short-circuit) + 5 control flow (if true/false, if/else, if/elif/else, nested if) + 4 while (countdown/no-execute/single/accumulator) + 4 runtime errors (div-by-zero, mod-by-zero, type error, undefined var) + 3 complex programs (fizzbuzz, full pipeline, power of 2).

---

## API Reference

### POST /api/compile/

```json
// Request
{ "source": "x = 10\nprint(x)" }

// Response
{
  "success": true,
  "braille": "⠭⠀⠶⠀⠼⠁⠚⠿⠈⠼⠏⠗⠊⠝⠞⠐⠣⠭⠐⠜",
  "output": ["10"],
  "variables": { "x": 10 },
  "ast": { "type": "Program", "body": [...] },
  "ast_tree": { "id": "n1", "label": "Program", "type": "Program", "category": "program", "children": [...] },
  "analysis": { "success": true, "errors": [], "warnings": [], "symbols": [...] },
  "errors": [],
  "tokens": [
    { "type": "IDENTIFIER", "value": "x", "line": 1 },
    { "type": "ASSIGN", "value": "=", "line": 1 },
    ...
  ]
}
```

### POST /api/debug/

```json
// Request
{ "source": "x = 5\nwhile x > 0:\n    print(x)\n    x = x - 1" }

// Response
{
  "steps": [
    {
      "step_number": 1, "line": 1, "statement_type": "Assign",
      "description": "x = 5", "event": "assign",
      "variables": { "x": { "value": 5, "type": "int", "display": "5" } },
      "output_line": "", "total_output": [],
      "branch_taken": "", "loop_iteration": 0, "error": ""
    },
    ...
  ],
  "total_steps": 17,
  "final_output": ["5", "4", "3", "2", "1"],
  "final_variables": { "x": 0 },
  "success": true
}
```

### POST /api/translate/

```json
// Request
{ "source": "x = 10" }
// Response
{ "braille": "⠭⠀⠶⠀⠼⠁⠚", "english": "x = 10" }
```

### POST /api/ast/

```json
// Request
{ "source": "x = 10" }
// Response
{ "ast": {...}, "ast_tree": {...}, "braille": "..." }
```

---

## Language Reference

### Supported Syntax

```
# Variables
x = 10
name = "hello"
flag = True
empty = None

# Arithmetic (integer only, / is floor division)
result = (a + b) * c - d / e % f

# Comparisons
x == y    x != y    x < y    x > y    x <= y    x >= y

# Boolean logic (short-circuit)
a and b    a or b    not a

# Control flow (4-space indentation)
if condition:
    ...
elif condition:
    ...
else:
    ...

while condition:
    ...

# Output
print(expression)
```

### Not Supported

Functions, lists, floats, for loops, string indexing, imports, classes, input().

---

## Setup & Run

```bash
# Terminal 1 - Backend
cd backend
python -m venv venv
venv\Scripts\activate   
pip install -r requirements.txt
python manage.py runserver     # → http://localhost:8000/api/

# Terminal 2 - Frontend
cd braillecode/frontend
npm install
npm start                    # → http://localhost:3000

# Run all tests
cd braillecode/backend
python -m tests.test_translator
python -m tests.test_lexer
python -m tests.test_parser
python -m tests.test_analyzer
python -m tests.test_interpreter
```
