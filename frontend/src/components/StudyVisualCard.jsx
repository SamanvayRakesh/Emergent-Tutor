import { useId, useRef, useState } from 'react';

export const STUDY_FORMATS = [
  { id: 'graph', label: 'Graph' },
  { id: 'cheatsheet', label: 'PDF Cheat Sheet' },
  { id: 'notes', label: 'Revision Notes' },
  { id: 'keypoints', label: 'Key Points' },
  { id: 'quickrevision', label: 'Quick Revision' },
];
const VISUAL_TYPES = ['concept', 'steps', 'compare', 'formula', 'timeline', 'cycle'];
const text = (v, max = 1600) => typeof v === 'string' && Boolean(v.trim()) && v.length <= max;
const number = v => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) <= 1e12;
const list = (v, max, check) => Array.isArray(v) && v.length > 0 && v.length <= max && v.every(check);

function validateTopicVisual(v) {
  if (!v || !VISUAL_TYPES.includes(v.type) || !text(v.title, 140) ||
      (!Array.isArray(v.items) || v.items.length < 2) || !list(v.items, 8, item => item && text(item.label, 90) && text(item.detail, 700))) return null;
  return { type: v.type, title: v.title.trim(), items: v.items.map(item => ({ label: item.label.trim(), detail: item.detail.trim() })) };
}

export function validateStudyVisual(d) {
  if (!d || !STUDY_FORMATS.some(f => f.id === d.kind) || !text(d.title, 160) || !text(d.summary, 1200)) return null;
  const base = { kind: d.kind, title: d.title.trim(), summary: d.summary.trim() };
  if (d.kind === 'graph') {
    if (!['bar', 'line', 'scatter'].includes(d.chartType) || !text(d.xLabel, 120) || !text(d.yLabel, 120) ||
        !text(d.basis, 1200) || typeof d.illustrative !== 'boolean' ||
        !list(d.points, 64, p => p && text(p.label, 90) && number(p.y) && (d.chartType === 'bar' || number(p.x)))) return null;
    if (d.points.length < 2 || (d.chartType !== 'bar' && new Set(d.points.map(p => p.x)).size < 2)) return null;
    return { ...base, chartType: d.chartType, xLabel: d.xLabel, yLabel: d.yLabel, illustrative: d.illustrative,
      basis: d.basis, points: (d.chartType === 'bar' ? d.points : [...d.points].sort((a, b) => a.x - b.x)).map(p =>
        ({ label: p.label, x: p.x, y: p.y, detail: text(p.detail, 700) ? p.detail : '' })) };
  }
  if (!list(d.sections, 40, s => s && text(s.heading, 160) && list(s.points, 10, p => text(p)))) return null;
  const sections = d.sections.map((s, i) => {
    // Older saved replies remain usable, with an interactive concept view.
    const visual = s.visual ? validateTopicVisual(s.visual) : {
      type: i % 2 ? 'compare' : 'concept', title: s.heading,
      items: s.points.slice(0, 8).map((p, j) => ({ label: `Key idea ${j + 1}`, detail: p })),
    };
    return visual && { heading: s.heading.trim(), points: s.points.map(p => p.trim()), visual,
      recall: s.recall && text(s.recall.question, 500) && text(s.recall.answer, 1000) ? s.recall : null };
  });
  if (sections.some(s => !s)) return null;
  let coverage = null;
  if (d.coverage) {
    if (!['complete', 'partial'].includes(d.coverage.status) || !text(d.coverage.note, 800) ||
        !list(d.coverage.topics, 40, topic => text(topic, 160))) return null;
    const headings = new Set(sections.map(s => s.heading.toLowerCase()));
    if (d.coverage.status === 'complete' && d.coverage.topics.some(t => !headings.has(t.trim().toLowerCase()))) return null;
    coverage = { status: d.coverage.status, note: d.coverage.note, topics: d.coverage.topics };
  }
  return { ...base, sections, coverage };
}

