# BrailleCode Compiler

**23XT67 — Compiler Design Lab**

A compiler that treats Braille as the native source code. Users write in English-like syntax, the system converts to Braille, then compiles and executes through a full pipeline: Translator → Lexer → Parser → Semantic Analyzer → Interpreter.

## Project Structure

```
braillecode/
├── backend/                     # Django + DRF
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                  # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── compiler/                # Django app
│   │   ├── apps.py
│   │   ├── urls.py              # /api/compile, /api/translate, /api/ast
│   │   ├── views.py             # DRF API views
│   │   ├── serializers.py
│   │   └── engine/              # Compiler pipeline (pure Python)
│   │       ├── braille_map.py
│   │       ├── translator.py
│   │       ├── tokens.py
│   │       ├── lexer.py
│   │       ├── ast_nodes.py
│   │       ├── parser.py
│   │       ├── analyzer.py
│   │       └── interpreter.py
│   └── tests/                   # 122 tests total
│       ├── test_translator.py
│       ├── test_lexer.py
│       ├── test_parser.py
│       ├── test_analyzer.py
│       └── test_interpreter.py
├── frontend/                    # React 18
│   ├── package.json
│   ├── public/index.html
│   └── src/
│       ├── index.js
│       ├── App.jsx
│       ├── App.css
│       ├── api/compilerApi.js
│       └── components/
│           ├── CodeEditor.jsx
│           ├── BrailleDisplay.jsx
│           └── OutputPanel.jsx
└── README.md
```

## Setup & Run

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm

### 1. Backend (Django)

```bash
cd braillecode/backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the Django server
python manage.py runserver
```

The API is at **http://localhost:8000/api/**

| Method | URL               | Description                        |
|--------|-------------------|------------------------------------|
| POST   | `/api/compile/`   | Full pipeline: compile + execute   |
| POST   | `/api/translate/` | English to Braille translation     |
| POST   | `/api/ast/`       | Returns AST JSON (no execution)    |

All endpoints accept: `{ "source": "your code here" }`

### 2. Frontend (React)

```bash
cd braillecode/frontend
npm install
npm start
```

Opens at **http://localhost:3000**, proxies API calls to Django on port 8000.

### Run All Tests (122 total)

```bash
cd braillecode/backend
python -m tests.test_translator
python -m tests.test_lexer
python -m tests.test_parser
python -m tests.test_analyzer
python -m tests.test_interpreter
```

### Quick API Test (no frontend)

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/compile/" `
  -ContentType "application/json" `
  -Body '{"source": "x = 10\nprint(x)"}'
```
