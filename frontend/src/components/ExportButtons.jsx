import React from 'react';

function dl(name, content, mime = 'text/plain') {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([content], { type: mime }));
  a.download = name; document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(a.href);
}

export default function ExportButtons({ source, braille, result }) {
  return (
    <div className="export-bar">
      <span className="export-lbl">Export</span>
      <button className="exp-btn" disabled={!source} onClick={() => dl('program.bcc', source)}>.bcc</button>
      <button className="exp-btn" disabled={!braille} onClick={() => dl('braille.brl', braille, 'text/plain;charset=utf-8')}>.brl</button>
      <button className="exp-btn" disabled={!result?.ast} onClick={() => dl('ast.json', JSON.stringify(result.ast, null, 2), 'application/json')}>AST</button>
      <button className="exp-btn" disabled={!result?.output?.length} onClick={() => dl('output.txt', result.output.join('\n'))}>Output</button>
      <button className="exp-btn exp-all" disabled={!result} onClick={() => dl('report.json', JSON.stringify({
        source, braille, ast: result?.ast, ast_tree: result?.ast_tree, tokens: result?.tokens,
        output: result?.output, variables: result?.variables, analysis: result?.analysis, errors: result?.errors,
      }, null, 2), 'application/json')}>Full report</button>
    </div>
  );
}
