import React, { useState, useRef, useEffect, useCallback } from 'react';

/*
 * Category → color mapping (matches the dark theme)
 */
const CATEGORY_COLORS = {
  program:    { bg: '#1f2937', border: '#6b7280', text: '#e5e7eb' },
  statement:  { bg: '#172554', border: '#3b82f6', text: '#93c5fd' },
  expression: { bg: '#172554', border: '#3b82f6', text: '#93c5fd' },
  operator:   { bg: '#3b1764', border: '#a855f7', text: '#d8b4fe' },
  literal:    { bg: '#14532d', border: '#22c55e', text: '#86efac' },
};

const DEFAULT_COLOR = { bg: '#1c2128', border: '#30363d', text: '#8b949e' };

function getColor(category) {
  return CATEGORY_COLORS[category] || DEFAULT_COLOR;
}

/*
 * Single tree node — renders label, type badge, and expand/collapse toggle
 */
function TreeNode({ node, depth = 0, highlightLine, onHoverLine }) {
  const [collapsed, setCollapsed] = useState(depth > 3);
  const hasChildren = node.children && node.children.length > 0;
  const color = getColor(node.category);
  const isHighlighted = highlightLine && node.line === highlightLine;

  return (
    <div className="ast-node-group">
      <div
        className={`ast-node ${isHighlighted ? 'ast-node-highlight' : ''}`}
        style={{
          '--node-bg': color.bg,
          '--node-border': color.border,
          '--node-text': color.text,
          marginLeft: depth * 24,
        }}
        onMouseEnter={() => onHoverLine && onHoverLine(node.line)}
        onMouseLeave={() => onHoverLine && onHoverLine(null)}
        onClick={() => hasChildren && setCollapsed(!collapsed)}
      >
        {/* Expand/collapse toggle */}
        {hasChildren && (
          <span className="ast-toggle">{collapsed ? '▸' : '▾'}</span>
        )}
        {!hasChildren && <span className="ast-toggle-spacer" />}

        {/* Node label */}
        <span className="ast-label">{node.label}</span>

        {/* Type badge */}
        <span className="ast-type-badge">{node.type}</span>

        {/* Line number */}
        {node.line > 0 && (
          <span className="ast-line-badge">L{node.line}</span>
        )}
      </div>

      {/* Children (if not collapsed) */}
      {hasChildren && !collapsed && (
        <div className="ast-children">
          {/* Vertical connector line */}
          <div
            className="ast-connector"
            style={{ left: depth * 24 + 12 }}
          />
          {node.children.map((child, i) => (
            <TreeNode
              key={child.id || i}
              node={child}
              depth={depth + 1}
              highlightLine={highlightLine}
              onHoverLine={onHoverLine}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/*
 * Legend showing category colors
 */
function TreeLegend() {
  const items = [
    { category: 'statement', label: 'Statement' },
    { category: 'operator', label: 'Operator' },
    { category: 'literal', label: 'Literal / Identifier' },
  ];

  return (
    <div className="ast-legend">
      {items.map(({ category, label }) => {
        const c = getColor(category);
        return (
          <span key={category} className="ast-legend-item">
            <span
              className="ast-legend-dot"
              style={{ background: c.border }}
            />
            {label}
          </span>
        );
      })}
    </div>
  );
}

/*
 * Main AST Tree Visualizer
 */
export default function ASTTreeVisualizer({ astTree, onHoverLine }) {
  const [highlightLine, setHighlightLine] = useState(null);

  const handleHoverLine = useCallback((line) => {
    setHighlightLine(line);
    if (onHoverLine) onHoverLine(line);
  }, [onHoverLine]);

  if (!astTree || !astTree.children) {
    return (
      <div className="ast-tree-empty">
        Compile your code to see the AST tree
      </div>
    );
  }

  return (
    <div className="ast-tree-visualizer">
      <TreeLegend />
      <div className="ast-tree-scroll">
        <TreeNode
          node={astTree}
          depth={0}
          highlightLine={highlightLine}
          onHoverLine={handleHoverLine}
        />
      </div>
    </div>
  );
}
