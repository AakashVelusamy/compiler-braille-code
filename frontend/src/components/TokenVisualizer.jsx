import React, { useState } from 'react';

const CAT = {
  PRINT:'kw',IF:'kw',ELSE:'kw',ELIF:'kw',WHILE:'kw',TRUE:'kw',FALSE:'kw',AND:'kw',OR:'kw',NOT:'kw',NONE:'kw',
  PLUS:'op',MINUS:'op',MULTIPLY:'op',DIVIDE:'op',MODULO:'op',ASSIGN:'op',EQUAL:'op',NOT_EQUAL:'op',
  LESS:'op',GREATER:'op',LESS_EQ:'op',GREATER_EQ:'op',
  INTEGER:'lit',STRING:'lit',
  IDENTIFIER:'id',
  LPAREN:'pn',RPAREN:'pn',COLON:'pn',COMMA:'pn',
  INDENT:'st',DEDENT:'st',NEWLINE:'st',EOF:'st',
};

const LEGEND = [
  { key: 'kw', label: 'Keyword', color: '#79c0ff' },
  { key: 'op', label: 'Operator', color: '#ffa198' },
  { key: 'lit', label: 'Literal', color: '#7ee787' },
  { key: 'id', label: 'Identifier', color: '#e3b341' },
  { key: 'pn', label: 'Punctuation', color: '#8b949e' },
  { key: 'st', label: 'Structure', color: '#6e7681' },
];

export default function TokenVisualizer({ tokens }) {
  const [view, setView] = useState('pills');

  if (!tokens?.length) return <div className="placeholder">No tokens</div>;

  const filtered = tokens.filter(t => t.type !== 'EOF');
  const lines = {};
  filtered.forEach(t => { if (!lines[t.line]) lines[t.line] = []; lines[t.line].push(t); });

  return (
    <div className="tok-viz">
      <div className="tok-top">
        <div className="tok-legend">
          {LEGEND.map(l => (
            <span key={l.key} className="tok-leg-item">
              <span className="tok-leg-dot" style={{ background: l.color }} />{l.label}
            </span>
          ))}
        </div>
        <div className="tok-view-toggle">
          <button className={view === 'pills' ? 'active' : ''} onClick={() => setView('pills')}>Pills</button>
          <button className={view === 'table' ? 'active' : ''} onClick={() => setView('table')}>Table</button>
        </div>
      </div>

      {view === 'pills' ? (
        <div className="tok-lines">
          {Object.entries(lines).map(([ln, toks]) => (
            <div key={ln} className="tok-line-grp">
              <span className="tok-ln">L{ln}</span>
              <div className="tok-pills">
                {toks.map((t, i) => {
                  const cat = CAT[t.type] || 'st';
                  return (
                    <span key={i} className={`tok-pill tok-${cat}`} title={`${t.type}: ${t.value}`}>
                      <span className="tok-pill-type">{t.type}</span>
                      {t.value && !['NEWLINE','INDENT','DEDENT'].includes(t.type) && (
                        <span className="tok-pill-val">{String(t.value)}</span>
                      )}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <table className="tok-table">
          <thead><tr><th>Line</th><th>Type</th><th>Value</th></tr></thead>
          <tbody>
            {filtered.map((t, i) => (
              <tr key={i} className={`tok-row-${CAT[t.type] || 'st'}`}>
                <td>{t.line}</td>
                <td className="tok-t-type">{t.type}</td>
                <td>{t.type === 'NEWLINE' ? '↵' : t.value || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
