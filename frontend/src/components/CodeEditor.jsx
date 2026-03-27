import React from 'react';
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

export default function CodeEditor({ value, onChange }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-icon">✎</span>
        <h3>Source code</h3>
        <span className="panel-badge">English</span>
      </div>
      <div className="editor-wrapper">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={value ?? DEFAULT_CODE}
          onChange={(val) => onChange(val || '')}
          options={{
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            wordWrap: 'on',
            padding: { top: 12 },
          }}
        />
      </div>
    </div>
  );
}

export { DEFAULT_CODE };