export function makeStudyVisualPrompt(chapter, focus, kind) {
  const label = STUDY_FORMATS.find(f => f.id === kind)?.label;
  if (!label) throw new Error('Unknown study format');
  return `Visualize: ${label} for ${chapter}${focus?.trim() ? `\nFocus: ${focus.trim()}` : ''}\n\n[STUDYVISUAL INSTRUCTIONS]\nReturn [STUDYVISUAL] valid JSON [/STUDYVISUAL]. Use the active chapter and school sources. ${kind === 'cheatsheet' ? 'Cover EVERY teaching topic in the chapter, even when a focus is supplied; give that focus extra attention. Give each topic its own useful visual with specific labels and explanations.' : 'Respect the requested focus; otherwise cover the chapter.'} For graphs use source data or clearly labelled examples derived from source formulas. Never invent statistics or relationships. Include topic-specific interactive visual data and recall questions in notes. Plain Unicode text in JSON, without HTML or LaTeX.`;
}

function filename(title, ext) {
  return `${title.replace(/[^a-z0-9_-]/gi, '-').replace(/-+/g, '-').slice(0, 90) || 'ace-it-study'}.${ext}`;
}
function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function saveSvg(svg, title) {
  if (!svg) return;
  const copy = svg.cloneNode(true);
  copy.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns', 'http://www.w3.org/2000/svg');
  saveBlob(new Blob([new XMLSerializer().serializeToString(copy)], { type: 'image/svg+xml' }), filename(title, 'svg'));
}
export function wrapText(value, maxChars = 24) {
  const lines = []; let line = '';
  for (const word of String(value).split(/\s+/)) {
    if (line && line.length + word.length + 1 > maxChars) { lines.push(line); line = ''; }
    for (let offset = 0; offset < word.length; offset += maxChars) {
      const piece = word.slice(offset, offset + maxChars);
      if (offset) { if (line) lines.push(line); line = piece; }
      else line = line ? `${line} ${piece}` : piece;
    }
  }
  if (line) lines.push(line);
  return lines;
}

