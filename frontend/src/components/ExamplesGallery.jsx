import React from 'react';
import { XIcon } from './Icons';

const VALID_EXAMPLES = [
  { name: 'Optimization Showcase', desc: 'Constant folding & dead code', code: 'a = 10 * 5 + 2\nb = 0\nif False:\n    print("unreachable")\nelse:\n    print(a)\n\n# Multiply by zero optimized away\nc = a * b \nprint(c)' },
  { name: 'Prime Checker', desc: 'Complex loops, conditions, scope', code: 'num = 29\nis_prime = True\ni = 2\nwhile i < num:\n    if num % i == 0:\n        is_prime = False\n    i = i + 1\n\nif is_prime:\n    print("Prime")\nelse:\n    print("Composite")' },
  { name: 'Fibonacci Sequence', desc: 'State tracking and reassignments', code: 'n = 10\na = 0\nb = 1\nwhile n > 0:\n    print(a)\n    temp = a + b\n    a = b\n    b = temp\n    n = n - 1' },
];

const ERROR_EXAMPLES = [
  { name: 'Lexical Error', desc: 'Invalid indentation levels', code: 'x = 10\nif x > 5:\n    print("ok")\n  print("bad indent")' },
  { name: 'Syntax Error', desc: 'Missing syntax tokens (colon, parens)', code: 'val = 10\nif val == 10\n    print "hello"' },
  { name: 'Semantic Error : Scope', desc: 'Undeclared variable reference', code: 'a = 10\nif a > 0:\n    b = 20\n\nprint(b)\nprint(c)' },
  { name: 'Semantic Error : Type', desc: 'Type mismatch in binary operation', code: 'msg = "Score: "\nval = 100\nprint(msg + val)' },
  { name: 'Runtime Error', desc: 'Division by zero during execution', code: 'total = 500\ntarget = 10\nwhile target >= 0:\n    print(total / target)\n    target = target - 5' }
];

export default function ExamplesGallery({ onSelect, onClose }) {
  const renderCard = (e, i) => (
    <div key={i} className="ex-card" onClick={() => { onSelect(e.code); onClose(); }}>
      <div className="ex-name">{e.name}</div>
      <div className="ex-desc">{e.desc}</div>
      <pre className="ex-preview">{e.code.split('\n').slice(0, 4).join('\n')}{e.code.split('\n').length > 4 ? '\n...' : ''}</pre>
    </div>
  );

  return (
    <div className="ex-overlay" onClick={onClose}>
      <div className="ex-modal" style={{ maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
        <div className="ex-header">
          <h2>Example Programs</h2>
          <button className="ex-close" onClick={onClose}><XIcon size={14} /></button>
        </div>
        <div className="ex-grid" style={{ display: 'block', padding: '16px 20px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--tx-2)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Pipeline Showcases</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: '10px', marginBottom: '24px' }}>
            {VALID_EXAMPLES.map(renderCard)}
          </div>

          <h3 style={{ fontSize: '13px', color: 'var(--tx-2)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Phase Error Demonstrations</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: '10px' }}>
            {ERROR_EXAMPLES.map(renderCard)}
          </div>
        </div>
      </div>
    </div>
  );
}
