import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Mail, Lock, User, ArrowRight, Eye, EyeOff, Sparkles, CheckCircle2, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthPage() {
  const [tab, setTab] = useState('login');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ email: '', password: '', name: '' });
  const [registerSuccess, setRegisterSuccess] = useState(false); // email verification pending
  const [unverifiedEmail, setUnverifiedEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendDone, setResendDone] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();

  const formatError = (detail) => {
    if (!detail) return 'Something went wrong';
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && detail.message) return detail.message;
    if (Array.isArray(detail)) return detail.map(e => e?.msg || JSON.stringify(e)).join(' ');
    return String(detail);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const endpoint = tab === 'login' ? '/auth/login' : '/auth/register';
      const payload = tab === 'login' ? { email: form.email, password: form.password } : form;
      const { data } = await axios.post(`${API}${endpoint}`, payload, { withCredentials: true });

      if (data.requires_verification) {
        // Registration successful — show email verification pending state
        setRegisterSuccess(true);
        return;
      }
      login(data);
      nav('/', { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      // Handle email not verified on login
      if (detail?.code === 'EMAIL_NOT_VERIFIED') {
        setUnverifiedEmail(detail.email || form.email);
        setError(detail.message || 'Email not verified. Please check your inbox.');
        return;
      }
      setError(formatError(detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    const email = unverifiedEmail || form.email;
    if (!email) return;
    setResending(true);
    try {
      await axios.post(`${API}/auth/resend-verification`, { email });
      setResendDone(true);
    } catch {
      setResendDone(true);
    } finally {
      setResending(false);
    }
  };

  const handleGoogle = () => {
    const redirectUrl = window.location.origin + '/';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  // Email verification pending state
  if (registerSuccess) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="text-center mb-8">
            <span className="font-heading font-black text-2xl">
              <span className="text-white">AceIt</span><span style={{ color: '#dc2626' }}> AI</span>
            </span>
          </div>
          <div className="glass rounded-2xl p-8 shadow-2xl text-center" data-testid="verify-email-pending">
            <CheckCircle2 size={52} className="mx-auto mb-4" style={{ color: '#22c55e' }} />
            <h2 className="text-white text-xl font-heading font-bold mb-2">Check your email!</h2>
            <p className="text-zinc-400 text-sm mb-2">
              We sent a verification link to <span className="text-white font-medium">{form.email}</span>
            </p>
            <p className="text-zinc-500 text-xs mb-6">Click the link to activate your account. Link expires in 24 hours.</p>
            {!resendDone ? (
              <button onClick={handleResendVerification} disabled={resending} data-testid="resend-email-btn"
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1.5 mx-auto">
                <RefreshCw size={14} className={resending ? 'animate-spin' : ''} />
                {resending ? 'Sending…' : 'Resend email'}
              </button>
            ) : (
              <p className="text-green-400 text-xs">Resent! Check your inbox again.</p>
            )}
            <button onClick={() => { setRegisterSuccess(false); setTab('login'); }}
              className="mt-4 text-zinc-500 text-xs hover:text-zinc-300 transition-colors block mx-auto">
              Back to Sign In
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center relative overflow-hidden px-4">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/8 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/8 rounded-full blur-3xl pointer-events-none" />
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center">
              <BookOpen size={20} className="text-white" />
            </div>
            <span className="font-heading font-black text-2xl">
              <span className="text-white">AceIt</span><span style={{ color: '#dc2626' }}> AI</span>
            </span>
          </div>
          <p className="text-zinc-500 text-sm font-body">Your AI-powered CBSE tutor</p>
        </div>

        <div className="glass rounded-2xl p-7 shadow-2xl">
          <div className="flex rounded-xl bg-zinc-900 p-1 mb-6 gap-1">
            {['login', 'register'].map(t => (
              <button key={t} data-testid={`auth-tab-${t}`}
                onClick={() => { setTab(t); setError(''); setUnverifiedEmail(''); setResendDone(false); }}
                className={`flex-1 py-2 rounded-lg text-sm font-body font-semibold transition-all ${tab === t ? 'bg-cyan-500 text-black shadow-lg' : 'text-zinc-400 hover:text-white'}`}>
                {t === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <button onClick={handleGoogle} data-testid="google-login-btn"
            className="w-full flex items-center justify-center gap-3 py-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-white text-sm font-body font-medium transition-all mb-4">
            <svg width="18" height="18" viewBox="0 0 18 18">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" />
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" />
              <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" />
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" />
            </svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-zinc-600 text-xs font-body">or continue with email</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <AnimatePresence>
              {tab === 'register' && (
                <motion.div key="name" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                  <div className="relative">
                    <User size={16} className="absolute left-3 top-3.5 text-zinc-500" />
                    <input data-testid="name-input" type="text" placeholder="Your name" required
                      value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                      className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3.5 text-zinc-500" />
              <input data-testid="email-input" type="email" placeholder="Email address" required
                value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3.5 text-zinc-500" />
              <input data-testid="password-input" type={showPass ? 'text' : 'password'} placeholder="Password" required
                value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-10 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
              <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-3.5 text-zinc-500 hover:text-zinc-300 transition-colors">
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                data-testid="auth-error" className="text-red-400 text-xs font-body p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                <p>{error}</p>
                {unverifiedEmail && !resendDone && (
                  <button onClick={handleResendVerification} disabled={resending} data-testid="resend-verification-link"
                    className="mt-2 text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1 transition-colors">
                    <RefreshCw size={12} className={resending ? 'animate-spin' : ''} />
                    {resending ? 'Sending…' : 'Resend verification email'}
                  </button>
                )}
                {resendDone && <p className="mt-1 text-green-400 text-xs">Verification email resent!</p>}
              </motion.div>
            )}

            <button type="submit" data-testid="auth-submit-btn" disabled={loading}
              className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-heading font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2">
              {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <>{tab === 'login' ? 'Sign In' : 'Create Account'}<ArrowRight size={16} /></>}
            </button>
          </form>

          {tab === 'register' && (
            <p className="text-zinc-600 text-xs text-center mt-4 font-body">By signing up, you agree to learn and grow with AceIt AI</p>
          )}
        </div>

        <div className="mt-6 grid grid-cols-3 gap-3">
          {[['Adaptive AI', 'Personalized teaching'], ['CBSE Class 6-12', 'Full curriculum'], ['Gamified', 'XP & achievements']].map(([t, d]) => (
            <div key={t} className="text-center p-3 rounded-xl glass border border-white/5">
              <p className="text-cyan-400 text-xs font-body font-semibold">{t}</p>
              <p className="text-zinc-600 text-xs font-body mt-0.5">{d}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
