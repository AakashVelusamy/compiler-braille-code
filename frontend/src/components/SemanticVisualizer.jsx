import React from 'react';
import { CheckIcon, XIcon, AlertIcon } from './Icons';

export default function SemanticVisualizer({ analysis }) {
  if (!analysis?.symbols) return <div className="placeholder"></div>;

  const { success, errors, warnings, symbols } = analysis;

  return (
    <div className="sem-viz">
      {/* Status banner */}
      

      {/* Errors */}
      {errors?.length > 0 && (
        <div className="sem-section">
          <div className="sem-section-title">Errors</div>
          {errors.map((e, i) => (
            <div key={i} className="sem-error">
              <span className="sem-error-icon"><XIcon size={12} /></span>
              <span className="sem-error-line">Line {e.line}</span>
              <span className="sem-error-msg">{e.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {warnings?.length > 0 && (
        <div className="sem-section">
          <div className="sem-section-title">Warnings</div>
          {warnings.map((w, i) => (
            <div key={i} className="sem-warning">
              <span className="sem-warn-icon"><AlertIcon size={12} /></span>
              <span className="sem-warn-line">Line {w.line}</span>
              <span className="sem-warn-msg">{w.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Symbol Table */}
      {symbols?.length > 0 && (
        <div className="sem-section">
          <div className="sem-section-title">Symbol Table</div>
          <table className="sem-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Scope</th>
                <th>Declared</th>
              </tr>
            </thead>
            <tbody>
              {symbols.map((s, i) => (
                <tr key={i}>
                  <td className="sem-sym-name">{s.name}</td>
                  <td>
                    <span className={`sem-type-badge sem-type-${s.inferred_type}`}>
                      {s.inferred_type}
                    </span>
                  </td>
                  <td className="sem-scope">
                    <span className="sem-scope-badge">
                      {s.scope_depth === 0 ? 'global' : `depth ${s.scope_depth}`}
                    </span>
                  </td>
                  <td className="sem-decl-line">Line {s.declared_line}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