// Shared by the interactive SVG and the PDF; no duplicated diagram interpretation.
export function topicLayout(visual) {
  const count = visual.items.length;
  if (visual.type === 'cycle') {
    const nodes = visual.items.map((item, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / count;
      return { ...item, x: 350 + 225 * Math.cos(a), y: 210 + 145 * Math.sin(a), w: 150, h: 72 };
    });
    return { width: 700, height: 420, nodes, edges: nodes.map((_, i) => [i, (i + 1) % count]) };
  }
  if (visual.type === 'concept') {
    const nodes = visual.items.map((item, i) => ({ ...item, x: i % 2 ? 565 : 135,
      y: 75 + Math.floor(i / 2) * 100, w: 220, h: 78 }));
    return { width: 700, height: Math.ceil(count / 2) * 100 + 50, nodes, edges: [], hub: true };
  }
  const sequential = ['steps', 'timeline'].includes(visual.type);
  const nodes = visual.items.map((item, i) => ({ ...item, x: sequential ? 350 : (i % 2 ? 520 : 180),
    y: 55 + (sequential ? i : Math.floor(i / 2)) * 105, w: sequential ? 490 : 300, h: 80 }));
  return { width: 700, height: (sequential ? count : Math.ceil(count / 2)) * 105 + 10, nodes,
    edges: sequential ? nodes.slice(1).map((_, i) => [i, i + 1]) : [] };
}
function edgeEnds(a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const radius = node => Math.min(Math.abs(dx) < 0.001 ? Infinity : node.w / 2 / Math.abs(dx),
    Math.abs(dy) < 0.001 ? Infinity : node.h / 2 / Math.abs(dy));
  const start = radius(a), end = radius(b);
  return [a.x + dx * start, a.y + dy * start, b.x - dx * end, b.y - dy * end];
}
function TopicVisual({ visual }) {
  const [selected, setSelected] = useState(0), svgRef = useRef(null);
  const arrow = `ace-topic-${useId().replace(/[^a-z0-9]/gi, '')}`;
  const layout = topicLayout(visual), active = Math.min(selected, visual.items.length - 1);
  return <div className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950 p-3" data-testid="topic-visual">
    <div className="flex items-center justify-between gap-3">
      <p className="text-sm text-cyan-200 font-semibold">{visual.title}</p>
      <button type="button" onClick={() => saveSvg(svgRef.current, visual.title)} className="shrink-0 text-xs text-cyan-300">Save SVG</button>
    </div>
    <div className="overflow-auto max-h-[440px] mt-2">
      <svg ref={svgRef} viewBox={`0 0 ${layout.width} ${layout.height}`} className="w-full min-w-[540px]"
        role="group" aria-label={`${visual.type}: ${visual.title}`} style={{ background: '#09090b' }}>
        <title>{visual.title}</title><rect width={layout.width} height={layout.height} fill="#09090b" />
        <defs><marker id={arrow} markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#67e8f9" /></marker></defs>
        {layout.hub && <><circle cx="350" cy={layout.height / 2} r="38" fill="#164e63" stroke="#22d3ee" />
          <text x="350" y={layout.height / 2 + 5} textAnchor="middle" fill="#cffafe" fontSize="14">Concept</text></>}
        {layout.hub && layout.nodes.map((n, i) => <line key={`hub-${i}`} x1="350" y1={layout.height / 2}
          x2={n.x} y2={n.y} stroke="#155e75" strokeWidth="2" />)}
        {layout.edges.map(([a, b], i) => {
          const [x1, y1, x2, y2] = edgeEnds(layout.nodes[a], layout.nodes[b]);
          return <line key={`edge-${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#67e8f9" strokeWidth="2" markerEnd={`url(#${arrow})`} />;
        })}
        {layout.nodes.map((n, i) => <g key={i} role="button" tabIndex={0} aria-pressed={active === i}
          aria-label={n.label} onClick={() => setSelected(i)}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected(i); } }} style={{ cursor: 'pointer' }}>
          <rect x={n.x - n.w / 2} y={n.y - n.h / 2} width={n.w} height={n.h} rx={visual.type === 'formula' ? 6 : 14}
            fill={active === i ? '#164e63' : '#18181b'} stroke={active === i ? '#67e8f9' : '#3f3f46'} strokeWidth="2" />
          <title>{n.detail}</title>
          {wrapText(n.label, visual.type === 'cycle' ? 17 : (n.w > 400 ? 48 : 27)).slice(0, 3).map((line, j, all) =>
            <text key={j} x={n.x} y={n.y + 5 + (j - (all.length - 1) / 2) * 18} textAnchor="middle" fill="#e4e4e7" fontSize="14" fontFamily="Arial, sans-serif">{line}</text>)}
        </g>)}
      </svg>
    </div>
    <div className="mt-3 flex flex-wrap gap-2" aria-label="Explore topic details">
      {visual.items.map((item, i) => <button type="button" key={i} aria-pressed={active === i} onClick={() => setSelected(i)}
        className={`rounded-lg border px-3 py-2 text-xs ${active === i ? 'border-cyan-400 bg-cyan-500/15 text-cyan-200' : 'border-white/10 text-zinc-300'}`}>{item.label}</button>)}
    </div>
    <div aria-live="polite" className="mt-3 text-sm text-zinc-300"><p className="font-semibold text-cyan-100">{visual.items[active].label}</p><p className="mt-1 whitespace-pre-wrap">{visual.items[active].detail}</p></div>
  </div>;
}

