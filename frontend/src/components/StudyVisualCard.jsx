import { useRef, useState } from 'react';

export const STUDY_FORMATS = [
  { id: 'graph', label: 'Graph' },
  { id: 'cheatsheet', label: 'PDF Cheat Sheet' },
  { id: 'notes', label: 'Revision Notes' },
  { id: 'keypoints', label: 'Key Points' },
  { id: 'quickrevision', label: 'Quick Revision' },
];
const text = (v, max = 800) => typeof v === 'string' && v.trim() && v.length <= max;
export function validateStudyVisual(d) {
  if (!d || !STUDY_FORMATS.some(f => f.id === d.kind) || !text(d.title, 120) || !text(d.summary, 600)) return null;
  if (d.kind === 'graph') {
    if (!['bar', 'line', 'scatter'].includes(d.chartType) || !text(d.xLabel, 100) || !text(d.yLabel, 100) || !text(d.basis, 600) || typeof d.illustrative !== 'boolean') return null;
    if (!Array.isArray(d.points) || d.points.length < 2 || d.points.length > 16) return null;
    if (d.points.some(p => !p || !text(p.label, 60) || !Number.isFinite(p.y) || Math.abs(p.y) > 1e12 || (d.chartType !== 'bar' && (!Number.isFinite(p.x) || Math.abs(p.x) > 1e12)))) return null;
    if (d.chartType !== 'bar' && new Set(d.points.map(p => p.x)).size < 2) return null;
    return { ...d, points: d.chartType === 'bar' ? d.points : [...d.points].sort((a,b) => a.x-b.x) };
  }
  if (!Array.isArray(d.sections) || d.sections.length < 1 || d.sections.length > 8) return null;
  if (d.sections.some(s => !s || !text(s.heading, 120) || !Array.isArray(s.points) || !s.points.length || s.points.length > 8 || s.points.some(p => !text(p)))) return null;
  return d;
}
export function makeStudyVisualPrompt(chapter, focus, kind) {
  const label = STUDY_FORMATS.find(f => f.id === kind)?.label;
  if (!label) throw new Error('Unknown study format');
  return `Visualize: ${label} for ${chapter}${focus?.trim() ? `\nFocus: ${focus.trim()}` : ''}\n\n[STUDYVISUAL INSTRUCTIONS]\nReturn [STUDYVISUAL] valid JSON [/STUDYVISUAL] with kind "${kind}". Use the current school and chapter material. Do not invent data. For a graph, use supported numeric values or an explicitly labelled illustrative example derived from a supported formula. If no meaningful graph is possible, explain why in plain text. For notes, use useful chapter facts, definitions, examples and revision prompts. Plain text with Unicode mathematical symbols, no LaTeX, HTML or Markdown in JSON strings.`;
}
function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
// Embed browser-rendered pages so Unicode text is preserved without extra PDF/font dependencies.
export function pdfFromJpegs(images) {
  const enc = new TextEncoder(), chunks = [], offsets = [0]; let length = 0;
  const put = value => { const b = typeof value === 'string' ? enc.encode(value) : value; chunks.push(b); length += b.length; };
  const obj = (id, content) => { offsets[id] = length; put(`${id} 0 obj\n${content}\nendobj\n`); };
  put('%PDF-1.4\n');
  obj(1, '<< /Type /Catalog /Pages 2 0 R >>');
  obj(2, `<< /Type /Pages /Count ${images.length} /Kids [${images.map((_,i)=>`${3+i*3} 0 R`).join(' ')}] >>`);
  images.forEach((bytes,i) => {
    const id = 3+i*3;
    obj(id, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /XObject << /Im${i} ${id+1} 0 R >> >> /Contents ${id+2} 0 R >>`);
    offsets[id+1] = length; put(`${id+1} 0 obj\n<< /Type /XObject /Subtype /Image /Width 1190 /Height 1684 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${bytes.length} >>\nstream\n`); put(bytes); put('\nendstream\nendobj\n');
    const command = `q 595 0 0 842 0 0 cm /Im${i} Do Q`;
    obj(id+2, `<< /Length ${enc.encode(command).length} >>\nstream\n${command}\nendstream`);
  });
  const start = length;
  put(`xref\n0 ${offsets.length}\n0000000000 65535 f \n`);
  offsets.slice(1).forEach(o=>put(`${String(o).padStart(10,'0')} 00000 n \n`));
  put(`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`);
  return new Blob(chunks, { type: 'application/pdf' });
}
export async function makeStudyPdf(d) {
  const images = []; let canvas, ctx, y, page = 0;
  const newPage = () => {
    canvas = document.createElement('canvas'); canvas.width=1190; canvas.height=1684;
    ctx=canvas.getContext('2d'); if (!ctx) throw new Error('PDF rendering is unavailable in this browser.');
    ctx.fillStyle='#ffffff'; ctx.fillRect(0,0,1190,1684);
    ctx.fillStyle='#0891b2'; ctx.font='bold 25px Arial'; ctx.fillText('ACE-IT • CHAPTER REVISION',72,70);
    ctx.fillStyle='#64748b'; ctx.font='20px Arial'; ctx.fillText(`Page ${++page}`,1020,1620); y=130;
  };
  const finish = () => { const raw=atob(canvas.toDataURL('image/jpeg',0.94).split(',')[1]); images.push(Uint8Array.from(raw,c=>c.charCodeAt(0))); };
  const line = (s, size=25, bold=false, color='#1e293b') => {
    ctx.font=`${bold?'bold ':''}${size}px Arial`;
    // Wrap long unbroken words too; no clipping of URLs or mathematical expressions.
    let current='';
    const flush = () => {
      if(y>1540){finish();newPage();ctx.font=`${bold?'bold ':''}${size}px Arial`;}
      ctx.fillStyle=color;ctx.fillText(current.trimEnd(),72,y); y+=size*1.45; current='';
    };
    for (const word of String(s).split(/(\s+)/)) {
      if(word.includes('\n')) { flush(); continue; }
      if(ctx.measureText(current+word).width<=1046) { current+=word; continue; }
      if(current.trim()) flush();
      if(ctx.measureText(word).width<=1046) { current=word.trimStart(); continue; }
      for(const c of word) { if(ctx.measureText(current+c).width>1046) flush(); current+=c; }
    }
    if(y>1540){finish();newPage();ctx.font=`${bold?'bold ':''}${size}px Arial`;}
    ctx.fillStyle=color;ctx.fillText(current,72,y);y+=size*1.45;
  };
  newPage();line(d.title,38,true);y+=15;line(d.summary);y+=20;
  for(const section of d.sections){line(section.heading,29,true,'#0e7490'); for(const point of section.points) line(`• ${point}`);y+=20;}
  finish();return pdfFromJpegs(images);
}
export default function StudyVisualCard({ data }) {
  const d=validateStudyVisual(data), svgRef=useRef(null), [busy,setBusy]=useState(false), [error,setError]=useState('');
  if(!d) return <p className="text-amber-300">This study visual could not be read. Please generate it again.</p>;
  const downloadPdf=async()=>{setBusy(true);setError('');try { saveBlob(await makeStudyPdf(d),`${d.title.replace(/[^a-z0-9]/gi,'-')}.pdf`); } catch(e){setError(e.message || 'PDF export failed. Please retry.');}finally{setBusy(false);}};
  const graph=d.kind==='graph'; let chart=null;
  if(graph){
    const points=d.points, minY=Math.min(0,...points.map(p=>p.y)), maxY=Math.max(0,...points.map(p=>p.y));
    const spanY=maxY-minY||1, minX=Math.min(...points.map(p=>p.x||0)), maxX=Math.max(...points.map(p=>p.x||0));
    const x=(p,i)=>d.chartType==='bar'?100+(i+.5)*600/points.length:100+(p.x-minX)/(maxX-minX||1)*600;
    const y=v=>360-(v-minY)/spanY*260;
    chart=<svg ref={svgRef} viewBox="0 0 800 470" role="img" aria-label={`${d.title}: ${d.xLabel} versus ${d.yLabel}`} style={{fontFamily:'Arial,sans-serif',background:'#0f172a',minWidth:640}}>
      <title>{d.title}</title><rect width="800" height="470" fill="#0f172a"/>
      <text x="400" y="34" textAnchor="middle" fill="#f8fafc" fontSize="18">{d.title.length>65?d.title.slice(0,62)+"…":d.title}</text>
      {[0,1,2,3,4].map(i=>{const v=minY+i*spanY/4;return <g key={i}><path d={`M100 ${y(v)} H700`} stroke="#334155"/><text x="90" y={y(v)+5} textAnchor="end" fill="#cbd5e1" fontSize="12">{Number(v.toPrecision(4))}</text></g>;})}
      <path d="M100 90 V360 H710" fill="none" stroke="#94a3b8"/>
      {d.chartType==='line'&&<polyline points={points.map((p,i)=>`${x(p,i)},${y(p.y)}`).join(' ')} fill="none" stroke="#22d3ee" strokeWidth="3"/>}
      {points.map((p,i)=><g key={i}>{d.chartType==='bar'?<rect x={x(p,i)-Math.min(18,240/points.length)} y={Math.min(y(p.y),y(0))} width={Math.min(36,480/points.length)} height={Math.max(1,Math.abs(y(p.y)-y(0)))} fill="#22d3ee"><title>{p.label}: {p.y}</title></rect>:<circle cx={x(p,i)} cy={y(p.y)} r="5" fill="#a78bfa"><title>{p.label}: ({p.x}, {p.y})</title></circle>}
        <text transform={`translate(${x(p,i)},377) rotate(35)`} fill="#cbd5e1" fontSize="11">{d.chartType==='bar'?p.label.slice(0,15):p.x}</text></g>)}
      <text x="400" y="447" fill="#e2e8f0" textAnchor="middle" fontSize="14">{d.xLabel.length>65?d.xLabel.slice(0,62)+"…":d.xLabel}</text><text transform="translate(25,235) rotate(-90)" fill="#e2e8f0" textAnchor="middle" fontSize="14">{d.yLabel.length>35?d.yLabel.slice(0,32)+"…":d.yLabel}</text>
    </svg>;
  }
  return <section className="my-3 rounded-2xl border border-cyan-500/20 bg-slate-950 p-4 text-slate-200">
    <div className="flex justify-between items-start gap-3"><div><p className="text-xs text-cyan-300">Ace-it Visualize · {STUDY_FORMATS.find(f=>f.id===d.kind).label}</p><h3 className="text-xl font-semibold mt-1">{d.title}</h3></div>
      {graph?<button type="button" className="text-xs text-cyan-300" onClick={()=>{const copy=svgRef.current.cloneNode(true);copy.setAttributeNS('http://www.w3.org/2000/xmlns/','xmlns','http://www.w3.org/2000/svg');saveBlob(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}),'ace-it-graph.svg');}}>Download SVG</button>:<button type="button" disabled={busy} onClick={downloadPdf} className="text-xs text-cyan-300 disabled:opacity-40">{busy?'Preparing PDF…':'Download PDF'}</button>}
    </div><p className="mt-2 text-sm text-slate-400">{d.summary}</p>
    {error&&<p role="alert" className="text-amber-300 mt-2">{error}</p>}
    {graph?<><p className="my-3 text-xs text-amber-200">{d.illustrative?'Illustrative example — not measured chapter data':'Chapter data'} · {d.basis}</p><div className="overflow-x-auto">{chart}</div><table className="w-full mt-3 text-xs"><caption className="text-left text-slate-400">Exact values and labels</caption><thead><tr><th className="text-left">Label</th>{d.chartType!=='bar'&&<th>{d.xLabel}</th>}<th>{d.yLabel}</th></tr></thead><tbody>{d.points.map((p,i)=><tr key={i}><td>{p.label}</td>{d.chartType!=='bar'&&<td className="text-center">{p.x}</td>}<td className="text-center">{p.y}</td></tr>)}</tbody></table></>:<div className="grid gap-3 mt-4 sm:grid-cols-2">{d.sections.map((s,i)=><article key={i} className="rounded-xl bg-slate-900 border border-white/5 p-3"><h4 className="text-cyan-200 font-semibold">{s.heading}</h4><ul className="list-disc pl-4 mt-2 space-y-2 text-sm">{s.points.map((p,j)=><li key={j}>{p}</li>)}</ul></article>)}</div>}
  </section>;
}
