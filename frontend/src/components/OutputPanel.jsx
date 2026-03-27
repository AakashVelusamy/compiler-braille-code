import React, { useState } from 'react';

const TABS = [
  { key: 'output', label: 'Output' },
  { key: 'variables', label: 'Variables' },
  { key: 'tokens', label: 'Tokens' },
  { key: 'ast', label: 'AST' },
];

export default function OutputPanel({ result, loading }) {
  const [activeTab, setActiveTab] = useState('output');

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-icon">▶</span>
        <h3>Results</h3>
        {result?.success === true && (
          <span className="panel-badge success">Passed</span>
        )}
        {result?.success === false && (
          <span className="panel-badge error">Error</span>
        )}
      </div>

      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="output-content">
        {loading ? (
          <div className="loading-placeholder">Compiling...</div>
        ) : !result ? (
          <div className="empty-placeholder">
            Click "Compile & Run" to see results
          </div>
        ) : (
          <>
            {activeTab === 'output' && <OutputTab result={result} />}
            {activeTab === 'variables' && <VariablesTab result={result} />}
            {activeTab === 'tokens' && <TokensTab result={result} />}
            {activeTab === 'ast' && <ASTTab result={result} />}
          </>
        )}
      </div>
    </div>
  );
}

function OutputTab({ result }) {
  return (
    <div className="tab-content">
      {/* Errors */}
      {result.errors?.length > 0 && (
        <div className="error-section">
          {result.errors.map((err, i) => (
            <div key={i} className="error-line">
              <span className="error-phase">[{err.phase}]</span>
              <span className="error-msg">{err.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Program output */}
      {result.output?.length > 0 ? (
        <div className="program-output">
          {result.output.map((line, i) => (
            <div key={i} className="output-line">
              <span className="line-num">{i + 1}</span>
              <span className="line-text">{line}</span>
            </div>
          ))}
        </div>
      ) : (
        !result.errors?.length && (
          <div className="empty-placeholder">No output produced</div>
        )
      )}

      {/* Warnings */}
      {result.analysis?.warnings?.length > 0 && (
        <div className="warning-section">
          {result.analysis.warnings.map((w, i) => (
            <div key={i} className="warning-line">
              ⚠ Line {w.line}: {w.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function VariablesTab({ result }) {
  const vars = result.variables || {};
  const entries = Object.entries(vars);

  if (entries.length === 0) {
    return <div className="empty-placeholder">No variables in scope</div>;
  }

  return (
    <div className="tab-content">
      <table className="var-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Value</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([name, value]) => (
            <tr key={name}>
              <td className="var-name">{name}</td>
              <td className="var-value">{formatValue(value)}</td>
              <td className="var-type">{getType(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TokensTab({ result }) {
  const tokens = result.tokens || [];

  if (tokens.length === 0) {
    return <div className="empty-placeholder">No tokens generated</div>;
  }

  return (
    <div className="tab-content tokens-scroll">
      <table className="token-table">
        <thead>
          <tr>
            <th>Line</th>
            <th>Type</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((tok, i) => (
            <tr key={i} className={`token-row token-${tok.type.toLowerCase()}`}>
              <td className="tok-line">{tok.line}</td>
              <td className="tok-type">{tok.type}</td>
              <td className="tok-value">{formatTokenValue(tok.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ASTTab({ result }) {
  const ast = result.ast;

  if (!ast || Object.keys(ast).length === 0) {
    return <div className="empty-placeholder">No AST generated</div>;
  }

  return (
    <div className="tab-content">
      <pre className="ast-json">{JSON.stringify(ast, null, 2)}</pre>
    </div>
  );
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function formatValue(value) {
  if (value === null) return 'None';
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'string') return `"${value}"`;
  return String(value);
}

function getType(value) {
  if (value === null) return 'none';
  if (typeof value === 'boolean') return 'bool';
  if (typeof value === 'number') return 'int';
  if (typeof value === 'string') return 'str';
  return typeof value;
}

function formatTokenValue(value) {
  if (value === '') return '—';
  if (value === '\\n') return '↵';
  return String(value);
}
