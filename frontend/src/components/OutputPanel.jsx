import React, { useState } from 'react';
import ASTTreeVisualizer from './ASTTreeVisualizer';
import TokenVisualizer from './TokenVisualizer';
import SemanticVisualizer from './SemanticVisualizer';
import IRVisualizer from './IRVisualizer';
import OptimizationVisualizer from './OptimizationVisualizer';
import CodeGenVisualizer from './CodeGenVisualizer';
import { TerminalIcon, ZapIcon, TreeIcon, SearchIcon, CodeIcon, CogIcon, CpuIcon, AlertIcon } from './Icons';

const TABS = [
  { key: 'output', label: 'Output', phase: null, Icon: TerminalIcon },
  { key: 'tokens', label: 'Lexical Analysis', phase: 'lexical', Icon: ZapIcon },
  { key: 'tree', label: 'Syntax Analysis', phase: 'syntax', Icon: TreeIcon },
  { key: 'sem', label: 'Semantic Analysis', phase: 'semantic', Icon: SearchIcon },
  { key: 'ir', label: 'Intermediate Code Generation', phase: 'ir', Icon: CodeIcon },
  { key: 'opt', label: 'Code Optimization', phase: 'opt', Icon: CogIcon },
  { key: 'codegen', label: 'Code Generation', phase: 'codegen', Icon: CpuIcon },
];

export default function OutputPanel({ result, loading }) {
  const [tab, setTab] = useState('output');

  return (
    <div className="output-panel">
      <div className="panel-bar">
        <span className="panel-title">Results</span>
        <div className="tab-bar-inline">
          {TABS.map(t => (
            <button key={t.key} className={`tab-btn ${tab === t.key ? 'on' : ''}`} onClick={() => setTab(t.key)}>
              <t.Icon size={12} className="tab-icon" />
              {t.label}
            </button>
          ))}
        </div>
        {result?.success === true && <span className="badge badge-ok">Passed</span>}
        {result?.success === false && <span className="badge badge-err">Error</span>}
      </div>
      <div className="out-body">
        {loading ? <div className="placeholder">Compiling...</div>
          : !result ? <div className="placeholder"></div>
            : <>
              {tab === 'output' && <OutputTab r={result} />}
              {tab === 'tokens' && <LexicalTab r={result} />}
              {tab === 'tree' && <SyntaxTab r={result} />}
              {tab === 'sem' && <SemTab r={result} />}
              {tab === 'ir' && <IRTab r={result} />}
              {tab === 'opt' && <OptTab r={result} />}
              {tab === 'codegen' && <CodeGenTab r={result} />}
            </>
        }
      </div>
    </div>
  );
}

/* ─── Output Tab ──────────────────────────────────────────────────────────── */
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
            <div key={i} className="out-line"><span className="out-num">{i + 1}</span><span className="out-txt">{l}</span></div>
          ))}
        </div>
      ) : !r.errors?.length && <div className="placeholder">No output</div>}
      {r.analysis?.warnings?.length > 0 && (
        <div className="warn-box">
          {r.analysis.warnings.map((w, i) => <div key={i} className="warn-line"><AlertIcon size={12} style={{marginRight:4}} /> Line {w.line}: {w.message}</div>)}
        </div>
      )}
      {/* Variables */}
      {Object.keys(r.variables || {}).length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div className="phase-section-title">Final Variables</div>
          <table className="var-tbl">
            <thead><tr><th>Name</th><th>Value</th><th>Type</th></tr></thead>
            <tbody>
              {Object.entries(r.variables).map(([n, v]) => (
                <tr key={n}>
                  <td className="v-name">{n}</td>
                  <td className="v-val">{v === null ? 'None' : typeof v === 'boolean' ? String(v) : typeof v === 'string' ? `"${v}"` : String(v)}</td>
                  <td className="v-type">{v === null ? 'none' : typeof v === 'boolean' ? 'bool' : typeof v === 'number' ? 'int' : typeof v === 'string' ? 'str' : typeof v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ─── Lexical Analysis Tab ────────────────────────────────────────────────── */
function LexicalTab({ r }) {
  return (
    <div className="phase-tab">
      <TokenVisualizer tokens={r.tokens} />
    </div>
  );
}

/* ─── Syntax Analysis Tab ─────────────────────────────────────────────────── */
function SyntaxTab({ r }) {
  return (
    <div className="phase-tab">
      <ASTTreeVisualizer astTree={r.ast_tree} />
      {r.ast && (
        <div style={{ marginTop: 14 }}>
          <pre className="ast-json">{JSON.stringify(r.ast, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

/* ─── Semantic Analysis Tab ───────────────────────────────────────────────── */
function SemTab({ r }) {
  return (
    <div className="phase-tab">
      <SemanticVisualizer analysis={r.analysis} />
    </div>
  );
}

/* ─── IR Generation Tab ───────────────────────────────────────────────────── */
function IRTab({ r }) {
  return (
    <div className="phase-tab">
      <IRVisualizer ir={r.ir} />
    </div>
  );
}

/* ─── Optimization Tab ────────────────────────────────────────────────────── */
function OptTab({ r }) {
  return (
    <div className="phase-tab">
      <OptimizationVisualizer optimization={r.optimization} />
    </div>
  );
}

/* ─── Code Gen Tab ────────────────────────────────────────────────────────── */
function CodeGenTab({ r }) {
  return (
    <div className="phase-tab">
      <CodeGenVisualizer codegen={r.codegen} />
    </div>
  );
}
