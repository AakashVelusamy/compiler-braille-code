"""
BrailleCode API Views
======================

Four endpoints:
  POST /api/translate/  - English ↔ Braille conversion only
  POST /api/compile/    - Full 6-phase pipeline: translate → lex → parse → analyze → IR → optimize → codegen → execute
  POST /api/ast/        - Returns the AST as JSON (for visualization)
  POST /api/debug/      - Step-by-step execution with state snapshots
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .engine.translator import Translator, TranslationError
from .engine.lexer import Lexer, LexerError
from .engine.parser import Parser, ParseError
from .engine.analyzer import SemanticAnalyzer
from .engine.ir_generator import IRGenerator
from .engine.optimizer import Optimizer
from .engine.codegen import CodeGenerator
from .engine.interpreter import Interpreter
from .engine.debugger import Debugger
from .engine.ast_nodes import ast_to_dict, ast_to_tree


translator = Translator()


@api_view(['POST'])
def translate(request):
    """
    POST /api/translate/
    Body: { "source": "x = 10\\nprint(x)" }

    Returns the Braille representation and round-trip English.
    """
    source = request.data.get('source', '')
    if not source.strip():
        return Response(
            {'error': 'Source code is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        braille = translator.english_to_braille(source)
        back_to_english = translator.braille_to_english(braille)
        return Response({
            'braille': braille,
            'english': back_to_english,
        })
    except TranslationError as e:
        return Response(
            {'error': f'Translation error: {e}'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
def compile_and_run(request):
    """
    POST /api/compile/
    Body: { "source": "x = 10\\nprint(x)" }

    Full 6-phase pipeline:
      1. Lexical Analysis  (translate + tokenize)
      2. Syntax Analysis   (parse → AST)
      3. Semantic Analysis  (type checks, scope validation)
      4. Intermediate Code Generation (AST → Three-Address Code)
      5. Code Optimization  (constant folding, propagation, dead code, strength reduction)
      6. Code Generation    (TAC → pseudo-assembly)
    Then: interpret the AST for actual execution output.
    """
    source = request.data.get('source', '')
    if not source.strip():
        return Response(
            {'error': 'Source code is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = {
        'success': False,
        'braille': '',
        'output': [],
        'variables': {},
        'ast': {},
        'analysis': {},
        'errors': [],
        'tokens': [],
        'ir': {},
        'optimization': {},
        'codegen': {},
    }

    # ── Phase 1: Lexical Analysis ────────────────────────────────────────
    # Step 1a: Translate English → Braille
    try:
        braille = translator.english_to_braille(source)
        result['braille'] = braille
    except TranslationError as e:
        result['errors'].append({
            'phase': 'lexical',
            'message': str(e),
            'line': getattr(e, 'line', 0),
        })
        return Response(result)

    # Step 1b: Tokenize (Lexical Analysis / Scanner)
    try:
        lexer = Lexer(braille)
        tokens = lexer.tokenize()
        result['tokens'] = [
            {
                'type': tok.type.name,
                'value': tok.value if tok.value is not None else '',
                'line': tok.line,
            }
            for tok in tokens
        ]
    except LexerError as e:
        result['errors'].append({
            'phase': 'lexical',
            'message': str(e),
            'line': e.line,
        })
        return Response(result)

    # ── Phase 2: Syntax Analysis (Parser) ────────────────────────────────
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        result['ast'] = ast_to_dict(ast)
        result['ast_tree'] = ast_to_tree(ast)
    except ParseError as e:
        result['errors'].append({
            'phase': 'syntax',
            'message': str(e),
            'line': e.token.line,
        })
        return Response(result)

    # ── Phase 3: Semantic Analysis ───────────────────────────────────────
    analyzer = SemanticAnalyzer()
    analysis_ok = analyzer.analyze(ast)
    result['analysis'] = analyzer.get_report()

    if not analysis_ok:
        result['errors'].extend([
            {
                'phase': 'semantic',
                'message': str(e),
                'line': e.line,
            }
            for e in analyzer.errors
        ])
        return Response(result)

    # ── Phase 4: Intermediate Code Generation ────────────────────────────
    ir_gen = IRGenerator()
    ir_instructions = ir_gen.generate(ast)
    result['ir'] = {
        'text': ir_gen.to_text(),
        'instructions': ir_gen.to_list(),
        'instruction_count': len(ir_instructions),
    }

    # ── Phase 5: Code Optimization ───────────────────────────────────────
    optimizer = Optimizer(ir_instructions)
    optimized = optimizer.optimize()
    result['optimization'] = optimizer.get_report()

    # ── Phase 6: Code Generation ─────────────────────────────────────────
    codegen = CodeGenerator(optimized)
    codegen.generate()
    result['codegen'] = codegen.get_report()

    # ── Execute (via tree-walk interpreter for actual output) ─────────────
    interp = Interpreter()
    exec_result = interp.execute(ast)

    result['success'] = exec_result['success']
    result['output'] = exec_result['output']
    result['variables'] = {
        k: _serialize_value(v) for k, v in exec_result['variables'].items()
    }

    if exec_result['errors']:
        result['errors'].extend([
            {
                'phase': 'runtime',
                'message': e['message'],
                'line': e['line'],
            }
            for e in exec_result['errors']
        ])

    return Response(result)


@api_view(['POST'])
def get_ast(request):
    """
    POST /api/ast/
    Body: { "source": "x = 10\\nprint(x)" }

    Returns only the AST (for visualization), without executing.
    """
    source = request.data.get('source', '')
    if not source.strip():
        return Response(
            {'error': 'Source code is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        braille = translator.english_to_braille(source)
        tokens = Lexer(braille).tokenize()
        ast = Parser(tokens).parse()
        return Response({
            'ast': ast_to_dict(ast),
            'ast_tree': ast_to_tree(ast),
            'braille': braille,
        })
    except (TranslationError, LexerError, ParseError) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


def _serialize_value(value):
    """Convert Python runtime values to JSON-safe representations."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


@api_view(['POST'])
def debug(request):
    """
    POST /api/debug/
    Body: { "source": "x = 10\\nprint(x)" }

    Executes the program step by step, returning a list of snapshots.
    Each step contains: line number, statement type, description,
    variable states, output, branch taken, loop iteration.
    """
    source = request.data.get('source', '')
    if not source.strip():
        return Response(
            {'error': 'Source code is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Run through translation → lexing → parsing → analysis first
    try:
        braille = translator.english_to_braille(source)
        tokens = Lexer(braille).tokenize()
        ast = Parser(tokens).parse()
    except (TranslationError, LexerError, ParseError) as e:
        return Response(
            {'error': str(e), 'steps': [], 'success': False},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Semantic check
    analyzer = SemanticAnalyzer()
    if not analyzer.analyze(ast):
        return Response({
            'error': 'Semantic errors found',
            'semantic_errors': [
                {'message': str(e), 'line': e.line} for e in analyzer.errors
            ],
            'steps': [],
            'success': False,
        })

    # Debug execution
    debugger = Debugger()
    result = debugger.run(ast)

    return Response(result)
