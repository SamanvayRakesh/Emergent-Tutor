import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Send, Square, Plus, BookOpen, ChevronDown, Trash2, Sparkles, CheckCircle, XCircle, MessageSquare, Brain, ArrowLeft, Youtube, ExternalLink, Zap, ThumbsUp, ThumbsDown, ChevronRight } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useCredits } from '../contexts/CreditsContext';
import { toast } from 'sonner';
import InteractiveQuizModal from './InteractiveQuizModal';
import MindMapCard, { validateMindMap, makeMindMapPrompt } from './MindMapCard';
import StudyVisualCard, { STUDY_FORMATS, makeStudyVisualPrompt, validateStudyVisual } from './StudyVisualCard';
import FlowchartCard, { validateFlowchart, makeFlowchartPrompt } from './FlowchartCard';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Retry only an authentication rejection, before generation can start.
// A response that has begun streaming is never replayed automatically.
export async function requestTutorReply(sessionId, content, signal) {
  const options = {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include', signal, body: JSON.stringify({ content }),
  };
  const url = API + '/chat/sessions/' + encodeURIComponent(sessionId) + '/message';
  let response = await fetch(url, options);
  if (response.status !== 401) return response;
  try {
    await axios.post(API + '/auth/refresh', {}, {
      withCredentials: true, timeout: 15000, signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    if (error.response?.status === 401 || error.response?.status === 403) {
      const expired = new Error('Your session has expired. Please sign in again, then request the visual.');
      expired.code = 'SESSION_EXPIRED';
      throw expired;
    }
    throw new Error('Could not renew your session. Please retry when the sign-in service is available.');
  }
  response = await fetch(url, options);
  if (response.status === 401) {
    const expired = new Error('Your session has expired. Please sign in again, then request the visual.');
    expired.code = 'SESSION_EXPIRED';
    throw expired;
  }
  return response;
}


const SUBJECT_COLORS = {
  Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4',
  Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b',
  'Social Science': '#3b82f6', 'Computer Science': '#ef4444'
};

// Normalize known malformed model math without changing existing math or code.
function fixMathDelimiters(text = '') {
  const repair = value => value.replace(/\{frac\}\s*[\[{]([^{}\[\]\n]+)[}\]]\s*[\[{]([^{}\[\]\n]+)[}\]]/g,
    (_, a, b) => `\\frac{${a}}{${b}}`);
  return String(text).split(/(```[\s\S]*?```|`[^`\n]*`|\$\$[\s\S]*?\$\$|\$(?:\\.|[^$\n])+\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g).map(part => {
    if (part.startsWith('`')) return part;
    if (part.startsWith('\\[')) return `\n\n$$\n${repair(part.slice(2,-2))}\n$$\n\n`;
    if (part.startsWith('\\(')) return `$${repair(part.slice(2,-2))}$`;
    if (part.startsWith('$')) return repair(part);
    return repair(part).replace(/\\(?:dfrac|tfrac|frac)\s*\{(?:[^{}]|\{[^{}]*\})*\}\s*\{(?:[^{}]|\{[^{}]*\})*\}|\\sqrt(?:\[[^\]\n]*\])?\s*\{(?:[^{}]|\{[^{}]*\})*\}|\\(?:times|div|pm|leq|geq|neq|approx|cdot|infty|alpha|beta|gamma|theta|pi|sigma|delta|lambda|mu|omega)\b/g, formula => `$${formula}$`);
  }).join('');
}