export function graphGeometry(points, chartType, range = [0, points.length - 1]) {
  const shown = points.slice(range[0], range[1] + 1), left = 95, right = 650, top = 55, bottom = 310;
  let low = Math.min(...shown.map(p => p.y)), high = Math.max(...shown.map(p => p.y));
  if (chartType === 'bar') { low = Math.min(0, low); high = Math.max(0, high); }
  const pad = high === low ? Math.max(1, Math.abs(low) * 0.1) : (high - low) * 0.1;
  low -= pad; high += pad;
  const minX = Math.min(...shown.map(p => p.x || 0)), maxX = Math.max(...shown.map(p => p.x || 0));
  const y = value => bottom - (value - low) / (high - low) * (bottom - top);
  const x = (p, i) => chartType === 'bar' ? left + (i + 0.5) * (right - left) / shown.length :
    left + 8 + (p.x - minX) / (maxX - minX || 1) * (right - left - 16);
  return { shown, low, high, minX, maxX, left, right, top, bottom, x, y };
}
const formatNumber = v => new Intl.NumberFormat('en', { maximumSignificantDigits: 5 }).format(v);
function GraphVisual({ data: d }) {
  const [selected, setSelected] = useState(0), [table, setTable] = useState(false), [connect, setConnect] = useState(true);
  const [range, setRange] = useState([0, d.points.length - 1]), svgRef = useRef(null);
  const g = graphGeometry(d.points, d.chartType, range), active = Math.max(range[0], Math.min(selected, range[1]));
  const p = d.points[active], isBar = d.chartType === 'bar';
  const chooseRange = (start, end) => { setRange([start, end]); setSelected(old => Math.max(start, Math.min(old, end))); };
  return <div data-testid="study-graph">
    <p className="my-3 text-xs text-amber-200">{d.illustrative ? 'Illustrative example — not measured data' : 'Chapter data'} · {d.basis}</p>
    <div className="flex flex-wrap items-center gap-3 mb-3">
      <button type="button" className="rounded-lg border border-white/10 px-3 py-2 text-xs text-cyan-200" onClick={() => saveSvg(svgRef.current, d.title)}>Download SVG</button>
      <button type="button" aria-expanded={table} onClick={() => setTable(v => !v)} className="rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300">{table ? 'Hide values' : 'Show exact values'}</button>
      {d.chartType === 'line' && <label className="flex gap-2 items-center text-xs text-zinc-300"><input type="checkbox" checked={connect} onChange={e => setConnect(e.target.checked)} />Connect points</label>}
    </div>
    <div className="overflow-x-auto">
      <svg ref={svgRef} viewBox="0 0 720 435" className="w-full min-w-[540px]" role="group" aria-label={`${d.title}: ${d.xLabel} versus ${d.yLabel}`} style={{ background: '#09090b' }}>
        <title>{d.title}</title><desc>{d.summary} Choose a point to see its exact value.</desc><rect width="720" height="435" fill="#09090b" />
        {[0, 1, 2, 3, 4].map(i => { const v = g.low + i * (g.high - g.low) / 4; return <g key={i}>
          <line x1={g.left} x2={g.right} y1={g.y(v)} y2={g.y(v)} stroke="#27272a" />
          <text x={g.left - 10} y={g.y(v) + 4} textAnchor="end" fill="#a1a1aa" fontSize="12">{formatNumber(v)}</text></g>; })}
        <path d={`M${g.left} ${g.top} V${g.bottom} H${g.right}`} fill="none" stroke="#71717a" />
        {g.low < 0 && g.high > 0 && <line x1={g.left} x2={g.right} y1={g.y(0)} y2={g.y(0)} stroke="#52525b" />}
        {d.chartType === 'line' && connect && <polyline points={g.shown.map((point, i) => `${g.x(point, i)},${g.y(point.y)}`).join(' ')} fill="none" stroke="#22d3ee" strokeWidth="2" />}
        {g.shown.map((point, i) => {
          const original = range[0] + i, cx = g.x(point, i), cy = g.y(point.y), width = Math.min(44, 360 / g.shown.length);
          return <g key={original} role="button" tabIndex={0} aria-pressed={active === original}
            aria-label={`${point.label}: ${isBar ? '' : `${d.xLabel} ${point.x}, `}${d.yLabel} ${point.y}`}
            onClick={() => setSelected(original)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected(original); } }} style={{ cursor: 'pointer' }}>
            <title>{point.label}: {point.y}</title>
            {isBar ? <rect x={cx - width / 2} y={Math.min(cy, g.y(0))} width={width} height={Math.max(2, Math.abs(cy - g.y(0)))} fill={active === original ? '#a78bfa' : '#22d3ee'} /> :
              <circle cx={cx} cy={cy} r={active === original ? 7 : 5} fill={active === original ? '#a78bfa' : '#22d3ee'} />}
            <circle cx={cx} cy={cy} r="18" fill="transparent" />
            {(g.shown.length <= 12 || i % Math.ceil(g.shown.length / 8) === 0 || i === g.shown.length - 1) &&
              <text transform={`translate(${cx},329) rotate(25)`} fill="#a1a1aa" fontSize="11" textAnchor="middle">{isBar ? point.label.slice(0, 16) : formatNumber(point.x)}</text>}
          </g>;
        })}
        {wrapText(d.xLabel, 60).slice(0, 2).map((line, i) => <text key={i} x="375" y={395 + i * 16} textAnchor="middle" fill="#e4e4e7" fontSize="13">{line}</text>)}
        <text transform="translate(20,185) rotate(-90)" textAnchor="middle" fill="#e4e4e7" fontSize="13">{d.yLabel.slice(0, 44)}</text>
      </svg>
    </div>
    <div className="mt-3 rounded-xl bg-zinc-900 p-3 text-sm text-zinc-300" aria-live="polite">
      <label className="block text-xs text-zinc-400 mb-2">Explore a point <select className="ml-2 max-w-full rounded-lg bg-zinc-950 border border-white/10 px-2 py-1 text-zinc-200" value={active} onChange={e => setSelected(Number(e.target.value))}>
        {g.shown.map((point, i) => <option key={i} value={range[0] + i}>{point.label}</option>)}</select></label>
      <p className="text-cyan-200">{p.label}: {!isBar && `${d.xLabel} = ${formatNumber(p.x)} · `}{d.yLabel} = {formatNumber(p.y)}</p>
      {p.detail && <p className="mt-1">{p.detail}</p>}
    </div>
    {d.points.length > 2 && <div className="mt-3 grid gap-2 sm:grid-cols-2 text-xs text-zinc-300">
      <label>Range start: {d.points[range[0]].label}<input aria-label="Graph range start" type="range" className="block w-full accent-cyan-400" min="0" max={range[1] - 1} value={range[0]} onChange={e => chooseRange(Number(e.target.value), range[1])} /></label>
      <label>Range end: {d.points[range[1]].label}<input aria-label="Graph range end" type="range" className="block w-full accent-cyan-400" min={range[0] + 1} max={d.points.length - 1} value={range[1]} onChange={e => chooseRange(range[0], Number(e.target.value))} /></label>
      <button type="button" onClick={() => chooseRange(0, d.points.length - 1)} className="text-left text-cyan-300">Reset range</button>
    </div>}
    {table && <div className="overflow-auto mt-3"><table className="w-full text-xs text-zinc-300"><caption className="text-left mb-2">Exact chapter values</caption><thead><tr><th className="text-left">Label</th>{!isBar && <th>{d.xLabel}</th>}<th>{d.yLabel}</th></tr></thead><tbody>
      {d.points.map((point, i) => <tr key={i} className="border-t border-white/5"><td className="py-2">{point.label}</td>{!isBar && <td className="text-center">{point.x}</td>}<td className="text-center">{point.y}</td></tr>)}
    </tbody></table></div>}
  </div>;
}

