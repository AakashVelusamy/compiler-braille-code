import React, { useState, useCallback } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from './Icons';

const CAT_STYLE = {
  program:   { bg: '#1a1a2e', bd: '#6366f1', tx: '#a5b4fc' },
  statement: { bg: '#0c1929', bd: '#3b82f6', tx: '#93c5fd' },
  operator:  { bg: '#1e0a34', bd: '#a855f7', tx: '#d8b4fe' },
  literal:   { bg: '#0a2618', bd: '#22c55e', tx: '#86efac' },
};
const DEF = { bg: '#111', bd: '#444', tx: '#999' };
const col = c => CAT_STYLE[c] || DEF;

function Node({ node, depth = 0, hl, onHover }) {
  const [open, setOpen] = useState(depth < 3);
  const has = node.children?.length > 0;
  const c = col(node.category);
  const lit = hl && node.line === hl;

  return (
    <div className="ast-grp">
      <div className={`ast-nd${lit ? ' ast-lit' : ''}`}
        style={{ '--nbg': c.bg, '--nbd': c.bd, '--ntx': c.tx, marginLeft: depth * 20 }}
        onMouseEnter={() => onHover?.(node.line)} onMouseLeave={() => onHover?.(null)}
        onClick={() => has && setOpen(!open)}>
        {has ? <span className="ast-arr">{open ? <ChevronDownIcon size={10} /> : <ChevronRightIcon size={10} />}</span> : <span className="ast-spc" />}
        <span className="ast-lbl">{node.label}</span>
        <span className="ast-badge">{node.type}</span>
        {node.line > 0 && <span className="ast-ln">:{node.line}</span>}
      </div>
      {has && open && (
        <div className="ast-ch">
          <div className="ast-vline" style={{ left: depth * 20 + 10 }} />
          {node.children.map((ch, i) => (
            <Node key={ch.id || i} node={ch} depth={depth + 1} hl={hl} onHover={onHover} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ASTTreeVisualizer({ astTree }) {
  const [hl, setHl] = useState(null);
  const hover = useCallback(l => setHl(l), []);

  if (!astTree?.children) return <div className="placeholder"></div>;

  return (
    <div className="ast-viz">
      <div className="ast-legend">
        {[['statement', 'Statement'], ['operator', 'Operator'], ['literal', 'Literal']].map(([k, v]) => (
          <span key={k} className="ast-leg-item"><span className="ast-leg-dot" style={{ background: col(k).bd }} />{v}</span>
        ))}
      </div>
      <div className="ast-scroll"><Node node={astTree} depth={0} hl={hl} onHover={hover} /></div>
    </div>
  );
}
