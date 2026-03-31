import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

const DEFAULT_CODE = `x = 10
y = 20
z = x + y * 2

if z > 30:
    print(z)
    z = z - 1
elif z == 30:
    print(0)
else:
    print(1)

while x > 0:
    x = x - 1

print(x)
print(z)`;

export default function CodeEditor({ value, onChange, highlightLine, errors }) {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorRef = useRef([]);

  function handleMount(editor, monaco) {
    editorRef.current = editor;
    monacoRef.current = monaco;

    monaco.editor.defineTheme('bcc-theme', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: '', foreground: 'ffffff' },
        { token: 'keyword', foreground: '79b8ff' },
        { token: 'string', foreground: 'a5d6ff' },
        { token: 'number', foreground: 'd2a8ff' },
        { token: 'comment', foreground: 'cccccc' },
      ],
      colors: {
        'editor.background': '#0d1117',
        'editor.lineHighlightBackground': '#161b22',
        'editorGutter.background': '#0d1117',
        'editor.selectionBackground': '#264f78',
        'editorInactiveSelectionBackground': '#264f7844',
      }
    });
    monaco.editor.setTheme('bcc-theme');
  }

  useEffect(() => {
    const ed = editorRef.current;
    if (!ed) return;
    if (highlightLine && highlightLine > 0) {
      decorRef.current = ed.deltaDecorations(decorRef.current, [{
        range: { startLineNumber: highlightLine, startColumn: 1, endLineNumber: highlightLine, endColumn: 1 },
        options: { isWholeLine: true, className: 'debug-line-hl', glyphMarginClassName: 'debug-glyph' },
      }]);
      ed.revealLineInCenter(highlightLine);
    } else {
      decorRef.current = ed.deltaDecorations(decorRef.current, []);
    }
  }, [highlightLine]);

  useEffect(() => {
    const m = monacoRef.current, ed = editorRef.current;
    if (!m || !ed) return;
    const model = ed.getModel();
    if (!model) return;
    if (errors?.length > 0) {
      m.editor.setModelMarkers(model, 'bcc', errors.filter(e => e.line > 0).map(e => ({
        severity: m.MarkerSeverity.Error, message: e.message,
        startLineNumber: e.line, startColumn: 1,
        endLineNumber: e.line, endColumn: model.getLineMaxColumn(e.line) || 1,
      })));
    } else {
      m.editor.setModelMarkers(model, 'bcc', []);
    }
  }, [errors]);

  return (
    <div className="code-editor-panel">
      <div className="panel-bar">
        <span className="panel-dot green" /><span className="panel-dot yellow" /><span className="panel-dot red" />
        <span className="panel-title">source.bcc</span>
        {highlightLine && <span className="badge badge-warn">Line {highlightLine}</span>}
      </div>
      <div className="editor-wrap">
        <Editor height="100%" defaultLanguage="python" theme="bcc-theme"
          value={value ?? DEFAULT_CODE} onChange={v => onChange(v || '')} onMount={handleMount}
          options={{
            fontSize: 14, fontFamily: "'JetBrains Mono', monospace", minimap: { enabled: false },
            lineNumbers: 'on', scrollBeyondLastLine: false, automaticLayout: true,
            tabSize: 4, wordWrap: 'on', padding: { top: 12 }, glyphMargin: true,
            renderLineHighlight: 'gutter',
          }}
        />
      </div>
    </div>
  );
}
export { DEFAULT_CODE };
