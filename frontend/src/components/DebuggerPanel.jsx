import React, { useState, useEffect, useRef } from 'react';

const EV = { assign:'←', print:'▶', branch:'◇', loop_start:'↻', loop_end:'■', error:'✗' };
const EC = { assign:'#58a6ff', print:'#3fb950', branch:'#d29922', loop_start:'#a855f7', loop_end:'#8b949e', error:'#f85149' };

export default function DebuggerPanel({ steps, loading, onStepChange }) {
  const [cur, setCur] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(800);
  const playRef = useRef(null);
  const tlRef = useRef(null);

  const total = steps?.length || 0;
  const step = steps?.[cur];

  useEffect(() => { onStepChange?.(step || null); }, [cur, step, onStepChange]);
  useEffect(() => {
    if (tlRef.current) tlRef.current.querySelector('.tl-step.active')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [cur]);
  useEffect(() => {
    if (playing && total > 0) {
      playRef.current = setInterval(() => {
        setCur(p => { if (p >= total - 1) { setPlaying(false); return p; } return p + 1; });
      }, speed);
    }
    return () => { if (playRef.current) clearInterval(playRef.current); };
  }, [playing, total, speed]);
  useEffect(() => { setCur(0); setPlaying(false); }, [steps]);

  if (loading) return <div className="placeholder">Running debugger...</div>;
  if (!steps || !total) return <div className="placeholder">Click Debug to step through your program</div>;

  return (
    <div className="dbg">
      {/* Controls */}
      <div className="dbg-ctrl">
        <button onClick={() => { setCur(0); setPlaying(false); }}>⏮</button>
        <button onClick={() => { setCur(p => Math.max(0, p-1)); setPlaying(false); }}>⏪</button>
        <button className={`dbg-play ${playing ? 'on' : ''}`} onClick={() => setPlaying(p => !p)}>
          {playing ? '⏸' : '▶'}
        </button>
        <button onClick={() => { setCur(p => Math.min(total-1, p+1)); setPlaying(false); }}>⏩</button>
        <button onClick={() => { setCur(total-1); setPlaying(false); }}>⏭</button>
        <span className="dbg-count">{cur+1} / {total}</span>
        <select className="dbg-speed" value={speed} onChange={e => setSpeed(+e.target.value)}>
          <option value={1500}>0.5x</option><option value={800}>1x</option>
          <option value={400}>2x</option><option value={150}>4x</option>
        </select>
      </div>

      {/* Progress */}
      <div className="dbg-prog"><div className="dbg-prog-fill" style={{ width: `${((cur+1)/total)*100}%` }} /></div>

      {/* Current step detail */}
      {step && (
        <div className="dbg-detail">
          <div className="dbg-desc-row">
            <span className="dbg-ev" style={{ color: EC[step.event] || '#8b949e' }}>{EV[step.event] || '•'}</span>
            <span className="dbg-desc">{step.description}</span>
            <span className="dbg-line">Line {step.line}</span>
          </div>

          {step.variables && Object.keys(step.variables).length > 0 && (
            <div className="dbg-vars">
              <div className="dbg-sec-title">Variables</div>
              <div className="dbg-var-list">
                {Object.entries(step.variables).map(([n, info]) => (
                  <span key={n} className="dbg-var">
                    <span className="dbg-vn">{n}</span>=<span className="dbg-vv">{info.display}</span>
                    <span className="dbg-vt">{info.type}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {step.total_output?.length > 0 && (
            <div className="dbg-out">
              <div className="dbg-sec-title">Output</div>
              <div className="dbg-out-pills">
                {step.total_output.map((l, i) => (
                  <span key={i} className={`dbg-out-pill ${i === step.total_output.length-1 && step.output_line ? 'new' : ''}`}>{l}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      <div className="tl" ref={tlRef}>
        {steps.map((s, i) => (
          <div key={i} className={`tl-step ${i === cur ? 'active' : ''} ${i < cur ? 'past' : ''}`}
            onClick={() => { setCur(i); setPlaying(false); }}>
            <span className="tl-ev" style={{ color: EC[s.event] || '#8b949e' }}>{EV[s.event] || '•'}</span>
            <span className="tl-num">#{s.step_number}</span>
            <span className="tl-desc">{s.description}</span>
            <span className="tl-ln">L{s.line}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
