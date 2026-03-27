import React, { useState, useCallback } from 'react';
import CodeEditor, { DEFAULT_CODE } from './components/CodeEditor';
import BrailleDisplay from './components/BrailleDisplay';
import OutputPanel from './components/OutputPanel';
import { compileCode } from './api/compilerApi';
import './App.css';

export default function App() {
  const [source, setSource] = useState(DEFAULT_CODE);
  const [result, setResult] = useState(null);
  const [braille, setBraille] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCompile = useCallback(async () => {
    if (!source.trim()) return;
    setLoading(true);
    setResult(null);
    setBraille('');

    try {
      const data = await compileCode(source);
      setResult(data);
      setBraille(data.braille || '');
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Network error';
      setResult({
        success: false,
        output: [],
        variables: {},
        ast: {},
        analysis: {},
        tokens: [],
        errors: [{ phase: 'network', message: msg, line: 0 }],
      });
    } finally {
      setLoading(false);
    }
  }, [source]);

  const handleClear = () => {
    setSource('');
    setResult(null);
    setBraille('');
  };

  const handleLoadExample = () => {
    setSource(DEFAULT_CODE);
    setResult(null);
    setBraille('');
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <span className="logo-braille">⠃⠉</span>
          <h1>BrailleCode<span className="header-thin">Compiler</span></h1>
        </div>
        <div className="header-right">
          <span className="header-subtitle">23XT67 — Compiler Design Lab</span>
        </div>
      </header>

      {/* Toolbar */}
      <div className="toolbar">
        <button className="btn btn-primary" onClick={handleCompile} disabled={loading}>
          {loading ? '⟳ Compiling...' : '▶ Compile & Run'}
        </button>
        <button className="btn btn-secondary" onClick={handleClear}>
          Clear
        </button>
        <button className="btn btn-secondary" onClick={handleLoadExample}>
          Load example
        </button>
        <div className="toolbar-info">
          <span className="pipeline-label">
            English → Braille → Lexer → Parser → Analyzer → Interpreter
          </span>
        </div>
      </div>

      {/* Main layout */}
      <div className="main-grid">
        {/* Left column: Editor + Braille */}
        <div className="left-col">
          <CodeEditor value={source} onChange={setSource} />
          <BrailleDisplay braille={braille} loading={loading} />
        </div>

        {/* Right column: Output */}
        <div className="right-col">
          <OutputPanel result={result} loading={loading} />
        </div>
      </div>
    </div>
  );
}
