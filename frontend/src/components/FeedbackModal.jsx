import { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquarePlus, X, Bug, Lightbulb, MessageCircle, Send, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPES = [
  { id: 'bug',        label: 'Bug Report',  icon: Bug,          color: '#f43f5e', bg: 'bg-rose-500/10 border-rose-500/30' },
  { id: 'suggestion', label: 'Suggestion',  icon: Lightbulb,    color: '#fbbf24', bg: 'bg-amber-500/10 border-amber-500/30' },
  { id: 'general',    label: 'General',     icon: MessageCircle, color: '#22d3ee', bg: 'bg-cyan-500/10 border-cyan-500/30' },
];

export default function FeedbackModal() {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState('general');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async () => {
    if (!message.trim() || message.trim().length < 5) {
      toast.error('Please write at least 5 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/feedback`, { type, message }, { withCredentials: true });
      setDone(true);
      setTimeout(() => { setOpen(false); setDone(false); setMessage(''); setType('general'); }, 2000);
    } catch (e) {
      toast.error('Could not send feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {/* Floating trigger button */}
      <button
        onClick={() => setOpen(true)}
        data-testid="feedback-btn"
        title="Send Feedback"
        className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-zinc-800 border border-white/10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-700 hover:border-white/20 shadow-xl transition-all hover:scale-110"
      >
        <MessageSquarePlus size={20} />
      </button>

      {/* Modal */}
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
                  <h3 className="text-white font-heading font-bold text-sm">Send Feedback</h3>
                </div>
                <button onClick={() => setOpen(false)} className="p-1 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-all">
                  <X size={16} />
                </button>
              </div>

              <div className="p-4">
                {done ? (
                  <div className="flex flex-col items-center gap-3 py-6">
                    <CheckCircle size={36} className="text-emerald-400" />
                    <p className="text-white font-body font-semibold text-sm">Feedback sent!</p>
                    <p className="text-zinc-500 text-xs font-body text-center">Thank you for helping us improve AceIt AI.</p>
                  </div>
                ) : (
                  <>
                    {/* Type selector */}
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

                    {/* Message */}
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
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
