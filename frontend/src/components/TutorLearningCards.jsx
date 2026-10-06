import { useEffect, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';


const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MathText = ({ children }) => <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[[rehypeKatex, { strict: false, trust: false }]]}>{String(children || '')}</ReactMarkdown>;

export function TutorCheck({ check, onScored }) {
  const [result, setResult] = useState(check), [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => setResult(check), [check]);
  if (!result || !Array.isArray(result.options) || result.options.length !== 4) return null;
  const answer = async letter => {
    if (busy || result.completed) return;
    setBusy(true); setError('');
    try {
      const { data } = await axios.post(`${API}/chat/checks/${result.check_id}/answer`, { answer: letter }, { withCredentials: true, timeout: 15000 });
      setResult(data.check); onScored?.(data.mastery);
      window.dispatchEvent(new Event('aceit-learning-updated'));
    } catch (e) { setError(e.response?.data?.detail || 'Could not save your answer. Please try again.'); }
    finally { setBusy(false); }
  };
  return <section className="my-3 rounded-xl border border-violet-400/25 bg-violet-500/10 p-3" data-testid="tutor-learning-check">
    <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-violet-300">Check your understanding</h3>
    <MathText>{result.question}</MathText>
    <div className="mt-2 grid gap-2">{result.options.map((option, i) => {
      const letter = 'ABCD'[i];
      const correct = result.completed && result.correct === letter;
      const selected = result.completed && result.selected === letter;
      return <button key={letter} disabled={busy || result.completed} onClick={() => answer(letter)}
        className={`rounded-lg border p-2 text-left text-sm ${correct ? 'border-green-400 bg-green-500/10' : selected ? 'border-rose-400 bg-rose-500/10' : 'border-white/15 hover:border-violet-400'}`}>
        <span className="mr-2 text-violet-300">{letter}.</span><MathText>{option}</MathText>
      </button>;
    })}</div>
    {busy && <p className="mt-2 text-xs text-zinc-400">Saving your answer…</p>}
    {error && <p role="alert" className="mt-2 text-sm text-amber-200">{typeof error === 'string' ? error : 'Could not save your answer.'}</p>}
    {result.completed && <div className="mt-3 text-sm"><p className={result.is_correct ? 'text-green-300' : 'text-amber-200'}>{result.is_correct ? 'Correct — progress saved.' : 'Let’s revisit this idea — progress saved.'}</p><MathText>{result.explanation}</MathText></div>}
    <p className="mt-2 text-xs text-zinc-400">Mastery changes when you answer, not when you read.</p>
  </section>;
}
