import React from 'react';

export default function BrailleDisplay({ braille, loading }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-icon">⠃</span>
        <h3>Braille output</h3>
        <span className="panel-badge">Unicode</span>
      </div>
      <div className="braille-content">
        {loading ? (
          <div className="loading-placeholder">Translating...</div>
        ) : braille ? (
          <pre className="braille-text">{braille}</pre>
        ) : (
          <div className="empty-placeholder">
            Braille representation will appear here after compilation
          </div>
        )}
      </div>
    </div>
  );
}
