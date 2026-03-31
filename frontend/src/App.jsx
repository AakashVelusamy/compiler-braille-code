import React, { useState, useCallback, useEffect, useRef } from 'react';
import CodeEditor, { DEFAULT_CODE } from './components/CodeEditor';
import BrailleDisplay from './components/BrailleDisplay';
import OutputPanel from './components/OutputPanel';
import DebuggerPanel from './components/DebuggerPanel';
import PipelineTimeline from './components/PipelineTimeline';
import ExamplesGallery from './components/ExamplesGallery';
import ExportButtons from './components/ExportButtons';
import { compileCode, debugCode, translateCode } from './api/compilerApi';
import { PlayIcon, DebugIcon, CodeIcon, XIcon, TrashIcon } from './components/Icons';
import './App.css';

export default function App() {
  const [source, setSource] = useState(DEFAULT_CODE);
  const [result, setResult] = useState(null);
  const [braille, setBraille] = useState('');
  const [loading, setLoading] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [debugSteps, setDebugSteps] = useState(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [activeDebugLine, setActiveDebugLine] = useState(null);
  const [showExamples, setShowExamples] = useState(false);
  const [liveBraille, setLiveBraille] = useState('');
  const [isLive, setIsLive] = useState(false);
  const timerRef = useRef(null);

  // Live braille preview
  useEffect(() => {
    if (!source.trim()) { setLiveBraille(''); setIsLive(false); return; }
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      try { const d = await translateCode(source); setLiveBraille(d.braille || ''); setIsLive(true); }
      catch { setLiveBraille(''); setIsLive(false); }
    }, 500);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [source]);

  const handleCompile = useCallback(async () => {
    if (!source.trim()) return;
    setLoading(true); setResult(null); setBraille('');
    setDebugMode(false); setDebugSteps(null); setActiveDebugLine(null);
    try {
      const d = await compileCode(source); setResult(d); setBraille(d.braille || ''); setIsLive(false);
    } catch (err) {
      setResult({ success: false, output: [], variables: {}, ast: {}, analysis: {}, tokens: [],
        errors: [{ phase: 'network', message: err.response?.data?.error || err.message, line: 0 }] });
    } finally { setLoading(false); }
  }, [source]);

  const handleDebug = useCallback(async () => {
    if (!source.trim()) return;
    setDebugLoading(true); setDebugSteps(null); setDebugMode(true);
    setActiveDebugLine(null); setResult(null); setBraille('');
    try { const d = await debugCode(source); setDebugSteps(d.steps || []); }
    catch (err) {
      setDebugSteps([]); setDebugMode(false);
      setResult({ success: false, output: [], variables: {}, ast: {}, analysis: {}, tokens: [],
        errors: [{ phase: 'debug', message: err.response?.data?.error || err.message, line: 0 }] });
    } finally { setDebugLoading(false); }
  }, [source]);

  const reset = (code) => {
    if (code !== undefined) setSource(code);
    setResult(null); setBraille(''); setDebugMode(false); setDebugSteps(null); setActiveDebugLine(null);
  };

  const errLines = result?.errors?.map(e => ({ line: e.line, message: e.message })) || [];
  const dispBraille = braille || liveBraille;

  return (
    <div className="app">

      {/* ─── Academic Top Strip ─── */}
      <div className="acad-strip">
        <div className="acad-left">
          <span className="acad-course">23XT67 - Compiler Design Lab</span>
          <span className="acad-divider" />
        </div>
        <div className="acad-right">
          <span className="acad-divider" />
          <span className="acad-member">
            <span className="acad-roll">23PT01</span>
            <span className="acad-name">Aakash Velusamy</span>
          </span>
          <span className="acad-divider" />
          <span className="acad-member">
            <span className="acad-roll">23PT11</span>
            <span className="acad-name">Harshil Bhavik Momaya</span>
          </span>
        </div>
      </div>

      {/* ─── Header ─── */}
      <header className="hdr">
        <div className="hdr-left">
          <div className="logo">
            <div className="logo-icon">
              <span className="logo-braille">⠃⠉⠉</span>
            </div>
            <span className="logo-name">BrailleCodeCompiler</span>
          </div>
        </div>
        <div className="hdr-center">
          <PipelineTimeline result={result} loading={loading} />
        </div>
      </header>

      {/* ─── Toolbar ─── */}
      <div className="toolbar">
        <div className="tb-left">
          <button className="btn btn-run" onClick={handleCompile} disabled={loading || debugLoading}>
            {loading ? <><span className="spin" /><span className="btn-lbl"> Compiling…</span></> : <><PlayIcon /><span className="btn-lbl"> Compile &amp; Run</span></>}
          </button>
          <button className="btn btn-dbg" onClick={handleDebug} disabled={loading || debugLoading}>
            {debugLoading ? <><span className="spin" /><span className="btn-lbl"> Debugging…</span></> : <><DebugIcon className="btn-icon" /><span className="btn-lbl"> Debug</span></>}
          </button>
          <div className="tb-sep" />
          <button className="btn btn-ghost" onClick={() => setShowExamples(true)}>
            <CodeIcon size={14} /><span className="btn-lbl"> Examples</span>
          </button>
          {debugMode && <button className="btn btn-ghost btn-exit" onClick={() => reset()}>
            <XIcon size={14} /><span className="btn-lbl"> Exit Debug</span>
          </button>}
          <button className="btn btn-ghost" onClick={() => reset('')}>
            <TrashIcon size={14} /><span className="btn-lbl"> Clear</span>
          </button>
        </div>
        {debugMode && <span className="tb-debug-tag">DEBUG MODE</span>}
      </div>

      {/* ─── Export ─── */}
      {result && !debugMode && <ExportButtons source={source} braille={braille} result={result} />}

      {/* ─── Main Layout ─── */}
      <div className="main">
        <div className="col-left">
          <CodeEditor value={source} onChange={setSource} highlightLine={activeDebugLine} errors={errLines} />
          <BrailleDisplay braille={dispBraille} loading={loading} isLive={isLive && !braille} />
        </div>
        <div className="col-right">
          {debugMode ? (
            <div className="debug-panel">
              <div className="panel-bar">
                <span className="panel-title">Debugger</span>
                <span className="badge badge-warn">Step-by-step</span>
              </div>
              <div className="debug-body">
                <DebuggerPanel steps={debugSteps} loading={debugLoading} onStepChange={s => setActiveDebugLine(s?.line || null)} />
              </div>
            </div>
          ) : (
            <OutputPanel result={result} loading={loading} />
          )}
        </div>
      </div>

      {showExamples && <ExamplesGallery onSelect={c => reset(c)} onClose={() => setShowExamples(false)} />}
    </div>
  );
}
