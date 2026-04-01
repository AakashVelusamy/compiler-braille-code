import React, { useState } from 'react';
import { CogIcon, ZapIcon, TrashIcon, SparklesIcon, ArrowRightIcon } from './Icons';

const PASS_COLORS = {
  'Constant Folding': { bg: 'rgba(74,222,128,0.08)', bd: 'rgba(74,222,128,0.25)', tx: '#86efac', Icon: CogIcon },
  'Constant Propagation': { bg: 'rgba(108,140,255,0.08)', bd: 'rgba(108,140,255,0.25)', tx: '#93b4ff', Icon: ZapIcon },
  'Dead Code Elimination': { bg: 'rgba(248,113,113,0.08)', bd: 'rgba(248,113,113,0.25)', tx: '#fca5a5', Icon: TrashIcon },
  'Strength Reduction': { bg: 'rgba(251,191,36,0.08)', bd: 'rgba(251,191,36,0.25)', tx: '#fcd34d', Icon: ZapIcon },
};

const DEFAULT_PASS = { bg: 'rgba(156,163,180,0.06)', bd: 'rgba(156,163,180,0.15)', tx: '#9ca3b4', Icon: CogIcon };

export default function OptimizationVisualizer({ optimization }) {
  const [tab, setTab] = useState('log');

  if (!optimization?.log) return <div className="placeholder"></div>;

  const { original_count, optimized_count, eliminated, stats, log, instructions } = optimization;
  const totalOpts = log.length;

  return (
    <div className="opt-viz">
      {/* Summary Bar */}
      <div className="opt-summary">
        <div className="opt-metric">
          <span className="opt-metric-val">{original_count}</span>
          <span className="opt-metric-lbl">Before</span>
        </div>
        <span className="opt-arrow"><ArrowRightIcon size={14} /></span>
        <div className="opt-metric opt-metric-hl">
          <span className="opt-metric-val">{optimized_count}</span>
          <span className="opt-metric-lbl">After</span>
        </div>
        {eliminated > 0 && (
          <div className="opt-metric opt-metric-cut">
            <span className="opt-metric-val">-{eliminated}</span>
            <span className="opt-metric-lbl">Eliminated</span>
          </div>
        )}
        <div className="opt-sep" />
        {Object.entries(stats).map(([key, count]) => {
          if (count <= 0) return null;
          const pc = PASS_COLORS[keyToPass(key)] || DEFAULT_PASS;
          return (
            <span key={key} className="opt-stat-pill" style={{
              background: pc.bg,
              borderColor: pc.bd,
              color: pc.tx,
            }}>
              <pc.Icon size={10} style={{ marginRight: 4 }} /> {count}
            </span>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="opt-tabs">
        <button className={`opt-tab ${tab === 'log' ? 'on' : ''}`} onClick={() => setTab('log')}>
          Optimization Log ({totalOpts})
        </button>
        <button className={`opt-tab ${tab === 'result' ? 'on' : ''}`} onClick={() => setTab('result')}>
          Optimized IR
        </button>
      </div>

      {/* Content */}
      <div className="opt-content">
        {tab === 'log' ? (
          totalOpts === 0 ? (
            <div className="opt-no-opts">
              <span className="opt-no-icon"><SparklesIcon size={20} /></span>
              <span className="opt-no-text">No optimizations applicable - code is already optimal</span>
            </div>
          ) : (
            <div className="opt-log">
              {log.map((entry, i) => {
                const pc = PASS_COLORS[entry.pass] || DEFAULT_PASS;
                return (
                  <div key={i} className="opt-entry" style={{ '--opt-bg': pc.bg, '--opt-bd': pc.bd }}>
                    <div className="opt-entry-header">
                      <span className="opt-entry-icon"><pc.Icon size={14} /></span>
                      <span className="opt-entry-pass" style={{ color: pc.tx }}>{entry.pass}</span>
                      <span className="opt-entry-idx">#{entry.index}</span>
                    </div>
                    <div className="opt-entry-diff">
                      <div className="opt-before">
                        <span className="opt-diff-lbl">Before</span>
                        <code className="opt-code opt-code-del">{entry.original}</code>
                      </div>
                      <span className="opt-diff-arrow"><ArrowRightIcon size={12} /></span>
                      <div className="opt-after">
                        <span className="opt-diff-lbl">After</span>
                        <code className={`opt-code ${entry.optimized === 'REMOVED' ? 'opt-code-rm' : 'opt-code-add'}`}>
                          {entry.optimized}
                        </code>
                      </div>
                    </div>
                    <div className="opt-entry-desc">{entry.description}</div>
                  </div>
                );
              })}
            </div>
          )
        ) : (
          <div className="opt-result-ir">
            {instructions?.map((inst, i) => (
              <div key={i} className="ir-inst-mini">
                <span className="ir-idx">{i}</span>
                <code className="ir-inst-text">{inst.text}</code>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function keyToPass(key) {
  const map = {
    constant_folding: 'Constant Folding',
    constant_propagation: 'Constant Propagation',
    dead_code_elimination: 'Dead Code Elimination',
    strength_reduction: 'Strength Reduction',
  };
  return map[key] || key;
}
