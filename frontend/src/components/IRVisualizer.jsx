import React, { useState } from 'react';

const OP_COLORS = {
  '=':        { bg: 'rgba(108,140,255,0.10)', bd: 'rgba(108,140,255,0.25)', tx: '#93b4ff' },
  '+':        { bg: 'rgba(74,222,128,0.08)',  bd: 'rgba(74,222,128,0.20)', tx: '#86efac' },
  '-':        { bg: 'rgba(74,222,128,0.08)',  bd: 'rgba(74,222,128,0.20)', tx: '#86efac' },
  '*':        { bg: 'rgba(74,222,128,0.08)',  bd: 'rgba(74,222,128,0.20)', tx: '#86efac' },
  '/':        { bg: 'rgba(74,222,128,0.08)',  bd: 'rgba(74,222,128,0.20)', tx: '#86efac' },
  '%':        { bg: 'rgba(74,222,128,0.08)',  bd: 'rgba(74,222,128,0.20)', tx: '#86efac' },
  'LABEL':    { bg: 'rgba(192,132,252,0.10)', bd: 'rgba(192,132,252,0.25)', tx: '#d8b4fe' },
  'GOTO':     { bg: 'rgba(251,191,36,0.10)',  bd: 'rgba(251,191,36,0.25)',  tx: '#fcd34d' },
  'IF_FALSE': { bg: 'rgba(251,191,36,0.10)',  bd: 'rgba(251,191,36,0.25)',  tx: '#fcd34d' },
  'IF_TRUE':  { bg: 'rgba(251,191,36,0.10)',  bd: 'rgba(251,191,36,0.25)',  tx: '#fcd34d' },
  'PARAM':    { bg: 'rgba(45,212,191,0.08)',  bd: 'rgba(45,212,191,0.20)', tx: '#5eead4' },
  'CALL':     { bg: 'rgba(45,212,191,0.10)',  bd: 'rgba(45,212,191,0.25)', tx: '#5eead4' },
  'HALT':     { bg: 'rgba(248,113,113,0.08)', bd: 'rgba(248,113,113,0.20)', tx: '#fca5a5' },
};

const DEFAULT_COLOR = { bg: 'rgba(156,163,180,0.06)', bd: 'rgba(156,163,180,0.15)', tx: '#9ca3b4' };

function getOpCategory(op) {
  if (op === '=') return 'assign';
  if (['+','-','*','/','%'].includes(op)) return 'arith';
  if (['==','!=','<','>','<=','>='].includes(op)) return 'compare';
  if (['and','or','not'].includes(op)) return 'logic';
  if (['LABEL'].includes(op)) return 'label';
  if (['GOTO','IF_FALSE','IF_TRUE'].includes(op)) return 'jump';
  if (['PARAM','CALL'].includes(op)) return 'call';
  if (op === 'HALT') return 'halt';
  return 'other';
}

const LEGEND = [
  { key: 'assign',  label: 'Assignment', color: '#93b4ff' },
  { key: 'arith',   label: 'Arithmetic', color: '#86efac' },
  { key: 'compare', label: 'Comparison', color: '#86efac' },
  { key: 'jump',    label: 'Jump/Branch', color: '#fcd34d' },
  { key: 'label',   label: 'Label',      color: '#d8b4fe' },
  { key: 'call',    label: 'Call',        color: '#5eead4' },
];

export default function IRVisualizer({ ir }) {
  const [view, setView] = useState('visual');
  const [hoveredLine, setHoveredLine] = useState(null);

  if (!ir?.instructions?.length) return <div className="placeholder">Compile to see Intermediate Code</div>;

  return (
    <div className="ir-viz">
      {/* Header */}
      <div className="ir-header">
        <div className="ir-stats">
          <span className="ir-stat">
            <span className="ir-stat-num">{ir.instruction_count}</span>
            <span className="ir-stat-lbl">instructions</span>
          </span>
        </div>
        <div className="ir-legend">
          {LEGEND.map(l => (
            <span key={l.key} className="ir-leg-item">
              <span className="ir-leg-dot" style={{ background: l.color }} />
              {l.label}
            </span>
          ))}
        </div>
        <div className="tok-view-toggle">
          <button className={view === 'visual' ? 'active' : ''} onClick={() => setView('visual')}>Visual</button>
          <button className={view === 'text' ? 'active' : ''} onClick={() => setView('text')}>Text</button>
        </div>
      </div>

      {/* Content */}
      {view === 'text' ? (
        <pre className="ir-text-view">{ir.text}</pre>
      ) : (
        <div className="ir-instructions">
          {ir.instructions.map((inst, i) => {
            const c = OP_COLORS[inst.op] || DEFAULT_COLOR;
            const isLabel = inst.op === 'LABEL';
            const isHovered = hoveredLine !== null && inst.line === hoveredLine && inst.line > 0;

            return (
              <div
                key={i}
                className={`ir-inst ${isLabel ? 'ir-inst-label' : ''} ${isHovered ? 'ir-inst-hl' : ''}`}
                style={{ '--ir-bg': c.bg, '--ir-bd': c.bd, '--ir-tx': c.tx }}
                onMouseEnter={() => inst.line > 0 && setHoveredLine(inst.line)}
                onMouseLeave={() => setHoveredLine(null)}
              >
                <span className="ir-idx">{i}</span>
                {isLabel ? (
                  <div className="ir-label-row">
                    <span className="ir-label-name">{inst.label}:</span>
                    {inst.comment && <span className="ir-comment">{inst.comment}</span>}
                  </div>
                ) : (
                  <>
                    <span className="ir-op-badge" style={{ background: c.bg, borderColor: c.bd, color: c.tx }}>
                      {inst.op}
                    </span>
                    {inst.result && <span className="ir-result">{inst.result}</span>}
                    {inst.result && (inst.arg1 || inst.op === '=') && <span className="ir-eq">=</span>}
                    {inst.arg1 && <span className="ir-arg">{inst.arg1}</span>}
                    {inst.arg2 && inst.op !== 'CALL' && <span className="ir-op-sym">{inst.op}</span>}
                    {inst.arg2 && <span className="ir-arg">{inst.arg2}</span>}
                    {inst.line > 0 && <span className="ir-src-line">L{inst.line}</span>}
                    {inst.comment && <span className="ir-comment">; {inst.comment}</span>}
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