// Page images preserve Unicode and diagrams without adding a PDF dependency.
export function pdfFromJpegs(images) {
  if (!images.length) throw new Error('No revision pages to export.');
  const enc = new TextEncoder(), chunks = [], offsets = [0]; let length = 0;
  const put = value => { const b = typeof value === 'string' ? enc.encode(value) : value; chunks.push(b); length += b.length; };
  const obj = (id, content) => { offsets[id] = length; put(`${id} 0 obj\n${content}\nendobj\n`); };
  put('%PDF-1.4\n'); obj(1, '<< /Type /Catalog /Pages 2 0 R >>');
  obj(2, `<< /Type /Pages /Count ${images.length} /Kids [${images.map((_, i) => `${3 + i * 3} 0 R`).join(' ')}] >>`);
  images.forEach((bytes, i) => {
    const id = 3 + i * 3;
    obj(id, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /XObject << /Im${i} ${id + 1} 0 R >> >> /Contents ${id + 2} 0 R >>`);
    offsets[id + 1] = length; put(`${id + 1} 0 obj\n<< /Type /XObject /Subtype /Image /Width 1190 /Height 1684 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${bytes.length} >>\nstream\n`);
    put(bytes); put('\nendstream\nendobj\n');
    const command = `q 595 0 0 842 0 0 cm /Im${i} Do Q`;
    obj(id + 2, `<< /Length ${enc.encode(command).length} >>\nstream\n${command}\nendstream`);
  });
  const start = length; put(`xref\n0 ${offsets.length}\n0000000000 65535 f \n`);
  offsets.slice(1).forEach(offset => put(`${String(offset).padStart(10, '0')} 00000 n \n`));
  put(`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`);
  return new Blob(chunks, { type: 'application/pdf' });
}

export async function makeStudyPdf(data) {
  const d = validateStudyVisual(data);
  if (!d || d.kind === 'graph') throw new Error('Choose chapter notes or a cheat sheet to export a PDF.');
  if (document.fonts?.ready) await document.fonts.ready;
  const images = []; let canvas, ctx, y, page = 0;
  const newPage = () => {
    canvas = document.createElement('canvas'); canvas.width = 1190; canvas.height = 1684;
    ctx = canvas.getContext('2d'); if (!ctx) throw new Error('PDF rendering is unavailable in this browser.');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 1190, 1684);
    ctx.fillStyle = '#0e7490'; ctx.font = 'bold 24px Arial'; ctx.fillText('ACE-IT • CHAPTER REVISION', 72, 66);
    ctx.fillStyle = '#64748b'; ctx.font = '20px Arial'; ctx.fillText(`Page ${++page}`, 1020, 1620); y = 125;
  };
  const finish = () => {
    const raw = atob(canvas.toDataURL('image/jpeg', 0.94).split(',')[1]);
    images.push(Uint8Array.from(raw, c => c.charCodeAt(0)));
  };
  const ensure = height => { if (y + height > 1550) { finish(); newPage(); } };
  const line = (value, size = 24, bold = false, color = '#1e293b') => {
    const font = `${bold ? 'bold ' : ''}${size}px Arial`;
    ctx.font = font; let current = '';
    const flush = () => { ensure(size * 1.5); ctx.font = font; ctx.fillStyle = color; ctx.fillText(current.trimEnd(), 72, y); y += size * 1.5; current = ''; };
    for (const paragraph of String(value).split('\n')) {
      for (const word of paragraph.split(/\s+/)) {
        const candidate = current ? `${current} ${word}` : word;
        if (ctx.measureText(candidate).width <= 1046) { current = candidate; continue; }
        if (current) flush();
        for (const c of word) { if (ctx.measureText(current + c).width > 1046) flush(); current += c; }
      }
      if (current) flush();
    }
  };
  const drawVisual = visual => {
    const layout = topicLayout(visual), scale = Math.min(1046 / layout.width, 620 / layout.height);
    const height = layout.height * scale;
    ensure(height + 30); ctx.save(); ctx.translate(72 + (1046 - layout.width * scale) / 2, y); ctx.scale(scale, scale);
    ctx.lineWidth = 2; ctx.strokeStyle = '#0891b2';
    const arrow = (x1, y1, x2, y2) => {
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      const angle = Math.atan2(y2 - y1, x2 - x1); ctx.beginPath(); ctx.moveTo(x2, y2);
      ctx.lineTo(x2 - 9 * Math.cos(angle - 0.5), y2 - 9 * Math.sin(angle - 0.5));
      ctx.lineTo(x2 - 9 * Math.cos(angle + 0.5), y2 - 9 * Math.sin(angle + 0.5)); ctx.closePath(); ctx.fillStyle = '#0891b2'; ctx.fill();
    };
    if (layout.hub) {
      layout.nodes.forEach(n => { ctx.beginPath(); ctx.moveTo(350, layout.height / 2); ctx.lineTo(n.x, n.y); ctx.stroke(); });
      ctx.beginPath(); ctx.arc(350, layout.height / 2, 38, 0, Math.PI * 2); ctx.fillStyle = '#cffafe'; ctx.fill(); ctx.stroke();
      ctx.font = '14px Arial'; ctx.textAlign = 'center'; ctx.fillStyle = '#164e63'; ctx.fillText('Concept', 350, layout.height / 2 + 5);
    }
    layout.edges.forEach(([a, b]) => arrow(...edgeEnds(layout.nodes[a], layout.nodes[b])));
    layout.nodes.forEach(n => {
      ctx.fillStyle = '#ecfeff'; ctx.fillRect(n.x - n.w / 2, n.y - n.h / 2, n.w, n.h);
      ctx.strokeStyle = '#0891b2'; ctx.strokeRect(n.x - n.w / 2, n.y - n.h / 2, n.w, n.h);
      ctx.fillStyle = '#164e63'; ctx.font = '15px Arial'; ctx.textAlign = 'center';
      const lines = wrapText(n.label, visual.type === 'cycle' ? 17 : (n.w > 400 ? 48 : 27)).slice(0, 3);
      lines.forEach((value, i) => ctx.fillText(value, n.x, n.y + 5 + (i - (lines.length - 1) / 2) * 18));
    });
    ctx.restore(); y += height + 25;
  };
  newPage(); line(d.title, 36, true); line(d.summary); y += 15;
  if (d.coverage) { line(`${d.coverage.status === 'complete' ? 'Chapter coverage' : 'Partial source coverage'}: ${d.coverage.note}`, 21, false, '#0e7490'); y += 15; }
  line('Topic index', 28, true); d.sections.forEach((s, i) => line(`${i + 1}. ${s.heading}`, 22)); y += 25;
  for (const [i, section] of d.sections.entries()) {
    ensure(170); line(`${i + 1}. ${section.heading}`, 29, true, '#0e7490');
    section.points.forEach(point => line(`• ${point}`)); y += 15;
    line(section.visual.title, 23, true); drawVisual(section.visual);
    // Export every explanation, including details hidden behind interactive nodes.
    section.visual.items.forEach(item => { line(item.label, 23, true); line(item.detail, 22); });
    if (section.recall) { line(`Recall: ${section.recall.question}`, 23, true); line(`Answer: ${section.recall.answer}`, 22); }
    y += 30;
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  finish(); return pdfFromJpegs(images);
}

function ChapterVisual({ data: d, preview = false }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [reviewed, setReviewed] = useState({});
  const [revealed, setRevealed] = useState({}), refs = useRef([]);
  const download = async () => {
    setBusy(true); setError('');
    try { saveBlob(await makeStudyPdf(d), filename(d.title, 'pdf')); }
    catch (e) { setError(e.message || 'PDF export failed. Please retry.'); }
    finally { setBusy(false); }
  };
  return <>
    <div className="flex items-center justify-between gap-3 mt-3">
      <p className="text-xs text-zinc-400" aria-live="polite">{Object.values(reviewed).filter(Boolean).length} / {d.sections.length} topics reviewed</p>
      <button type="button" disabled={busy || preview} onClick={download} className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-200 disabled:opacity-40">{preview ? 'PDF available when complete' : busy ? 'Preparing PDF…' : 'Download PDF'}</button>
    </div>
    {error && <p role="alert" className="mt-2 text-amber-300">{error}</p>}
    {d.coverage && <p className={`mt-3 text-xs ${d.coverage.status === 'partial' ? 'text-amber-200' : 'text-zinc-400'}`}>{d.coverage.status === 'partial' ? 'Partial source coverage: ' : ''}{d.coverage.note}</p>}
    <nav aria-label="Chapter topics" className="my-3 flex flex-wrap gap-2">
      {d.sections.map((s, i) => <button type="button" key={i} onClick={() => { refs.current[i]?.scrollIntoView({ behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' }); refs.current[i]?.focus({ preventScroll: true }); }}
        className="rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300">{i + 1}. {s.heading}</button>)}
    </nav>
    <div className="space-y-4">
      {d.sections.map((s, i) => <article key={i} ref={el => { refs.current[i] = el; }} tabIndex={-1} className="rounded-xl bg-zinc-900/70 border border-white/5 p-4 outline-none focus:ring-2 focus:ring-cyan-500/40">
        <div className="flex items-start justify-between gap-3"><h4 className="text-cyan-100 font-semibold">{i + 1}. {s.heading}</h4>
          <label className="flex shrink-0 items-center gap-2 text-xs text-zinc-400"><input type="checkbox" checked={Boolean(reviewed[i])} onChange={e => setReviewed(v => ({ ...v, [i]: e.target.checked }))} />Reviewed</label></div>
        {d.kind === 'quickrevision' && <button type="button" aria-expanded={Boolean(revealed[i])} className="mt-3 text-xs text-cyan-300" onClick={() => setRevealed(v => ({ ...v, [i]: !v[i] }))}>{revealed[i] ? 'Hide answer' : 'Reveal answer'}</button>}
        {(d.kind !== 'quickrevision' || revealed[i]) && <><ul className="list-disc pl-5 mt-3 space-y-2 text-sm text-zinc-300">{s.points.map((point, j) => <li key={j} className="whitespace-pre-wrap">{point}</li>)}</ul><TopicVisual visual={s.visual} /></>}
        {s.recall && <div className="mt-3 border-t border-white/10 pt-3"><p className="text-sm text-violet-200">{s.recall.question}</p>
          <button type="button" className="mt-2 text-xs text-violet-300" aria-expanded={Boolean(revealed[`recall-${i}`])} onClick={() => setRevealed(v => ({ ...v, [`recall-${i}`]: !v[`recall-${i}`] }))}>{revealed[`recall-${i}`] ? 'Hide answer' : 'Check your recall'}</button>
          {revealed[`recall-${i}`] && <p className="mt-2 text-sm text-zinc-300">{s.recall.answer}</p>}</div>}
      </article>)}
    </div>
  </>;
}

export default function StudyVisualCard({ data, preview = false }) {
  const d = validateStudyVisual(data);
  if (!d) return <p role="alert" className="text-amber-300">This study visual was incomplete or could not be read. Please generate it again.</p>;
  return <section className="my-3 rounded-2xl border border-cyan-500/20 bg-zinc-950 p-4 text-zinc-200">
    <p className="text-xs text-cyan-300">Ace-it Visualize · {STUDY_FORMATS.find(f => f.id === d.kind).label}</p>
    <h3 className="text-xl font-semibold mt-1">{d.title}</h3><p className="mt-2 text-sm text-zinc-400">{d.summary}</p>
    {d.kind === 'graph' ? <GraphVisual key={`${d.title}-${JSON.stringify(d.points)}`} data={d} /> : <ChapterVisual key={`${d.kind}-${d.title}`} data={d} preview={preview} />}
  </section>;
}