function parseQuizBlocks(content) {
  if (content.includes('[MINDMAP]') && !content.includes('[/MINDMAP]')) {
    return [{ type: 'text', content: 'The mind map was incomplete. Please request it again.' }];
  }
  if (content.includes('[FLOWCHART]') && !content.includes('[/FLOWCHART]')) {
    return [{ type: 'text', content: 'The flowchart was incomplete. Please request it again.' }];
  }
  if (content.includes('[STUDYVISUAL]') && !content.includes('[/STUDYVISUAL]')) return [{ type: 'text', content: 'The study visual was incomplete. Please generate it again.' }];
  const fixed = content;
  const parts = [];
  // Combined regex: matches either [QUIZ]...[/QUIZ] or [YOUTUBE]...[/YOUTUBE]
  const regex = /\[QUIZ\]([\s\S]*?)\[\/QUIZ\]|\[YOUTUBE\]([\s\S]*?)\[\/YOUTUBE\]|\[MINDMAP\]([\s\S]*?)\[\/MINDMAP\]|\[FLOWCHART\]([\s\S]*?)\[\/FLOWCHART\]|\[STUDYVISUAL\]([\s\S]*?)\[\/STUDYVISUAL\]/g;
  let lastIdx = 0, match;
  while ((match = regex.exec(fixed)) !== null) {
    if (match.index > lastIdx) parts.push({ type: 'text', content: fixMathDelimiters(fixed.slice(lastIdx, match.index)) });
    if (match[1] !== undefined) {
      try {
        const data = JSON.parse(match[1].trim());
        parts.push({ type: 'quiz', data });
      } catch {
        parts.push({ type: 'text', content: match[0] });
      }
    } else if (match[2] !== undefined) {
      const query = match[2].trim();
      if (query) parts.push({ type: 'youtube', query });
    }
    if (match[3] !== undefined) {
      try {
        const data = validateMindMap(JSON.parse(match[3].trim()));
        if (!data) throw new Error('Invalid mind map');
        parts.push({ type: 'mindmap', data });
      } catch {
        parts.push({ type: 'text', content: 'The mind map could not be read. Please request it again.' });
      }
    }
    if (match[4] !== undefined) {
      try {
        const data = validateFlowchart(JSON.parse(match[4].trim()));
        if (!data) throw new Error('Invalid flowchart');
        parts.push({ type: 'flowchart', data });
      } catch {
        parts.push({ type: 'text', content: 'The flowchart could not be read. Please request it again.' });
      }
    }
    if (match[5] !== undefined) {
      try {
        const data = validateStudyVisual(JSON.parse(match[5].trim()));
        if (!data) throw new Error('Invalid study visual');
        parts.push({ type: 'studyvisual', data });
      } catch {
        parts.push({ type: 'text', content: 'The study visual could not be read. Please generate it again.' });
      }
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < fixed.length) parts.push({ type: 'text', content: fixMathDelimiters(fixed.slice(lastIdx)) });
  return parts;
}

// Read only complete section objects. Unfinished JSON remains private.
export function completedVisualSections(content) {
  if (typeof content !== 'string' || content.length > 150000) return [];
  const start = /"sections"\s*:\s*\[/.exec(content);
  if (!start) return [];
  const sections = [];
  let depth = 0, quoted = false, escaped = false, first = -1;
  for (let i = start.index + start[0].length; i < content.length; i++) {
    const c = content[i];
    if (quoted) {
      if (escaped) escaped = false;
      else if (c === '\\') escaped = true;
      else if (c === '"') quoted = false;
      continue;
    }
    if (c === '"') { quoted = true; continue; }
    if (c === '{') { if (depth === 0) first = i; depth++; }
    else if (c === '}') {
      depth--;
      if (depth < 0) break;
      if (depth === 0 && first >= 0) {
        try {
          const section = JSON.parse(content.slice(first, i + 1));
          if (!section.visual && Array.isArray(section.items)) {
            section.visual = { type: section.type || 'concept', title: section.heading, items: section.items };
            section.points = section.items.map(item => item?.detail);
          }
          const valid = validateStudyVisual({ kind: 'notes', title: 'Preview', summary: 'Preview', sections: [section] });
          if (valid) sections.push(valid.sections[0]);
        } catch { /* Never show an incomplete or invalid object. */ }
        first = -1;
        if (sections.length === 40) break;
      }
    } else if (c === ']' && depth === 0) break;
  }
  return sections;
}

export function visualRequestInfo(content) {
  const match = /^Visualize: (Mind map|Flowchart|Graph|PDF Cheat Sheet|Revision Notes|Key Points|Quick Revision) for ([^\n]+)/.exec(content || '');
  if (!match) return null;
  const ids = { 'Mind map': 'mindmap', Flowchart: 'flowchart', Graph: 'graph', 'PDF Cheat Sheet': 'cheatsheet', 'Revision Notes': 'notes', 'Key Points': 'keypoints', 'Quick Revision': 'quickrevision' };
  return { label: match[1], kind: ids[match[1]], chapter: match[2] };
}

function cleanVisualFocus(input) {
  if (!visualRequestInfo(input)) return input;
  return /^Focus: ([^\n]+)/m.exec(input)?.[1] || '';
}

export function VisualReplyProgress({ request, content, ready = false }) {
  const sections = completedVisualSections(content);
  const complete = /\[\/(?:STUDYVISUAL|MINDMAP|FLOWCHART)\]/.test(content);
  const parts = complete ? parseQuizBlocks(content) : [];
  const visual = parts.find(part => ['studyvisual', 'mindmap', 'flowchart'].includes(part.type));
  return <div className="flex gap-3" data-testid="visual-progress">
    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-600 flex-shrink-0 flex items-center justify-center mt-1"><Sparkles size={14} className="text-white" /></div>
    <div className="message-ai p-3.5 w-full max-w-[82%]">
      <div role="status" aria-live="polite" className="flex items-center gap-2 text-xs text-violet-200">
        <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
        {ready ? 'Visual ready · saving your reply…' : sections.length ? `${sections.length} topic${sections.length === 1 ? '' : 's'} ready · building the rest…` : content ? 'Building your visual…' : `Preparing ${request?.label || 'your visual'}…`}
      </div>
      {visual?.type === 'studyvisual' ? <StudyVisualCard data={visual.data} preview={!ready} /> :
        visual?.type === 'mindmap' ? <MindMapCard data={visual.data} /> :
        visual?.type === 'flowchart' ? <FlowchartCard data={visual.data} /> :
        sections.length > 0 ? <StudyVisualCard preview data={{ kind: request?.kind || 'notes', title: request?.chapter || 'Chapter', summary: 'Finished topics appear here while the rest is being prepared.', sections }} /> :
        <div aria-hidden="true" className="mt-4 space-y-3 animate-pulse">
          <div className="h-4 w-2/3 rounded bg-violet-400/10" />
          <div className="grid grid-cols-2 gap-3">{[0, 1].map(i => <div key={i} className="h-20 rounded-xl border border-cyan-400/10 bg-cyan-400/5" />)}</div>
          <div className="h-3 w-5/6 rounded bg-white/5" />
        </div>}
    </div>
  </div>;
}

function YouTubeCard({ query }) {
  const encoded = encodeURIComponent(query);
  const searchUrl = `https://www.youtube.com/results?search_query=${encoded}`;
  // YouTube embed playlist via search (no API key needed)
  const embedUrl = `https://www.youtube.com/embed?listType=search&list=${encoded}`;
  const [showEmbed, setShowEmbed] = useState(false);

  return (
    <div className="my-3 rounded-2xl border border-red-500/20 bg-red-500/5 overflow-hidden" data-testid="youtube-card">
      <div className="flex items-center justify-between p-3.5 border-b border-red-500/10">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-red-500/15 flex items-center justify-center flex-shrink-0">
            <Youtube size={16} className="text-red-400" />
          </div>
          <div className="min-w-0">
            <p className="text-red-300 text-[10px] font-body uppercase tracking-wider font-semibold">Visual Boost</p>
            <p className="text-white text-sm font-body font-medium truncate">{query}</p>
          </div>
        </div>
        <a href={searchUrl} target="_blank" rel="noreferrer" data-testid="youtube-open-link"
          className="flex-shrink-0 p-2 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all">
          <ExternalLink size={14} />
        </a>
      </div>
      {showEmbed ? (
        <div className="aspect-video bg-black">
          <iframe src={embedUrl} title={`YouTube: ${query}`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen className="w-full h-full" />
        </div>
      ) : (
        <button onClick={() => setShowEmbed(true)} data-testid="youtube-play-btn"
          className="w-full p-3 flex items-center justify-center gap-2 text-red-300 hover:text-red-200 hover:bg-red-500/5 text-xs font-body font-semibold transition-all">
          <Youtube size={14} /> Play video search inline
        </button>
      )}
    </div>
  );
}

function QuizCard({ data }) {
  const [selected, setSelected] = useState(null);
  const [revealed, setRevealed] = useState(false);

  const handleSelect = (opt) => {
    if (revealed) return;
    setSelected(opt);
    setRevealed(true);
  };

  const letter = (opt) => opt.charAt(0);
  const isCorrect = selected && letter(selected) === data.correct;

  return (
    <div className="my-3 p-4 rounded-2xl border border-violet-500/20 bg-violet-500/5">
      <div className="flex items-center gap-2 mb-3">
        <Brain size={16} className="text-violet-400" />
        <span className="text-violet-400 text-xs font-body uppercase tracking-wider font-semibold">Quick Check</span>
      </div>
      <p className="text-white font-body text-sm mb-3 leading-relaxed">{data.question}</p>
      <div className="space-y-2">
        {data.options?.map((opt, i) => {
          const isOpt = letter(opt) === data.correct;
          const isSel = selected === opt;
          let bg = 'bg-zinc-900/50 border-white/10 hover:border-white/20';
          if (revealed) {
            if (isOpt) bg = 'bg-green-500/15 border-green-500/40';
            else if (isSel && !isOpt) bg = 'bg-red-500/15 border-red-500/40';
            else bg = 'bg-zinc-900/30 border-white/5 opacity-60';
          }
          return (
            <button key={i} onClick={() => handleSelect(opt)} disabled={revealed}
              className={`w-full text-left px-3 py-2.5 rounded-xl border text-sm font-body transition-all flex items-center gap-3 ${bg}`}>
              <span className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-heading font-bold flex-shrink-0 ${revealed && isOpt ? 'border-green-400 text-green-400' : revealed && isSel ? 'border-red-400 text-red-400' : 'border-zinc-600 text-zinc-500'}`}>
                {letter(opt)}
              </span>
              <span className="text-zinc-200">{opt.slice(3)}</span>
              {revealed && isOpt && <CheckCircle size={14} className="text-green-400 ml-auto" />}
              {revealed && isSel && !isOpt && <XCircle size={14} className="text-red-400 ml-auto" />}
            </button>
          );
        })}
      </div>
      {revealed && (
        <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
          className={`mt-3 p-3 rounded-xl text-sm font-body ${isCorrect ? 'bg-green-500/10 border border-green-500/20 text-green-300' : 'bg-orange-500/10 border border-orange-500/20 text-orange-300'}`}>
          {isCorrect ? 'Excellent! ' : 'Not quite! '}{data.explanation}
        </motion.div>
      )}
    </div>
  );
}

function MessageBubble({ msg, isStreaming, isNios, feedbackState, onFeedback, onDetailRequest }) {
  const isUser = msg.role === 'user';
  // Structured blocks are parsed after the reply completes.
  const parts = (!isUser && !isStreaming) ? parseQuizBlocks(msg.content) : null;
  const structuredStreaming = isStreaming && /\[(?:STUDYVISUAL|MINDMAP|FLOWCHART)(?:\]|$)/.test(msg.content);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-1 ${isUser ? 'bg-cyan-500 text-black' : 'bg-gradient-to-br from-violet-500 to-fuchsia-600'}`}>
        {isUser ? <span className="text-xs font-heading font-black">U</span> : <Sparkles size={14} className="text-white" />}
      </div>

      <div className={`max-w-[82%] flex flex-col gap-1.5`}>
        <div className={`${isUser ? 'message-user' : 'message-ai'} p-3.5`}>
          {isUser ? (
            <p className="text-white text-sm font-body leading-relaxed">{/^Visualize: (Mind map|Flowchart|Graph|PDF Cheat Sheet|Revision Notes|Key Points|Quick Revision) for /.test(msg.content) ? msg.content.split(/\n\n\[(?:MINDMAP|FLOWCHART|STUDYVISUAL) INSTRUCTIONS\]/)[0] : msg.content}</p>
          ) : msg.visualPreview ? (
            <StudyVisualCard data={msg.visualPreview} preview />
          ) : structuredStreaming ? (
            <VisualReplyProgress content={msg.content} />
          ) : isStreaming ? (
            <div className="markdown-content text-sm font-body streaming-cursor">
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[[rehypeKatex, { strict: false, trust: false }]]}>
                {fixMathDelimiters(msg.content)}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="text-sm font-body">
              {parts?.map((part, i) =>
                part.type === 'studyvisual' ? (
                  <StudyVisualCard key={`study-${i}`} data={part.data} />
                ) : part.type === 'flowchart' ? (
                  <FlowchartCard key={`flow-${i}`} data={part.data} />
                ) : part.type === 'mindmap' ? (
                  <MindMapCard key={`map-${i}`} data={part.data} />
                ) : part.type === 'quiz' ? (
                  <QuizCard key={`quiz-${i}`} data={part.data} />
                ) : part.type === 'youtube' ? (
                  <YouTubeCard key={`yt-${i}`} query={part.query} />
                ) : (
                  <div key={`text-${i}`} className="markdown-content">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[[rehypeKatex, { strict: false, trust: false }]]}
                      components={{
                        p: ({ children }) => (
                          <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
                        ),
                        code: ({ inline, children }) => (
                          inline
                            ? <code className="bg-black/30 text-cyan-300 px-1 py-0.5 rounded text-xs">{children}</code>
                            : <pre className="bg-black/30 text-cyan-300 p-3 rounded-xl text-xs overflow-x-auto my-2"><code>{children}</code></pre>
                        ),
                      }}
                    >{part.content}</ReactMarkdown>
                  </div>
                )
              )}
            </div>
          )}
        </div>

        {msg.unconfirmed && <span className="text-xs text-amber-200">Connection interrupted · reload the chat to check whether this reply was saved.</span>}
        {msg.stopped && <span className="text-xs text-zinc-500">Response stopped</span>}
        {/* Feedback & Detail row — only for finalised AI messages */}
        {!isUser && !isStreaming && (
          <div className="flex items-center gap-2 pl-1" data-testid="msg-actions">
            {/* Thumbs Up */}
            <button
              data-testid="feedback-up-btn"
              onClick={() => onFeedback(msg.message_id, 'up')}
              disabled={!msg.message_id}
              className={`p-1.5 rounded-lg transition-all text-xs flex items-center gap-1 ${
                feedbackState === 'up'
                  ? 'bg-green-500/20 text-green-400 border border-green-500/40'
                  : 'text-zinc-600 hover:text-green-400 hover:bg-green-500/10 border border-transparent'
              }`}
            >
              <ThumbsUp size={12} />
            </button>

            {/* Thumbs Down */}
            <button
              data-testid="feedback-down-btn"
              onClick={() => onFeedback(msg.message_id, 'down')}
              disabled={!msg.message_id}
              className={`p-1.5 rounded-lg transition-all text-xs flex items-center gap-1 ${
                feedbackState === 'down'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                  : 'text-zinc-600 hover:text-red-400 hover:bg-red-500/10 border border-transparent'
              }`}
            >
              <ThumbsDown size={12} />
            </button>

            {/* Explain in Detail — NIOS only */}
            {isNios && (
              <button
                data-testid="explain-detail-btn"
                onClick={() => onDetailRequest()}
                className="ml-1 flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-body font-semibold text-violet-400 border border-violet-500/25 hover:bg-violet-500/10 hover:border-violet-500/40 transition-all"
              >
                <ChevronRight size={11} /> Explain in detail
              </button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SessionSetup({ onCreated, prefill }) {
  const { user } = useAuth();
  const userClass = user?.class_level || '9';
  const isNios = user?.school === 'nios';
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [sel, setSel] = useState({ class: userClass, subject: '', chapterId: '', chapterName: '' });
  const [loading, setLoading] = useState(false);
  const prefillRan = useRef(false);

  useEffect(() => {
    // Grade-locked: only load subjects for user's class
    setSel(p => ({ ...p, class: userClass }));
    axios.get(`${API}/syllabus/${userClass}/subjects`, { withCredentials: true }).then(r => setSubjects(r.data)).catch(() => setSubjects([]));
  }, [userClass]);

  // Auto-fill and auto-create from Syllabus navigation state
  useEffect(() => {
    if (!prefill || prefillRan.current || !prefill.class_level) return;
    prefillRan.current = true;

    const run = async () => {
      setLoading(true);
      try {
        const [subjRes, chapRes] = await Promise.all([
          axios.get(`${API}/syllabus/${prefill.class_level}/subjects`, { withCredentials: true }),
          axios.get(`${API}/syllabus/${prefill.class_level}/${encodeURIComponent(prefill.subject)}/chapters`, { withCredentials: true })
        ]);
        setSubjects(subjRes.data);
        setChapters(chapRes.data);
        setSel({ class: prefill.class_level, subject: prefill.subject, chapterId: prefill.chapter_id, chapterName: prefill.chapter });

        // Auto-create session
        const { data } = await axios.post(`${API}/chat/sessions`, {
          class_level: prefill.class_level,
          subject: prefill.subject,
          chapter: prefill.chapter,
          chapter_id: prefill.chapter_id
        }, { withCredentials: true });
        onCreated(data);
      } catch (e) {
        console.error(e);
        setLoading(false);
      }
    };
    run();
  }, [prefill, onCreated]);

  const onSubjectChange = async (subj) => {
    setSel(p => ({ ...p, subject: subj, chapterId: '', chapterName: '' }));
    const r = await axios.get(`${API}/syllabus/${userClass}/${encodeURIComponent(subj)}/chapters`, { withCredentials: true });
    setChapters(r.data);
  };

  const handleStart = async () => {
    if (!sel.class || !sel.subject || !sel.chapterId) return;
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/chat/sessions`, {
        class_level: sel.class, subject: sel.subject, chapter: sel.chapterName, chapter_id: sel.chapterId
      }, { withCredentials: true });
      onCreated(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const selectClass = 'w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-cyan-500/50 appearance-none';

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md glass rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-white font-heading font-bold">Start AI Tutoring</h2>
            <p className="text-zinc-500 text-xs font-body">
              {prefill ? `Loading ${prefill.subject} — ${prefill.chapter}...` : 'Select your topic to begin'}
            </p>
          </div>
        </div>

        {/* Prefill auto-launch spinner */}
        {prefill && loading && (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="w-10 h-10 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
            <p className="text-zinc-400 text-sm font-body">Opening your session...</p>
          </div>
        )}

        {!prefill && <div className="space-y-3">
          <div className="px-4 py-3 rounded-xl border border-amber-400/30 bg-amber-500/10 text-amber-300 text-sm font-body font-semibold flex items-center gap-2" data-testid="chat-class-locked">
            <Sparkles size={14} />
            {isNios ? 'Secondary Course — NIOS' : `Class ${userClass} — your active grade`}
          </div>

          {subjects.length > 0 && (
            <div className="relative">
              <select value={sel.subject} onChange={e => onSubjectChange(e.target.value)} data-testid="subject-select" className={selectClass}>
                <option value="">Select Subject</option>
                {subjects.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
              </select>
              <ChevronDown size={16} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
            </div>
          )}

          {chapters.length > 0 && (
            <div className="relative">
              <select value={sel.chapterId} onChange={e => {
                const ch = chapters.find(c => c.id === e.target.value);
                setSel(p => ({ ...p, chapterId: e.target.value, chapterName: ch?.name || '' }));
              }} data-testid="chapter-select" className={selectClass}>
                <option value="">Select Chapter</option>
                {chapters.map(ch => <option key={ch.id} value={ch.id}>{ch.name}</option>)}
              </select>
              <ChevronDown size={16} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
            </div>
          )}

          <button onClick={handleStart} disabled={!sel.chapterId || loading} data-testid="start-chat-btn"
            className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-black font-heading font-bold text-sm transition-all flex items-center justify-center gap-2">
            {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <><Sparkles size={16} /> Start Learning</>}
          </button>
        </div>}
      </motion.div>
    </div>
  );
}

export default function ChatPage() {
  const { sessionId: paramId } = useParams();
  const nav = useNavigate();
  const location = useLocation();
  const prefill = location.state || null;
  const { user } = useAuth();
  const { usage, plan, triggerUpgrade, refresh: refreshSub } = useSubscription();
  const { refresh: refreshCredits } = useCredits();
  const isNios = user?.school === 'nios';
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [visualizeOpen, setVisualizeOpen] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [visualRequest, setVisualRequest] = useState(null);
  const [visualReady, setVisualReady] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const [quizModal, setQuizModal] = useState(null); // {quizData}
  const [feedbackMap, setFeedbackMap] = useState({}); // { [message_id]: 'up'|'down' }
  const [chapterMastery, setChapterMastery] = useState(null); // { mastery_pct, recommended_difficulty }
  const bottomRef = useRef(null);
  const streamBufferRef = useRef('');
  const rafRef = useRef(null);
  const sendingRef = useRef(false);
  const activeRequestRef = useRef(null);
  const stoppedRef = useRef(false);
  const readyVisualRef = useRef('');
  const replyCompletedRef = useRef(false);
  const [replyError, setReplyError] = useState('');

  // Cleanup RAF on unmount
  useEffect(() => () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); }, []);

  const sendFeedback = useCallback(async (messageId, vote) => {
    if (!messageId) return;
    // Optimistic UI — update immediately
    setFeedbackMap(p => ({ ...p, [messageId]: vote }));
    try {
      await axios.post(`${API}/chat/feedback`, { message_id: messageId, vote }, { withCredentials: true });
    } catch (e) {
      console.warn('[AceIt] feedback error:', e);
      // Revert on failure
      setFeedbackMap(p => { const n = { ...p }; delete n[messageId]; return n; });
    }
  }, []);

  const loadSession = useCallback(async (sid) => {
    try {
      const { data } = await axios.get(`${API}/chat/sessions/${sid}`, { withCredentials: true });
      setSession(data.session);
      setMessages(data.messages);
      localStorage.setItem('aceit_last_chat_session', sid);
      // Fetch chapter mastery (fire-and-forget, non-blocking)
      if (data.session?.chapter) {
        axios.get(`${API}/quiz/topic-mastery`, {
          params: { topic: data.session.chapter, subject: data.session.subject }, withCredentials: true,
        }).then(r => setChapterMastery(r.data)).catch(() => {});
      }
    } catch {
      localStorage.removeItem('aceit_last_chat_session');
      nav('/chat', { replace: true });
    }
  }, [nav]);

  const handleCreated = (newSession) => {
    setSessions(p => [newSession, ...p]);
    setSession(newSession);
    setMessages([]);
    setChapterMastery(null);
    localStorage.setItem('aceit_last_chat_session', newSession.session_id);
    nav(`/chat/${newSession.session_id}`, { replace: true, state: null });
    if (newSession?.chapter) {
      axios.get(`${API}/quiz/topic-mastery`, {
        params: { topic: newSession.chapter, subject: newSession.subject }, withCredentials: true,
      }).then(r => setChapterMastery(r.data)).catch(() => {});
    }
  };

  useEffect(() => {
    if (!paramId) {
      const lastId = localStorage.getItem('aceit_last_chat_session');
      if (lastId) { nav(`/chat/${lastId}`, { replace: true }); return; }
    }
    if (paramId) loadSession(paramId);
    axios.get(`${API}/chat/sessions`, { withCredentials: true }).then(r => setSessions(r.data)).catch(() => {});
  }, [paramId, loadSession, nav]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: streaming ? 'instant' : 'smooth' });
  }, [messages, streamingContent, streaming]);

  const processStream = async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = body.detail;
      throw new Error(typeof detail === 'string' ? detail : detail?.message ||
        (res.status === 401 ? 'Your session expired. Please sign in again.' : 'The tutor request failed. Please try again.'));
    }
    if (!res.body) throw new Error('The tutor response was missing. Please try again.');
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '', full = '', finished = false;

    const handleEvent = (event) => {
      const payload = event.split('\n').filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart()).join('\n');
      if (!payload) return;
      let d;
      try { d = JSON.parse(payload); }
      catch { throw new Error('The tutor response was interrupted. Please try again.'); }
      if (d.type === 'reset') {
        full = ''; streamBufferRef.current = ''; setStreamingContent(''); setVisualReady(false); readyVisualRef.current = ''; return;
      }
      if (d.type === 'error') throw new Error(d.message || 'The tutor could not finish this reply. Please try again.');
      if (d.type === 'visual_ready' && typeof d.content === 'string') {
        full = d.content; streamBufferRef.current = full; readyVisualRef.current = full;
        if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
        setStreamingContent(full); setVisualReady(true); return;
      }
      if (d.type === 'chunk' && typeof d.content === 'string') {
        full += d.content;
        streamBufferRef.current = full;
        if (!rafRef.current) {
          rafRef.current = requestAnimationFrame(() => {
            setStreamingContent(streamBufferRef.current);
            rafRef.current = null;
          });
        }
      }
      if (d.type === 'done') {
        if (!full.trim()) throw new Error('The tutor returned an empty reply. Please try again.');
        if (finished) return;
        finished = true; replyCompletedRef.current = true;
        if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
        setMessages(p => [...p, { role: 'assistant', content: full,
          timestamp: new Date().toISOString(), message_id: d.message_id }]);
        setStreamingContent('');
        if (d.credits_used) {
          toast.success(`−${d.credits_used} credits (${d.word_count || 0} words)`, {
            id: 'credit-deduct', duration: 1800,
            style: { background: 'rgba(30,27,75,0.85)', color: '#fcd34d', border: '1px solid rgba(251,191,36,0.4)', fontSize: '13px' },
            icon: <Zap size={14} className="text-yellow-400" />,
          });
        }
      }
    };

    try {
      while (!finished) {
        const { value, done } = await reader.read();
        buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
        // Normalize only after accumulating; CRLF delimiters may span chunks.
        buffer = buffer.replace(/\r\n/g, '\n');
        let boundary;
        while ((boundary = buffer.indexOf('\n\n')) !== -1) {
          const event = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          handleEvent(event);
          if (finished) break;
        }
        if (done) {
          if (!finished && buffer.trim()) handleEvent(buffer);
          break;
        }
      }
      if (!finished) throw new Error('The connection ended before the tutor finished. Please try again.');
    } finally {
      try { await reader.cancel(); } catch {}
      reader.releaseLock();
    }
  };

  // Detect quiz intent and auto-open quiz modal
  const QUIZ_INTENTS = ['give me a quiz', 'quiz me', 'test me', 'practice quiz', 'quick quiz', 'start a quiz', 'quiz on this'];
  const isQuizIntent = (text) => QUIZ_INTENTS.some(q => text.toLowerCase().includes(q));

  const openQuizModal = useCallback(async () => {
    if (!session) return false;
    const toastId = toast.loading('Generating quick quiz…');
    try {
      const { data } = await axios.post(`${API}/quiz/generate`, {
        class_level: session.class_level,
        subject: session.subject,
        chapter: session.chapter,
        topic: session.chapter,
        num_questions: 5,
      }, { withCredentials: true });
      toast.dismiss(toastId);
      setQuizModal({ quizData: data });
      return true;
    } catch (e) {
      toast.dismiss(toastId);
      const detail = e?.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Could not generate quiz. Try again.';
      toast.error(msg);
      return false;
    }
  }, [session]);

  const stopReply = () => {
    if (!activeRequestRef.current || stoppedRef.current) return;
    stoppedRef.current = true;
    activeRequestRef.current.abort();
  };

  useEffect(() => () => activeRequestRef.current?.abort(), []);

  const sendMessage = async (forced) => {
    const text = (forced !== undefined ? forced : input).trim();
    if (!text || streaming || sendingRef.current || !session) return;
    stoppedRef.current = false;
    readyVisualRef.current = ''; replyCompletedRef.current = false;
    sendingRef.current = true;
    setReplyError('');
    if (forced === undefined) setInput('');

    // Detect quiz intent → open quiz modal
    if (isQuizIntent(text)) {
      const opened = await openQuizModal();
      if (opened) {
        // Only add the user message if quiz actually opened
        // Quiz generation already ran: avoid an unconsumed, charged tutor request.
        setMessages(p => [...p, { role: 'user', content: text, timestamp: new Date().toISOString() }]);
        sendingRef.current = false;
        return;
      }
      // Fallback: quiz failed — continue as normal chat message
    }

    setMessages(p => [...p, { role: 'user', content: text, timestamp: new Date().toISOString() }]);
    setVisualRequest(visualRequestInfo(text));
    setVisualReady(false);
    setStreaming(true);
    setStreamingContent('');
    streamBufferRef.current = '';
    const controller = new AbortController();
    activeRequestRef.current = controller;
    const timeout = setTimeout(() => controller.abort(), 120000);

    const retainVisualPreview = () => {
      const request = visualRequestInfo(text);
      if (!request || replyCompletedRef.current) return;
      if (readyVisualRef.current) {
        setMessages(p => [...p, { role: 'assistant', content: readyVisualRef.current,
          timestamp: new Date().toISOString(), unconfirmed: true }]);
        return;
      }
      const sections = completedVisualSections(streamBufferRef.current);
      if (!sections.length) return;
      setMessages(p => [...p, { role: 'assistant', content: '', unconfirmed: true,
        timestamp: new Date().toISOString(), visualPreview: { kind: request.kind,
          title: request.chapter, summary: 'Generation was interrupted. These finished topics are still available.',
          sections, coverage: { status: 'partial', note: 'Incomplete preview; some chapter topics are missing.', topics: sections.map(s => s.heading) } } }]);
    };
    try {
      const res = await requestTutorReply(session.session_id, text, controller.signal);
      if (res.status === 429) {
        // Daily limit hit — trigger upgrade modal
        const body = await res.json().catch(() => ({}));
        const detail = body?.detail || {};
        triggerUpgrade?.({
          feature: detail.feature, message: detail.message,
          limit_info: detail.limit_info, upgrade_to: detail.upgrade_to || 'pro',
        });
        // Remove the user's optimistic message
        setMessages(p => p.slice(0, -1));
        setStreaming(false);
        return;
      }
      if (res.status === 402) {
        const body = await res.json().catch(() => ({}));
        const msg = body?.detail?.message || 'Not enough credits to send another AI message.';
        triggerUpgrade?.({ feature: 'credits', message: msg, upgrade_to: 'pro' });
        toast.error(msg, {
          id: 'no-credits', duration: 5000,
          style: { background: 'rgba(76,5,25,0.92)', color: '#fee2e2', border: '1px solid rgba(244,63,94,0.6)' },
        });
        setMessages(p => p.slice(0, -1));
        setStreaming(false);
        refreshCredits?.();
        return;
      }
      // Credit toast is now shown in processStream with actual word count
      await processStream(res);
      refreshSub?.();
      refreshCredits?.();
    } catch (e) {
      retainVisualPreview();
      if (stoppedRef.current) {
        const partial = streamBufferRef.current;
        if (partial.trim() && !visualRequestInfo(text)) setMessages(p => [...p, {
          role: 'assistant', content: partial, timestamp: new Date().toISOString(), stopped: true,
        }]);
        toast.info('Reply stopped');
        return;
      }
      console.error(e);
      if (e.code === 'SESSION_EXPIRED') setMessages(p => p.slice(0, -1));
      setInput(text);
      setReplyError(e.name === 'AbortError' ? 'The tutor timed out. Retry your question.' : e.message || 'The tutor could not reply.');
      toast.error(e.name === 'AbortError' ? 'The tutor took too long to respond. Please try again.' :
        e.message || 'The tutor could not reply. Please try again.', { id: 'tutor-error', duration: 6000 });
    } finally {
      activeRequestRef.current = null;
      sendingRef.current = false;
      clearTimeout(timeout);
      if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
      streamBufferRef.current = '';
      setStreamingContent('');
      setStreaming(false);
      setVisualRequest(null); setVisualReady(false);
      refreshCredits?.();
    }
  };

  const SUGGESTIONS = ['Explain with a simple example', 'Give me a quick quiz', 'Why does this work?', 'Summarize key points'];

  if (!paramId && !session) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <h1 className="text-white font-heading font-bold flex items-center gap-2"><Sparkles size={20} className="text-cyan-400" /> AI Tutor</h1>
          {sessions.length > 0 && (
            <button onClick={() => setShowSessions(!showSessions)} data-testid="sessions-toggle"
              className="text-sm text-cyan-400 font-body flex items-center gap-1 hover:text-cyan-300">
              <MessageSquare size={15} /> History
            </button>
          )}
        </div>
        <SessionSetup onCreated={handleCreated} prefill={prefill} />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Quiz Modal */}
      {quizModal && (
        <InteractiveQuizModal
          quizData={quizModal.quizData}
          onClose={() => { setQuizModal(null); refreshCredits?.(); }}
          onComplete={(results) => {
            refreshCredits?.();
            axios.get(`${API}/quiz/topic-mastery`, { params: { topic: session.chapter, subject: session.subject }, withCredentials: true })
              .then(r => setChapterMastery(r.data)).catch(() => {});
            // Build a message that sends the quiz results to the AI tutor for validation
            const topic = session?.chapter || session?.subject || 'this topic';
            const wrongAnswers = results.results?.filter(r => !r.correct) || [];
            let msg = `I just finished a quiz on **${topic}**. My score: **${results.correct_count}/${results.total_questions} (${results.score}%)**.\n\n`;
            if (wrongAnswers.length > 0) {
              msg += `I got ${wrongAnswers.length} question(s) wrong. Please explain these:\n\n`;
              wrongAnswers.forEach((r, i) => {
                msg += `**Q${i + 1}:** ${r.question}\n`;
                msg += `My answer: ${r.user_answer || '(skipped)'} | Correct answer: ${r.correct_answer}\n\n`;
              });
              msg += `Please explain why those answers are correct and help me understand the concepts I missed.`;
            } else {
              msg += `I got all questions correct! Can you give me a slightly harder follow-up question or introduce the next concept?`;
            }
            sendMessage(msg);
          }}
        />
      )}

      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 glass flex items-center gap-3">
        <button onClick={() => nav(-1)} data-testid="back-btn"
          className="p-1.5 rounded-lg hover:bg-white/5 text-zinc-500 hover:text-white transition-colors">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-white font-heading font-bold text-sm truncate">{session?.subject}</h2>
          <p className="text-zinc-500 text-xs font-body truncate">
            {session?.chapter} • {isNios ? 'Secondary Course' : `Class ${session?.class_level}`}
          </p>
        </div>

        {/* Chapter Mastery Badge */}
        {chapterMastery && (
          <div
            data-testid="chapter-mastery-badge"
            className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-body font-bold border ${
              chapterMastery.mastery_pct >= 70
                ? 'bg-green-500/15 text-green-400 border-green-500/30'
                : chapterMastery.mastery_pct >= 40
                ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                : 'bg-zinc-700/50 text-zinc-400 border-zinc-600/40'
            }`}
            title={`Chapter mastery: ${chapterMastery.mastery_pct}%`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            {chapterMastery.mastery_pct}% mastery
          </div>
        )}
        <button onClick={() => { localStorage.removeItem('aceit_last_chat_session'); setSession(null); setMessages([]); nav('/chat', { replace: true }); }} data-testid="new-chat-btn"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-body hover:bg-cyan-500/20 transition-all">
          <Plus size={14} /> New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !streaming && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full gap-3 text-center px-4">
            <div className="w-10 h-10 rounded-full border border-violet-500/25 bg-violet-500/10 flex items-center justify-center">
              <Sparkles size={18} className="text-violet-400" />
            </div>
            <p className="text-zinc-300 text-sm font-body font-semibold">Session Started</p>
            <p className="text-zinc-600 text-xs font-body">Ask anything about <span className="text-zinc-400">{session?.chapter}</span></p>
          </motion.div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.timestamp || i}
            msg={msg}
            isStreaming={false}
            isNios={isNios}
            feedbackState={feedbackMap[msg.message_id]}
            onFeedback={sendFeedback}
            onDetailRequest={() => sendMessage('Explain in detail')}
          />
        ))}
        {streaming && visualRequest && <VisualReplyProgress request={visualRequest} content={streamingContent} ready={visualReady} />}
        {streaming && !visualRequest && streamingContent && (
          <MessageBubble
            msg={{ role: 'assistant', content: streamingContent }}
            isStreaming={true}
            isNios={isNios}
            feedbackState={undefined}
            onFeedback={() => {}}
            onDetailRequest={() => {}}
          />
        )}
        {streaming && !visualRequest && !streamingContent && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-600 flex-shrink-0 flex items-center justify-center">
              <Sparkles size={14} className="text-white" />
            </div>
            <div className="message-ai px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={`dot-${i}`} className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length < 3 && !streaming && session && (
        <div className="px-4 pb-2 flex gap-2 overflow-x-auto no-scrollbar">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => sendMessage(s)}
              className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-body glass border border-white/10 text-zinc-400 hover:text-white hover:border-white/20 transition-all">
              {s}
            </button>
          ))}
        </div>
      )}

      {replyError && <div role="alert" className="mx-4 mb-2 rounded-xl border border-amber-400/30 p-3 text-sm text-amber-200">
        {replyError} <button onClick={() => sendMessage()} disabled={streaming} className="ml-2 underline">Retry question</button>
      </div>}
      {/* Input */}
      <div className="ace-prompt p-4 border-t border-white/5 glass">
        <div className="mb-2">
          <button type="button" data-testid="visualize-toggle" aria-expanded={visualizeOpen}
            onClick={() => setVisualizeOpen(open => !open)}
            className="inline-flex items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-500/10 px-3 py-2 text-xs text-violet-300">
            <Sparkles size={14} /> Visualize <ChevronDown size={13} />
          </button>
          {visualizeOpen && <div className="mt-2 rounded-xl border border-white/10 bg-zinc-950 p-3">
            <p className="text-xs text-zinc-400 mb-2">Choose a study format for this chapter. Add an optional focus in the prompt below.</p>
            <div className="flex flex-wrap gap-2">
              <button type="button" data-testid="visualize-mindmap" disabled={streaming || !session}
                onClick={() => {
                  if (streaming || sendingRef.current || !session) return;
                  const prompt = makeMindMapPrompt(session.chapter, cleanVisualFocus(input));
                  setVisualizeOpen(false); setInput(''); sendMessage(prompt);
                }}
                className="rounded-lg px-3 py-2 text-xs bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 disabled:opacity-40">Mind Map</button>
              <button type="button" data-testid="visualize-flowchart" disabled={streaming || !session}
                onClick={() => {
                  if (streaming || sendingRef.current || !session) return;
                  const prompt = makeFlowchartPrompt(session.chapter, cleanVisualFocus(input));
                  setVisualizeOpen(false); setInput(''); sendMessage(prompt);
                }}
                className="rounded-lg px-3 py-2 text-xs bg-violet-500/15 border border-violet-500/30 text-violet-300 disabled:opacity-40">Flowchart</button>
              {STUDY_FORMATS.map(format =>
                <button key={format.id} type="button" data-testid={`visualize-${format.id}`} disabled={streaming || !session}
                  onClick={() => {
                    if (streaming || sendingRef.current || !session) return;
                    const prompt = makeStudyVisualPrompt(session.chapter, cleanVisualFocus(input), format.id);
                    setVisualizeOpen(false); setInput(''); sendMessage(prompt);
                  }} className="rounded-lg px-3 py-2 text-xs bg-teal-500/15 border border-teal-500/30 text-teal-300 disabled:opacity-40">
                  {format.label}
                </button>)}
            </div>
            <p className="mt-2 text-[11px] text-zinc-500">Uses normal tutor credits. Finished topics appear as they are prepared.</p>
          </div>}
        </div>
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea data-testid="chat-input"
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
              placeholder="Ask your AI tutor anything..."
              rows={1}
              className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body resize-none overflow-hidden"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
          </div>
          {streaming ? (
            <button onClick={stopReply} data-testid="stop-response-btn" aria-label="Stop generating response" title="Stop response"
              className="w-11 h-11 rounded-xl bg-rose-500 hover:bg-rose-400 flex items-center justify-center transition-all flex-shrink-0">
              <Square size={16} fill="currentColor" className="text-white" />
            </button>
          ) : (
          <button onClick={() => sendMessage()} disabled={!input.trim()} data-testid="send-message-btn"
            className="w-11 h-11 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 flex items-center justify-center transition-all flex-shrink-0">
            <Send size={18} className="text-black" />
          </button>
          )}
        </div>
      </div>
    </div>
  );
}






