import React from 'react';

const EX = [
  { name: 'Hello World', desc: 'Basic print', code: 'print("hello world")' },
  { name: 'Arithmetic', desc: 'Operators + precedence', code: 'x = 10\ny = 20\nz = x + y * 2\nprint(z)\nprint(x - y)\nprint(z % 7)' },
  { name: 'If / Elif / Else', desc: 'Conditional branching', code: 'score = 75\nif score >= 90:\n    print("excellent")\nelif score >= 70:\n    print("good")\nelif score >= 50:\n    print("pass")\nelse:\n    print("fail")' },
  { name: 'Countdown', desc: 'While loop', code: 'x = 5\nwhile x > 0:\n    print(x)\n    x = x - 1\nprint("done")' },
  { name: 'Sum 1..N', desc: 'Accumulator', code: 'n = 10\ntotal = 0\ni = 1\nwhile i <= n:\n    total = total + i\n    i = i + 1\nprint(total)' },
  { name: 'FizzBuzz', desc: 'Modulo + branching', code: 'i = 1\nwhile i <= 15:\n    if i % 15 == 0:\n        print("fizzbuzz")\n    elif i % 3 == 0:\n        print("fizz")\n    elif i % 5 == 0:\n        print("buzz")\n    else:\n        print(i)\n    i = i + 1' },
  { name: 'Power of 2', desc: 'Compute 2^10', code: 'result = 1\ni = 0\nwhile i < 10:\n    result = result * 2\n    i = i + 1\nprint(result)' },
  { name: 'Fibonacci', desc: 'First 10 numbers', code: 'a = 0\nb = 1\ncount = 0\nwhile count < 10:\n    print(a)\n    temp = a + b\n    a = b\n    b = temp\n    count = count + 1' },
  { name: 'Factorial', desc: 'Compute 8!', code: 'n = 8\nfact = 1\ni = 1\nwhile i <= n:\n    fact = fact * i\n    i = i + 1\nprint(fact)' },
  { name: 'Boolean Logic', desc: 'and, or, not', code: 'a = True\nb = False\nc = not a or b\nd = a and not b\nprint(c)\nprint(d)\nx = 10\nresult = x > 5 and x < 20\nprint(result)' },
];

export default function ExamplesGallery({ onSelect, onClose }) {
  return (
    <div className="ex-overlay" onClick={onClose}>
      <div className="ex-modal" onClick={e => e.stopPropagation()}>
        <div className="ex-header">
          <h2>Example Programs</h2>
          <button className="ex-close" onClick={onClose}>×</button>
        </div>
        <div className="ex-grid">
          {EX.map((e, i) => (
            <div key={i} className="ex-card" onClick={() => { onSelect(e.code); onClose(); }}>
              <div className="ex-name">{e.name}</div>
              <div className="ex-desc">{e.desc}</div>
              <pre className="ex-preview">{e.code.split('\n').slice(0, 4).join('\n')}{e.code.split('\n').length > 4 ? '\n...' : ''}</pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
