import React, { useState } from 'react';

const MNEMONIC_COLORS = {
  'LOAD':  { bg: 'rgba(108,140,255,0.10)', tx: '#93b4ff' },
  'STORE': { bg: 'rgba(108,140,255,0.10)', tx: '#93b4ff' },
  'MOVI':  { bg: 'rgba(108,140,255,0.08)', tx: '#7da3f0' },
  'MOV':   { bg: 'rgba(108,140,255,0.08)', tx: '#7da3f0' },
  'ADD':   { bg: 'rgba(74,222,128,0.08)',  tx: '#86efac' },
  'SUB':   { bg: 'rgba(74,222,128,0.08)',  tx: '#86efac' },
  'MUL':   { bg: 'rgba(74,222,128,0.08)',  tx: '#86efac' },
  'DIV':   { bg: 'rgba(74,222,128,0.08)',  tx: '#86efac' },
  'MOD':   { bg: 'rgba(74,222,128,0.08)',  tx: '#86efac' },
  'CMP':   { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'CMP_EQ':{ bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'JMP':   { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JE':    { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JNE':   { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JL':    { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JG':    { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JLE':   { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'JGE':   { bg: 'rgba(192,132,252,0.10)', tx: '#d8b4fe' },
  'PUSH':  { bg: 'rgba(45,212,191,0.08)',  tx: '#5eead4' },
  'CALL':  { bg: 'rgba(45,212,191,0.10)',  tx: '#5eead4' },
  'NEG':   { bg: 'rgba(248,113,113,0.08)', tx: '#fca5a5' },
  'NOT':   { bg: 'rgba(248,113,113,0.08)', tx: '#fca5a5' },
  'AND':   { bg: 'rgba(251,191,36,0.06)',  tx: '#fbbf24' },
  'OR':    { bg: 'rgba(251,191,36,0.06)',  tx: '#fbbf24' },
  'HALT':  { bg: 'rgba(248,113,113,0.10)', tx: '#f87171' },
  'SETEQ': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'SETNE': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'SETLT': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'SETGT': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'SETLE': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
  'SETGE': { bg: 'rgba(251,191,36,0.08)',  tx: '#fcd34d' },
};

const DEFAULT_MN = { bg: 'rgba(156,163,180,0.06)', tx: '#9ca3b4' };

const LEGEND = [
  { label: 'Load/Store',  color: '#93b4ff' },
  { label: 'Arithmetic',  color: '#86efac' },
  { label: 'Compare/Set', color: '#fcd34d' },
  { label: 'Jump/Branch', color: '#d8b4fe' },
  { label: 'Call/Push',   color: '#5eead4' },
  { label: 'Control',     color: '#f87171' },
];

export default function CodeGenVisualizer({ codegen }) {
  const [view, setView] = useState('visual');

  if (!codegen?.instructions?.length) return <div className="placeholder"></div>;

  const { assembly_text, instruction_count, registers_used, memory_locations, memory_map, data_section, instructions } = codegen;

  return (
    <div className="cg-viz">
      {/* Header */}
      <div className="cg-header">
        <div className="cg-stats">
          <div className="cg-stat-item">
            <span className="cg-stat-num">{instruction_count}</span>
            <span className="cg-stat-lbl">instructions</span>
          </div>
          <div className="cg-stat-item">
            <span className="cg-stat-num">{registers_used}</span>
            <span className="cg-stat-lbl">registers</span>
          </div>
          <div className="cg-stat-item">
            <span className="cg-stat-num">{memory_locations}</span>
            <span className="cg-stat-lbl">memory slots</span>
          </div>
        </div>

        <div className="cg-legend">
          {LEGEND.map(l => (
            <div key={l.label} className="cg-leg-item">
              <span className="cg-leg-dot" style={{ background: l.color }} />
              {l.label}
            </div>
          ))}
        </div>

        <div className="tok-view-toggle">
          <button className={view === 'visual' ? 'active' : ''} onClick={() => setView('visual')}>Visual</button>
          <button className={view === 'text' ? 'active' : ''} onClick={() => setView('text')}>Assembly</button>
          <button className={view === 'memory' ? 'active' : ''} onClick={() => setView('memory')}>Memory</button>
        </div>
      </div>

      {/* Content */}
      <div className="cg-body">
        {view === 'text' ? (
          <pre className="cg-asm-text">{assembly_text}</pre>
        ) : view === 'memory' ? (
          <div className="cg-memory">
            <div className="cg-section">
              <div className="cg-section-title">Register File</div>
              <div className="cg-reg-grid">
                {Array.from({ length: 8 }, (_, i) => {
                  const rName = `R${i}`;
                  const used = i < registers_used;
                  return (
                    <div key={i} className={`cg-reg ${used ? 'cg-reg-used' : ''}`}>
                      <span className="cg-reg-name">{rName}</span>
                      <span className="cg-reg-status">{used ? 'allocated' : 'free'}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {Object.keys(memory_map).length > 0 && (
              <div className="cg-section">
                <div className="cg-section-title">Memory Map</div>
                <table className="cg-mem-table">
                  <thead><tr><th>Variable</th><th>Address</th></tr></thead>
                  <tbody>
                    {Object.entries(memory_map).map(([name, addr]) => (
                      <tr key={name}>
                        <td className="cg-mem-var">{name}</td>
                        <td className="cg-mem-addr">{addr}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div className="cg-instructions">
            {instructions.map((inst, i) => {
              const mc = MNEMONIC_COLORS[inst.mnemonic] || DEFAULT_MN;
              const isLabel = inst.label && !inst.mnemonic;

              return (
                <div key={i} className={`cg-inst ${isLabel ? 'cg-inst-label' : ''}`}>
                  <span className="cg-idx">{i}</span>
                  {isLabel ? (
                    <span className="cg-label-name">{inst.label}:</span>
                  ) : (
                    <>
                      <span className="cg-mnemonic" style={{ color: mc.tx, background: mc.bg }}>
                        {inst.mnemonic}
                      </span>
                      <span className="cg-operands">{inst.operands}</span>
                      {inst.comment && <span className="cg-comment">; {inst.comment}</span>}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
