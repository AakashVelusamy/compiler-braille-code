import React from 'react';

export default function BrailleDisplay({ braille, loading, isLive }) {
  return (
    <div className="braille-panel">
      <div className="panel-bar">
        <span className="braille-icon">⠃⠗⠇</span>
        <span className="panel-title">Braille</span>
        {isLive && <span className="badge badge-live">LIVE</span>}
      </div>
      <div className="braille-body">
        {loading ? (
          <div className="placeholder">Translating...</div>
        ) : braille ? (
          <pre className="braille-text">{braille}</pre>
        ) : (
          <div className="placeholder">Braille appears here as you type</div>
        )}
      </div>
    </div>
  );
}
