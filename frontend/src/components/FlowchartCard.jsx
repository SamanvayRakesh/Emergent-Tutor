import { useId, useState } from 'react';
import { wrapVisualText } from './MindMapCard';

export function validateFlowchart(value) {
  if (!value || typeof value.title !== 'string' || !value.title.trim() ||
      !Array.isArray(value.steps) || value.steps.length < 2 || value.steps.length > 8) return null;
  const steps = value.steps.map(step => {
    if (!step || typeof step.label !== 'string' || !step.label.trim() ||
        typeof step.detail !== 'string' || !step.detail.trim()) return null;
    return { label: step.label.trim().slice(0, 70), detail: step.detail.trim().slice(0, 320) };
  });
  if (steps.some(step => !step)) return null;
  return { title: value.title.trim().slice(0, 100),
    summary: typeof value.summary === 'string' ? value.summary.trim().slice(0, 240) : '', steps };
}
export function makeFlowchartPrompt(chapter, focus = '') {
  return 'Visualize: Flowchart for ' + chapter + (focus.trim() ? ' — focus: ' + focus.trim() : '') +
    '\n\n[FLOWCHART INSTRUCTIONS]\nUse only the active chapter and school sources. Analyze the chapter and organize a STUDY PATH: main idea, important concepts, source-supported examples or applications, then recap. Use a real process if the chapter contains one; otherwise sequence the learning, not imaginary real-world events. ' +
    'A descriptive chapter can still have a study flowchart. Label it a study path, so arrows mean study next rather than causes. Refuse only when there is no usable chapter material for the requested focus. ' +
    'Return only [FLOWCHART] valid JSON [/FLOWCHART]. Schema: {"title":"Process name","summary":"Purpose","steps":[{"label":"Step name","detail":"What happens and why"}]}. ' +
    'Use 3 to 8 steps. Every step must build on what the student learned previously. Do not falsely claim that categories or qualities cause one another. No questions, quizzes or other blocks.';
}
export default function FlowchartCard({ data }) {
  const [selected, setSelected] = useState(0);
  const marker = 'flow-arrow-' + useId().replace(/[^a-zA-Z0-9]/g, '');
  const chart = validateFlowchart(data);
  if (!chart) return <p role="alert" className="text-amber-300">The flowchart could not be read. Please request it again.</p>;
  const active = Math.min(selected, chart.steps.length - 1), height = chart.steps.length * 155 + 35;
  function download(event) {
    const svg = event.currentTarget.closest('[data-testid="flowchart-card"]').querySelector('svg').cloneNode(true);
    svg.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns', 'http://www.w3.org/2000/svg'); svg.setAttribute('width', '600'); svg.setAttribute('height', String(height));
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml' }));
    const link = document.createElement('a');
    link.href = url; link.download = (chart.title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 70) || 'chapter') + '-flowchart.svg';
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section data-testid="flowchart-card" className="my-3 rounded-2xl border border-violet-500/25 bg-zinc-950 overflow-hidden">
    <div className="p-4 flex flex-wrap items-center justify-between gap-2">
      <div><p className="text-violet-300 text-xs uppercase tracking-wider">Ace-it Visualize · Study Flowchart</p><h3 className="text-white font-bold mt-1">{chart.title}</h3></div>
      <button type="button" onClick={download} className="text-xs text-violet-300 border border-violet-500/30 rounded-lg px-3 py-2">Download SVG</button>
    </div>
    <p className="px-4 pb-2 text-xs text-violet-300">Arrows show the recommended learning order.</p>
    {chart.summary && <p className="px-4 pb-3 text-sm text-zinc-400">{chart.summary}</p>}
    <div className="overflow-x-auto max-h-[650px] overflow-y-auto">
      <svg viewBox={'0 0 600 ' + height} role="img" aria-label={'Flowchart: ' + chart.title} className="w-full min-w-[320px]" style={{ background: '#09090b' }}>
        <rect width="600" height={height} fill="#09090b" />
        <defs><marker id={marker} markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#a78bfa" /></marker></defs>
        {chart.steps.map((step, i) => {
          const y = 25 + i * 155;
          return <g key={i}>
            {i < chart.steps.length - 1 && <line x1="300" y1={y + 112} x2="300" y2={y + 146}
              stroke="#a78bfa" strokeWidth="2" markerEnd={'url(#' + marker + ')'} />}
            <g role="button" tabIndex={0} aria-label={'Step ' + (i + 1) + ': ' + step.label}
              style={{ cursor: 'pointer' }} onClick={() => setSelected(i)}
              onKeyDown={event => { if (['Enter', ' '].includes(event.key)) { event.preventDefault(); setSelected(i); } }}>
              <rect x="80" y={y} width="440" height="112" rx={i === 0 || i === chart.steps.length - 1 ? 38 : 14}
                fill={active === i ? '#2e1065' : '#18181b'} stroke={active === i ? '#c4b5fd' : '#7c3aed'} strokeWidth="2" />
              <text x="105" y={y + 22} fill="#a78bfa" fontSize="11" fontFamily="Arial, sans-serif">{i + 1}</text>
              {wrapVisualText(step.label, 43).slice(0, 2).map((line, j) => <text key={j} x="300" y={y + 31 + j * 18}
                textAnchor="middle" fill="#ede9fe" fontSize="15" fontFamily="Arial, sans-serif">{line}</text>)}
              {wrapVisualText(step.detail, 58).slice(0, 2).map((line, j) => <text key={'detail-' + j} x="300" y={y + 78 + j * 14}
                textAnchor="middle" fill="#a1a1aa" fontSize="11" fontFamily="Arial, sans-serif">{line}</text>)}
            </g>
          </g>;
        })}
      </svg>
    </div>
    <div className="p-4 border-t border-white/10">
      <p className="text-xs text-zinc-400 mb-3">Choose a step for its full explanation.</p>
      <div className="flex flex-wrap gap-2 mb-3">{chart.steps.map((step, i) =>
        <button type="button" key={i} aria-pressed={active === i} onClick={() => setSelected(i)}
          className={'rounded-lg px-3 py-2 text-xs border ' + (active === i ? 'bg-violet-500/20 border-violet-400 text-violet-200' : 'border-white/10 text-zinc-400')}>{i + 1}. {step.label}</button>)}</div>
      <h4 className="text-white font-semibold mb-2">{chart.steps[active].label}</h4>
      <p className="text-zinc-300 text-sm">{chart.steps[active].detail}</p>
    </div>
  </section>;
}

