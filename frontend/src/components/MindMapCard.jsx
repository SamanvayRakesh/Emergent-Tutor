import { useState } from 'react';

const COLORS = ['#22d3ee', '#a78bfa', '#34d399', '#fbbf24', '#fb7185', '#60a5fa'];
const clean = (value, limit) => typeof value === 'string' ? value.trim().slice(0, limit) : '';
export function validateMindMap(value) {
  if (!value || !Array.isArray(value.branches) || !clean(value.title, 100)) return null;
  if (!value.branches.length || value.branches.length > 6) return null;
  const branches = value.branches.map(branch => {
    if (!branch || !clean(branch.label, 60) || !Array.isArray(branch.points)) return null;
    return { label: clean(branch.label, 60), relation: clean(branch.relation, 24) || 'includes',
      points: branch.points.filter(p => typeof p === 'string' && p.trim()).slice(0, 4).map(p => clean(p, 220)) };
  });
  if (branches.some(branch => !branch || !branch.points.length)) return null;
  return { title: clean(value.title, 100), summary: clean(value.summary, 240), branches };
}
export function makeMindMapPrompt(chapter, focus = '') {
  return 'Visualize: Mind map for ' + chapter + (focus.trim() ? ' — focus: ' + focus.trim() : '') +
    '\n\n[MINDMAP INSTRUCTIONS]\nExplain in detail using ONLY the available material for this session’s chapter and school. ' +
    'If the source does not support the requested topic, say so in plain text instead of inventing a map. ' +
    'Otherwise return ONLY [MINDMAP] followed by valid JSON and [/MINDMAP]. ' +
    'Schema: {"title":"Chapter title","summary":"One sentence linking the concepts","branches":[{"label":"Short topic name","relation":"causes / uses / includes","points":["Specific fact","Chapter example"]}]}. ' +
    'Use 3 to 6 branches, at most 4 concise points per branch, no Markdown inside JSON strings. ' +
    'Prioritize the requested focus, not a generic chapter overview. Choose distinct concepts, explicit relationships, precise facts and one source-supported example per branch where available. Avoid repetitive vague statements. No questions, quizzes, or other blocks.';
}
export function wrapVisualText(text, width = 23) {
  const words = text.split(/\s+/), result = [''];
  for (const word of words) {
    const i = result.length - 1;
    if (result[i] && (result[i] + ' ' + word).length > width) result.push(word);
    else result[i] += (result[i] ? ' ' : '') + word;
  }
  return result.slice(0, 3).map((line, i) => i === 2 && result.length > 3 ? line + '…' : line);
}
export default function MindMapCard({ data }) {
  const [selected, setSelected] = useState(0);
  const map = validateMindMap(data);
  if (!map) return <p role="alert" className="text-amber-300">The mind map could not be read. Please request it again.</p>;
  const active = Math.min(selected, map.branches.length - 1);
  const maxPoints = Math.max(...map.branches.map(branch => branch.points.length));
  const rowHeight = maxPoints * 98 + 68;
  const rows = Math.ceil(map.branches.length / 2), height = rows * rowHeight + 40;
  const centerY = height / 2;
  const positions = map.branches.map((_, i) => ({ left: i % 2 === 0,
    x: i % 2 === 0 ? 350 : 930, y: 20 + rowHeight * (Math.floor(i / 2) + 0.5) }));
  const curve = (x1, y1, x2, y2) => 'M' + x1 + ',' + y1 + ' C' + ((x1 + x2) / 2) + ',' + y1 + ' ' +
    ((x1 + x2) / 2) + ',' + y2 + ' ' + x2 + ',' + y2;
  function download(event) {
    const copy = event.currentTarget.closest('[data-testid="mind-map-card"]').querySelector('svg').cloneNode(true);
    copy.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns', 'http://www.w3.org/2000/svg');
    copy.setAttribute('width', '1280'); copy.setAttribute('height', String(height));
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)], { type: 'image/svg+xml' }));
    const link = document.createElement('a');
    link.href = url; link.download = (map.title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 70) || 'chapter') + '-mind-map.svg';
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section data-testid="mind-map-card" className="my-3 rounded-2xl border border-cyan-500/25 bg-zinc-950 overflow-hidden">
    <div className="p-4 flex flex-wrap items-center justify-between gap-2">
      <div><p className="text-cyan-300 text-xs uppercase tracking-wider">Ace-it Visualize · Mind Map</p>
        <h3 className="text-white font-bold mt-1">{map.title}</h3></div>
      <button type="button" onClick={download} className="text-xs text-cyan-300 border border-cyan-500/30 rounded-lg px-3 py-2">Download SVG</button>
    </div>
    {map.summary && <p className="px-4 pb-3 text-sm text-zinc-400">{map.summary}</p>}
    <p className="px-4 pb-2 text-xs text-zinc-500">Topic → concept groups → key points. Scroll to explore the full map.</p>
    <div className="overflow-auto max-h-[650px]">
      <svg viewBox={'0 0 1280 ' + height} role="img" aria-label={'Mind map: ' + map.title}
        className="w-full min-w-[960px]" style={{ background: '#09090b' }}>
        <rect width="1280" height={height} fill="#09090b" />
        {positions.map((p, i) => <path key={'main-link-' + i}
          d={curve(p.left ? 530 : 750, centerY, p.left ? 440 : 840, p.y)}
          fill="none" stroke={COLORS[i]} strokeWidth="3" opacity="0.7" />)}
        {map.branches.map((branch, i) => branch.points.map((point, j) => {
          const p = positions[i], y = p.y + (j - (branch.points.length - 1) / 2) * 98;
          return <path key={'point-link-' + i + '-' + j} d={curve(p.left ? 260 : 1020, p.y, p.left ? 230 : 1050, y)}
            fill="none" stroke={COLORS[i]} strokeWidth="1.5" opacity="0.45" />;
        }))}
        <rect x="530" y={centerY - 60} width="220" height="120" rx="28" fill="#164e63" stroke="#22d3ee" strokeWidth="2" />
        <text x="640" y={centerY - 34} textAnchor="middle" fill="#67e8f9" fontSize="10" letterSpacing="2" fontFamily="Arial, sans-serif">MAIN TOPIC</text>
        {wrapVisualText(map.title, 24).map((line, i, all) => <text key={i} x="640" y={centerY + 7 + (i - (all.length - 1) / 2) * 20}
          textAnchor="middle" fill="#ecfeff" fontSize="16" fontWeight="bold" fontFamily="Arial, sans-serif">{line}</text>)}
        {map.branches.map((branch, i) => {
          const p = positions[i];
          return <g key={i}>
            <g role="button" tabIndex={0} aria-label={'Explore ' + branch.label} style={{ cursor: 'pointer' }}
              onClick={() => setSelected(i)} onKeyDown={event => { if (['Enter', ' '].includes(event.key)) { event.preventDefault(); setSelected(i); } }}>
              <rect x={p.x - 90} y={p.y - 54} width="180" height="108" rx="18"
                fill={active === i ? '#27272a' : '#18181b'} stroke={COLORS[i]} strokeWidth={active === i ? 3 : 1.5} />
              <text x={p.x} y={p.y - 33} textAnchor="middle" fill={COLORS[i]} fontSize="10" fontFamily="Arial, sans-serif">{branch.relation}</text>
              {wrapVisualText(branch.label, 20).map((line, j, all) => <text key={j} x={p.x} y={p.y + 7 + (j - (all.length - 1) / 2) * 18}
                textAnchor="middle" fill="#f4f4f5" fontSize="14" fontWeight="bold" fontFamily="Arial, sans-serif">{line}</text>)}
            </g>
            {branch.points.map((point, j) => {
              const x = p.left ? 120 : 1160, y = p.y + (j - (branch.points.length - 1) / 2) * 98;
              return <g key={j}>
                <rect x={x - 110} y={y - 42} width="220" height="84" rx="14" fill="#121216" stroke={COLORS[i]} strokeOpacity="0.35" />
                {wrapVisualText(point, 32).map((line, k, all) => <text key={k} x={x} y={y + 4 + (k - (all.length - 1) / 2) * 16}
                  textAnchor="middle" fill="#d4d4d8" fontSize="12" fontFamily="Arial, sans-serif">{line}</text>)}
              </g>;
            })}
          </g>;
        })}
      </svg>
    </div>
    <div className="p-4 border-t border-white/10">
      <div className="flex flex-wrap gap-2 mb-4">{map.branches.map((branch, i) =>
        <button type="button" key={i} aria-pressed={active === i} onClick={() => setSelected(i)}
          className="rounded-lg border px-3 py-2 text-xs" style={{ color: COLORS[i], borderColor: COLORS[i],
            background: active === i ? '#27272a' : 'transparent' }}>{branch.label}</button>)}</div>
      <h4 className="font-semibold text-white mb-2">{map.branches[active].label}</h4>
      <ul className="list-disc pl-5 text-zinc-300 space-y-2 text-sm">
        {map.branches[active].points.map((point, i) => <li key={i}>{point}</li>)}
      </ul>
    </div>
  </section>;
}

