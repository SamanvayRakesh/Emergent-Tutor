import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Plus, BookOpen, ChevronDown, Trash2, Sparkles, CheckCircle, XCircle, MessageSquare, Brain, ArrowLeft, Youtube, ExternalLink, Zap } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useCredits } from '../contexts/CreditsContext';
import { toast } from 'sonner';
import { MathText } from './MathRenderer';
import InteractiveQuizModal from './InteractiveQuizModal';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUBJECT_COLORS = {
  Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4',
  Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b',
  'Social Science': '#3b82f6', 'Computer Science': '#ef4444'
};

function parseQuizBlocks(content) {
  const parts = [];
  // Combined regex: matches either [QUIZ]...[/QUIZ] or [YOUTUBE]...[/YOUTUBE]
  const regex = /\[QUIZ\]([\s\S]*?)\[\/QUIZ\]|\[YOUTUBE\]([\s\S]*?)\[\/YOUTUBE\]/g;
  let lastIdx = 0, match;
  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIdx) parts.push({ type: 'text', content: content.slice(lastIdx, match.index) });
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
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < content.length) parts.push({ type: 'text', content: content.slice(lastIdx) });
  return parts;
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

function MessageBubble({ msg, isStreaming }) {
  const isUser = msg.role === 'user';
  const parts = !isUser ? parseQuizBlocks(msg.content) : null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-1 ${isUser ? 'bg-cyan-500 text-black' : 'bg-gradient-to-br from-violet-500 to-fuchsia-600'}`}>
        {isUser ? <span className="text-xs font-heading font-black">U</span> : <Sparkles size={14} className="text-white" />}
      </div>

      <div className={`max-w-[82%] ${isUser ? 'message-user' : 'message-ai'} p-3.5`}>
        {isUser ? (
          <p className="text-white text-sm font-body leading-relaxed">{msg.content}</p>
        ) : (
          <div className={`text-sm font-body ${isStreaming ? 'streaming-cursor' : ''}`}>
            {parts?.map((part, i) =>
              part.type === 'quiz' ? (
                <QuizCard key={`quiz-${i}`} data={part.data} />
              ) : part.type === 'youtube' ? (
                <YouTubeCard key={`yt-${i}`} query={part.query} />
              ) : (
                <div key={`text-${i}`} className="markdown-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Render math in inline code and paragraphs
                      p: ({ children }) => (
                        <p className="mb-2 last:mb-0 leading-relaxed">
                          {typeof children === 'string' ? <MathText text={children} /> : children}
                        </p>
                      ),
                      code: ({ inline, children }) => {
                        const text = String(children).trim();
                        // Detect LaTeX-like patterns
                        if (inline && (text.includes('\\frac') || text.includes('\\sqrt') || text.startsWith('$'))) {
                          return <MathText text={`$${text}$`} />;
                        }
                        return inline
                          ? <code className="bg-black/30 text-cyan-300 px-1 py-0.5 rounded text-xs">{children}</code>
                          : <pre className="bg-black/30 text-cyan-300 p-3 rounded-xl text-xs overflow-x-auto my-2"><code>{children}</code></pre>;
                      },
                    }}
                  >{part.content}</ReactMarkdown>
                </div>
              )
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
            <Sparkles size={14} /> Class {userClass} — your active grade
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
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const [quizModal, setQuizModal] = useState(null); // {quizData}
  const bottomRef = useRef(null);

  const loadSession = useCallback(async (sid) => {
    try {
      const { data } = await axios.get(`${API}/chat/sessions/${sid}`, { withCredentials: true });
      setSession(data.session);
      setMessages(data.messages);
    } catch { nav('/chat', { replace: true }); }
  }, [nav]);

  useEffect(() => {
    if (paramId) loadSession(paramId);
    axios.get(`${API}/chat/sessions`, { withCredentials: true }).then(r => setSessions(r.data)).catch(() => {});
  }, [paramId, loadSession]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleCreated = (newSession) => {
    setSessions(p => [newSession, ...p]);
    setSession(newSession);
    setMessages([]);
    // Clear prefill state so back-nav doesn't re-trigger
    nav(`/chat/${newSession.session_id}`, { replace: true, state: null });
  };

  const processStream = async (res) => {
    if (!res.ok) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '', full = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const d = JSON.parse(line.slice(6));
            if (d.type === 'chunk') { full += d.content; setStreamingContent(full); }
            if (d.type === 'done') {
              setMessages(p => [...p, { role: 'assistant', content: full, timestamp: new Date().toISOString() }]);
              setStreamingContent('');
              // Show accurate credit deduction
              if (d.credits_used) {
                toast.success(`−${d.credits_used} credits (${d.word_count || 0} words)`, {
                  id: 'credit-deduct', duration: 1800,
                  style: { background: 'rgba(30,27,75,0.85)', color: '#fcd34d', border: '1px solid rgba(251,191,36,0.4)', fontSize: '13px' },
                  icon: <Zap size={14} className="text-yellow-400" />,
                });
              }
            }
          } catch {}
        }
      }
    }
  };

  // Detect quiz intent and auto-open quiz modal
  const QUIZ_INTENTS = ['give me a quiz', 'quiz me', 'test me', 'practice quiz', 'quick quiz', 'start a quiz', 'quiz on this'];
  const isQuizIntent = (text) => QUIZ_INTENTS.some(q => text.toLowerCase().includes(q));

  const openQuizModal = useCallback(async () => {
    if (!session) return false;
    try {
      const { data } = await axios.post(`${API}/quiz/generate`, {
        class_level: session.class_level,
        subject: session.subject,
        chapter: session.chapter,
        topic: session.chapter,   // use the actual chapter as quiz topic
        num_questions: 5,
      }, { withCredentials: true });
      setQuizModal({ quizData: data });
      return true;
    } catch {
      return false;
    }
  }, [session]);

  const sendMessage = async (forced) => {
    const text = (forced !== undefined ? forced : input).trim();
    if (!text || streaming || !session) return;
    if (forced === undefined) setInput('');

    // Detect quiz intent → open quiz modal
    if (isQuizIntent(text)) {
      setMessages(p => [...p, { role: 'user', content: text, timestamp: new Date().toISOString() }]);
      const opened = await openQuizModal();
      if (opened) return;
      // Fallback: continue to send as chat if quiz generation fails
    }

    setMessages(p => [...p, { role: 'user', content: text, timestamp: new Date().toISOString() }]);
    setStreaming(true);
    setStreamingContent('');

    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat/sessions/${session.session_id}/message`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include', body: JSON.stringify({ content: text })
      });
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
    } catch (e) { console.error(e); setStreamingContent(''); }
    setStreaming(false);
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
        <button onClick={() => nav('/chat')} data-testid="back-btn"
          className="p-1.5 rounded-lg hover:bg-white/5 text-zinc-500 hover:text-white transition-colors">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-white font-heading font-bold text-sm truncate">{session?.subject}</h2>
          <p className="text-zinc-500 text-xs font-body truncate">{session?.chapter} • Class {session?.class_level}</p>
        </div>
        <button onClick={() => nav('/chat')} data-testid="new-chat-btn"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-body hover:bg-cyan-500/20 transition-all">
          <Plus size={14} /> New
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
          <MessageBubble key={msg.timestamp || i} msg={msg} isStreaming={false} />
        ))}
        {streaming && streamingContent && (
          <MessageBubble msg={{ role: 'assistant', content: streamingContent }} isStreaming={true} />
        )}
        {streaming && !streamingContent && (
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

      {/* Input */}
      <div className="p-4 border-t border-white/5 glass">
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
          <button onClick={sendMessage} disabled={!input.trim() || streaming} data-testid="send-message-btn"
            className="w-11 h-11 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 flex items-center justify-center transition-all flex-shrink-0">
            <Send size={18} className="text-black" />
          </button>
        </div>
      </div>
    </div>
  );
}
