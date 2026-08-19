import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquarePlus, X, Bug, Lightbulb, MessageCircle, Send, CheckCircle, CornerDownRight, Inbox } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPES = [
  { id: 'bug',        label: 'Bug Report',  icon: Bug,          color: '#f43f5e', bg: 'bg-rose-500/10 border-rose-500/30' },
  { id: 'suggestion', label: 'Suggestion',  icon: Lightbulb,    color: '#fbbf24', bg: 'bg-amber-500/10 border-amber-500/30' },
  { id: 'general',    label: 'General',     icon: MessageCircle, color: '#22d3ee', bg: 'bg-cyan-500/10 border-cyan-500/30' },
];

export default function FeedbackModal({ externalOpen, onExternalClose }) {
  const [open, setOpen]           = useState(externalOpen || false);
  const [tab, setTab]             = useState('send');   // 'send' | 'replies'
  const [type, setType]           = useState('general');
  const [message, setMessage]     = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone]           = useState(false);
  const [myFeedback, setMyFeedback] = useState([]);
  const [loadingReplies, setLoadingReplies] = useState(false);

  // Sync with external control
  if (externalOpen && !open) setOpen(true);

  const handleClose = () => {
    setOpen(false);
    setDone(false);
    setMessage('');
    setType('general');
    setTab('send');
    onExternalClose?.();
  };

  const fetchMyFeedback = async () => {
    setLoadingReplies(true);
    try {
      const { data } = await axios.get(`${API}/feedback/my-feedback`, { withCredentials: true });
      setMyFeedback(data.feedback || []);
    } catch { /* silently fail */ }
    finally { setLoadingReplies(false); }
  };

  useEffect(() => {
    if (open && tab === 'replies') fetchMyFeedback();
  }, [open, tab]);

  const submit = async () => {
    if (!message.trim() || message.trim().length < 5) {
      toast.error('Please write at least 5 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/feedback`, { type, message }, { withCredentials: true });
      setDone(true);
      setTimeout(() => handleClose(), 2000);
    } catch (e) {
      toast.error('Could not send feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const repliedCount = myFeedback.filter(f => f.admin_reply).length;

  return (
    <AnimatePresence>
      {open && (
          <div className="fixed inset-0 z-[120] flex items-end sm:items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, y: 40, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.97 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-sm bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
              data-testid="feedback-modal"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <MessageSquarePlus size={18} className="text-cyan-400" />
                  <h3 className="text-white font-heading font-bold text-sm">Feedback</h3>
                </div>
                <button onClick={handleClose} data-testid="feedback-close-btn" className="p-1 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-all">
                  <X size={16} />
                </button>
              </div>

              {/* Tab switcher */}
              <div className="flex border-b border-white/5">
                <button
                  data-testid="tab-send-feedback"
                  onClick={() => setTab('send')}
                  className={`flex-1 py-2.5 text-xs font-body font-semibold transition-all ${tab === 'send' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-zinc-500 hover:text-zinc-300'}`}>
                  Send Feedback
                </button>
                <button
                  data-testid="tab-my-replies"
                  onClick={() => setTab('replies')}
                  className={`flex-1 py-2.5 text-xs font-body font-semibold transition-all flex items-center justify-center gap-1 ${tab === 'replies' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-zinc-500 hover:text-zinc-300'}`}>
                  My Replies
                  {repliedCount > 0 && (
                    <span className="bg-cyan-500 text-black text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">{repliedCount}</span>
                  )}
                </button>
              </div>

              <div className="p-4">
                {/* ── SEND TAB ── */}
                {tab === 'send' && (
                  done ? (
                    <div className="flex flex-col items-center gap-3 py-6">
                      <CheckCircle size={36} className="text-emerald-400" />
                      <p className="text-white font-body font-semibold text-sm">Feedback sent!</p>
                      <p className="text-zinc-500 text-xs font-body text-center">Thank you for helping us improve AceIt AI.</p>
                    </div>
                  ) : (
                    <>
                      <p className="text-zinc-500 text-xs font-body mb-2 uppercase tracking-widest">Type</p>
                      <div className="flex gap-2 mb-4">
                        {TYPES.map(({ id, label, icon: Icon, color, bg }) => (
                          <button
                            key={id}
                            onClick={() => setType(id)}
                            className={`flex-1 flex flex-col items-center gap-1 py-2.5 rounded-xl border text-xs font-body font-semibold transition-all ${
                              type === id ? `${bg} border-current` : 'bg-white/5 border-white/5 text-zinc-500 hover:text-zinc-300'
                            }`}
                            style={{ color: type === id ? color : undefined }}
                          >
                            <Icon size={14} />
                            {label}
                          </button>
                        ))}
                      </div>

                      <p className="text-zinc-500 text-xs font-body mb-2 uppercase tracking-widest">Message</p>
                      <textarea
                        value={message}
                        onChange={e => setMessage(e.target.value)}
                        placeholder="Describe your issue or suggestion..."
                        maxLength={2000}
                        rows={4}
                        data-testid="feedback-message-input"
                        className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm font-body placeholder-zinc-600 resize-none focus:outline-none focus:border-cyan-500/50 transition-all mb-1"
                      />
                      <p className="text-zinc-600 text-xs font-body text-right mb-4">{message.length}/2000</p>

                      <button
                        onClick={submit}
                        disabled={submitting || message.trim().length < 5}
                        data-testid="feedback-submit-btn"
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-cyan-500 text-black font-heading font-bold text-sm disabled:opacity-50 hover:bg-cyan-400 transition-all"
                      >
                        <Send size={14} />
                        {submitting ? 'Sending...' : 'Send Feedback'}
                      </button>
                    </>
                  )
                )}

                {/* ── REPLIES TAB ── */}
                {tab === 'replies' && (
                  loadingReplies ? (
                    <div className="py-8 text-center text-zinc-500 text-xs font-body">Loading…</div>
                  ) : myFeedback.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 py-8">
                      <Inbox size={28} className="text-zinc-600" />
                      <p className="text-zinc-500 text-xs font-body text-center">No feedback submitted yet.</p>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                      {myFeedback.map(fb => (
                        <div key={fb.feedback_id} data-testid={`my-feedback-${fb.feedback_id}`}
                          className="bg-zinc-800/60 rounded-xl p-3 border border-white/5">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full font-body ${
                              fb.type === 'bug'        ? 'bg-rose-500/20 text-rose-400' :
                              fb.type === 'suggestion' ? 'bg-amber-500/20 text-amber-400' :
                                                         'bg-cyan-500/20 text-cyan-400'
                            }`}>{fb.type === 'bug' ? 'Bug' : fb.type === 'suggestion' ? 'Suggestion' : 'General'}</span>
                            <span className="text-zinc-600 text-[11px] font-body">{new Date(fb.created_at).toLocaleDateString()}</span>
                          </div>
                          <p className="text-zinc-300 text-xs font-body leading-relaxed">{fb.message}</p>

                          {fb.admin_reply ? (
                            <div className="mt-2.5 pl-2.5 border-l-2 border-cyan-500/50">
                              <div className="flex items-center gap-1 mb-0.5">
                                <CornerDownRight size={10} className="text-cyan-400" />
                                <span className="text-cyan-400 text-[10px] font-semibold font-body">Reply from Team</span>
                              </div>
                              <p className="text-white text-xs font-body leading-relaxed">{fb.admin_reply}</p>
                            </div>
                          ) : (
                            <p className="mt-2 text-zinc-600 text-[11px] font-body italic">Awaiting reply…</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
  );
}
