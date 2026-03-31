import React from 'react';
import { ZapIcon, TreeIcon, SearchIcon, CodeIcon, CogIcon, CpuIcon, CheckIcon, XIcon, ArrowRightSlimIcon } from './Icons';

const PHASES = [
  { key: 'lexical',       label: 'Lexical Analysis',      Icon: ZapIcon, num: '1' },
  { key: 'syntax',        label: 'Syntax Analysis',       Icon: TreeIcon, num: '2' },
  { key: 'semantic',      label: 'Semantic Analysis',     Icon: SearchIcon, num: '3' },
  { key: 'ir',            label: 'Intermediate Code Generation', Icon: CodeIcon, num: '4' },
  { key: 'optimization',  label: 'Code Optimization',     Icon: CogIcon,  num: '5' },
  { key: 'codegen',       label: 'Code Generation',      Icon: CpuIcon, num: '6' },
];

export default function PipelineTimeline({ result, loading }) {
  const failPhase = result?.errors?.[0]?.phase;

  const status = (key) => {
    if (loading) return 'running';
    if (!result) return 'idle';
    if (!failPhase) return 'ok';
    const fi = PHASES.findIndex(p => p.key === failPhase);
    const ci = PHASES.findIndex(p => p.key === key);
    if (fi === -1) return 'ok';
    return ci < fi ? 'ok' : ci === fi ? 'fail' : 'skip';
  };

  return (
    <div className="pipe">
      {PHASES.map((p, i) => {
        const s = status(p.key);
        return (
          <React.Fragment key={p.key}>
            <div className={`pipe-step pipe-${s}`} title={`Phase ${p.num}: ${p.label}`}>
              <span className="pipe-num">{p.num}</span>
              <p.Icon size={11} className="pipe-icon-main" />
              <span className="pipe-lbl">{p.label}</span>
              {s === 'fail' && <XIcon size={10} className="pipe-status-icon" />}
            </div>
            {i < PHASES.length - 1 && <ArrowRightSlimIcon size={10} className={`pipe-arrow ${s === 'fail' || s === 'skip' ? 'dim' : ''}`} />}
          </React.Fragment>
        );
      })}
    </div>
  );
}
