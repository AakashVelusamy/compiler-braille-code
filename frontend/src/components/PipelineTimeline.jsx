import React from 'react';

const PHASES = [
  { key: 'translation', label: 'Translate', sym: '⠃' },
  { key: 'lexer',       label: 'Lex',       sym: '⚡' },
  { key: 'parser',      label: 'Parse',     sym: '🌳' },
  { key: 'semantic',    label: 'Analyze',   sym: '🔎' },
  { key: 'runtime',     label: 'Execute',   sym: '▶' },
];

export default function PipelineTimeline({ result, loading }) {
  const failPhase = result?.errors?.[0]?.phase;

  const status = (key) => {
    if (loading) return 'running';
    if (!result) return 'idle';
    if (!failPhase) return 'ok';
    const fi = PHASES.findIndex(p => p.key === failPhase);
    const ci = PHASES.findIndex(p => p.key === key);
    if (fi === -1) return 'ok';
    return ci < fi ? 'ok' : ci === fi ? 'fail' : 'skip';
  };

  return (
    <div className="pipe">
      {PHASES.map((p, i) => {
        const s = status(p.key);
        return (
          <React.Fragment key={p.key}>
            <div className={`pipe-step pipe-${s}`}>
              <span className="pipe-sym">{p.sym}</span>
              <span className="pipe-lbl">{p.label}</span>
              {s === 'ok' && <span className="pipe-chk">✓</span>}
              {s === 'fail' && <span className="pipe-x">✗</span>}
            </div>
            {i < PHASES.length - 1 && <span className={`pipe-arrow ${s === 'fail' || s === 'skip' ? 'dim' : ''}`}>→</span>}
          </React.Fragment>
        );
      })}
    </div>
  );
}
