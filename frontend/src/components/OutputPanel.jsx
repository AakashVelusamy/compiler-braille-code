import React, { useState } from 'react';
import ASTTreeVisualizer from './ASTTreeVisualizer';
import TokenVisualizer from './TokenVisualizer';

const TABS = [
  { key: 'output', label: 'Output' },
  { key: 'vars', label: 'Variables' },
  { key: 'tokens', label: 'Tokens' },
  { key: 'tree', label: 'AST Tree' },
  { key: 'json', label: 'AST JSON' },
];

export default function OutputPanel({ result, loading }) {
  const [tab, setTab] = useState('output');

  return (
    <div className="output-panel">
      <div className="panel-bar">
        <span className="panel-title">Results</span>
        {result?.success === true && <span className="badge badge-ok">Passed</span>}
        {result?.success === false && <span className="badge badge-err">Error</span>}
      </div>
      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn ${tab === t.key ? 'on' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>
      <div className="out-body">
        {loading ? <div className="placeholder">Compiling...</div>
         : !result ? <div className="placeholder">Click Compile & Run to see results</div>
         : <>
            {tab === 'output' && <OutputTab r={result} />}
            {tab === 'vars' && <VarsTab r={result} />}
            {tab === 'tokens' && <TokenVisualizer tokens={result.tokens} />}
            {tab === 'tree' && <ASTTreeVisualizer astTree={result.ast_tree} />}
            {tab === 'json' && <pre className="ast-json">{JSON.stringify(result.ast, null, 2)}</pre>}
          </>
        }
      </div>
    </div>
  );
}

function OutputTab({ r }) {
  return (
    <div>
      {r.errors?.length > 0 && (
        <div className="err-box">
          {r.errors.map((e, i) => (
            <div key={i} className="err-line"><span className="err-phase">[{e.phase}]</span> {e.message}</div>
          ))}
        </div>
      )}
      {r.output?.length > 0 ? (
        <div className="prog-out">
          {r.output.map((l, i) => (
            <div key={i} className="out-line"><span className="out-num">{i+1}</span><span className="out-txt">{l}</span></div>
          ))}
        </div>
      ) : !r.errors?.length && <div className="placeholder">No output</div>}
      {r.analysis?.warnings?.length > 0 && (
        <div className="warn-box">
          {r.analysis.warnings.map((w, i) => <div key={i} className="warn-line">⚠ Line {w.line}: {w.message}</div>)}
        </div>
      )}
    </div>
  );
}

function VarsTab({ r }) {
  const entries = Object.entries(r.variables || {});
  if (!entries.length) return <div className="placeholder">No variables</div>;
  return (
    <table className="var-tbl">
      <thead><tr><th>Name</th><th>Value</th><th>Type</th></tr></thead>
      <tbody>
        {entries.map(([n, v]) => (
          <tr key={n}>
            <td className="v-name">{n}</td>
            <td className="v-val">{v === null ? 'None' : typeof v === 'boolean' ? String(v) : typeof v === 'string' ? `"${v}"` : String(v)}</td>
            <td className="v-type">{v === null ? 'none' : typeof v === 'boolean' ? 'bool' : typeof v === 'number' ? 'int' : typeof v === 'string' ? 'str' : typeof v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
