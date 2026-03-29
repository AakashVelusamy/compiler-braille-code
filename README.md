# BrailleCode Compiler

**23XT67 — Compiler Design Lab**
**23PT01 - Aakash Velusamy | 23PT11 - Harshil Bhavik Momaya**

A compiler that treats Braille as the native source code. Users write in English-like syntax, the system converts to Braille, then compiles and executes through a full pipeline.

## Features

### Core Compiler Pipeline
- **Translator** — Bidirectional English ↔ Braille (Unicode U+2800–U+283F) conversion
- **Lexer** — Tokenizes Braille input with indentation-based scoping (INDENT/DEDENT)
- **Parser** — Recursive descent parser with 7-level operator precedence → AST
- **Semantic Analyzer** — Symbol table, scope tracking, variable usage checks, type inference
- **Interpreter** — Tree-walk executor with division-by-zero protection and loop limits

### Frontend Features
- **Monaco Editor** — VS Code-quality code editor with Python syntax highlighting
- **Live Braille Preview** — Real-time Braille translation as you type (debounced 500ms)
- **AST Tree Visualizer** — Interactive collapsible tree, color-coded by node category
- **Token Stream Visualizer** — Colored pills grouped by line (keyword/operator/literal/identifier)
- **Step-by-Step Debugger** — Play/pause/step controls, variable watch, output tracking, line highlighting
- **Pipeline Timeline** — Visual stepper showing pass/fail status for each compiler phase
- **Error Highlighting** — Red squiggly markers in the editor on error lines
- **Example Programs Gallery** — 10 preloaded programs (FizzBuzz, Fibonacci, Factorial, etc.)
- **Export/Download** — Export source (.bcc), Braille (.brl), AST (.json), output, or full report

### API Endpoints
| Method | URL               | Description                        |
|--------|-------------------|------------------------------------|
| POST   | `/api/compile/`   | Full pipeline: compile + execute   |
| POST   | `/api/translate/` | English ↔ Braille translation      |
| POST   | `/api/ast/`       | Returns AST + tree (no execution)  |
| POST   | `/api/debug/`     | Step-by-step execution snapshots   |

## Project Structure

```
braillecode/
├── backend/                         # Django + DRF
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                      # Django settings, urls, wsgi
│   └── compiler/                    # Django app
│       ├── views.py                 # 4 API endpoints
│       ├── urls.py
│       ├── serializers.py
│       └── engine/                  # Compiler pipeline
│           ├── braille_map.py       # Unicode mapping table
│           ├── translator.py        # English ↔ Braille
│           ├── tokens.py            # Token type definitions
│           ├── lexer.py             # Braille → token stream
│           ├── ast_nodes.py         # AST node types + serializers
│           ├── parser.py            # Recursive descent parser
│           ├── analyzer.py          # Semantic analysis
│           ├── interpreter.py       # Tree-walk interpreter
│           └── debugger.py          # Step-by-step executor
├── frontend/                        # React 18
│   ├── package.json
│   ├── public/index.html
│   └── src/
│       ├── App.jsx                  # Main app with all features wired
│       ├── App.css                  # Complete dark theme styling
│       ├── api/compilerApi.js       # API client (compile, debug, translate)
│       └── components/
│           ├── CodeEditor.jsx       # Monaco with debug + error highlighting
│           ├── BrailleDisplay.jsx   # Live Braille preview panel
│           ├── OutputPanel.jsx      # Tabbed results (Output/Vars/Tokens/AST)
│           ├── ASTTreeVisualizer.jsx    # Interactive AST tree
│           ├── DebuggerPanel.jsx        # Step-by-step debugger with playback
│           ├── PipelineTimeline.jsx     # Compiler phase pass/fail stepper
│           ├── ExamplesGallery.jsx      # 10 example programs modal
│           └── ExportButtons.jsx        # Download .bcc/.brl/.json/report
└── README.md
```

## Setup & Run

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm

### 1. Backend (Django)

```bash
cd braillecode/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start server
python manage.py runserver
```

API available at **http://localhost:8000/api/**

### 2. Frontend (React)

```bash
cd braillecode/frontend
npm install
npm start
```

Opens at **http://localhost:3000**

### Run Tests (122 total)

```bash
cd braillecode/backend
python -m tests.test_translator      # 12 tests
python -m tests.test_lexer           # 18 tests
python -m tests.test_parser          # 23 tests
python -m tests.test_analyzer        # 26 tests
python -m tests.test_interpreter     # 43 tests
```

### Quick API Test (PowerShell)

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/compile/" `
  -ContentType "application/json" `
  -Body '{"source": "x = 10\nif x > 5:\n    print(x)\nelse:\n    print(0)"}'
```

## Language Reference

### Supported Features
- Variables: `x = 10`, `msg = "hello"`, `flag = True`
- Arithmetic: `+`, `-`, `*`, `/` (integer), `%`
- Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Boolean logic: `and`, `or`, `not`
- Control flow: `if`/`elif`/`else`, `while`
- Output: `print(expression)`
- Literals: integers, strings, `True`, `False`, `None`
- Scoping: Python-style 4-space indentation
