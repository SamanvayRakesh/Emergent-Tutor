import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Eye, EyeOff, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EMAIL_REGEX = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
const SPECIAL_CHAR_REGEX = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/;

export default function AuthPage() {
  const [tab, setTab]           = useState('login');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [form, setForm]         = useState({ email: '', password: '', name: '', school: '' });
  const [schools, setSchools]   = useState([]);
  const { login } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    if (tab === 'register' && schools.length === 0) {
      axios.get(`${API}/auth/schools`)
        .then(r => setSchools(r.data.schools || []))
        .catch(() => {});
    }
  }, [tab]); // eslint-disable-line

  const formatError = (detail) => {
    if (!detail) return 'Something went wrong';
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && detail.message) return detail.message;
    if (Array.isArray(detail)) return detail.map(e => e?.msg || JSON.stringify(e)).join(' ');
    return String(detail);
  };

  // Password strength checker
  const pwStrength = (pw) => {
    if (!pw) return null;
    const hasLen = pw.length >= 6;
    const hasSpecial = SPECIAL_CHAR_REGEX.test(pw);
    if (hasLen && hasSpecial) return 'strong';
    if (hasLen || hasSpecial) return 'medium';
    return 'weak';
  };
  const strength = tab === 'register' ? pwStrength(form.password) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!EMAIL_REGEX.test(form.email.trim())) {
      setError('Invalid email format. Use the format: name@domain.tld');
      return;
    }

    if (tab === 'register') {
      if (!form.school) { setError('Please select your school to continue.'); return; }
      if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return; }
      if (!SPECIAL_CHAR_REGEX.test(form.password)) { setError('Password must contain at least one special character (e.g. @, #, !, $).'); return; }
    }

    setLoading(true);
    try {
      const endpoint = tab === 'login' ? '/auth/login' : '/auth/register';
      const payload  = tab === 'login'
        ? { email: form.email, password: form.password }
        : form;
      const { data } = await axios.post(`${API}${endpoint}`, payload, { withCredentials: true });
      login(data);
      nav('/', { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 429) { setError(formatError(detail)); return; }
      setError(formatError(detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    const redirectUrl = window.location.origin + '/';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  // ── Main auth form ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center relative overflow-hidden px-4">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/8 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/8 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <img src="/aceit-logo.png" alt="Ace It" className="h-16 w-auto object-contain" />
          </div>
          <p className="text-zinc-500 text-sm font-body">Your AI-powered exam prep tutor</p>
        </div>

        <div className="glass rounded-2xl p-7 shadow-2xl">
          {/* Tab switcher */}
          <div className="flex rounded-xl bg-zinc-900 p-1 mb-6 gap-1">
            {['login', 'register'].map(t => (
              <button key={t} data-testid={`auth-tab-${t}`}
                onClick={() => { setTab(t); setError(''); }}
                className={`flex-1 py-2 rounded-lg text-sm font-body font-semibold transition-all ${tab === t ? 'bg-cyan-500 text-black shadow-lg' : 'text-zinc-400 hover:text-white'}`}>
                {t === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          {/* Google */}
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
            {tab === 'register' && (
              <div>
                <div className="relative">
                  <User size={16} className="absolute left-3 top-3.5 text-zinc-500" />
                  <input data-testid="name-input" type="text" placeholder="Your name" required
                    name="name" autoComplete="name"
                    value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                    className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
                </div>
              </div>
            )}

            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3.5 text-zinc-500" />
              <input data-testid="email-input" type="email" placeholder="Email address" required
                name="email" autoComplete="email"
                value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3.5 text-zinc-500" />
              <input data-testid="password-input" type={showPass ? 'text' : 'password'} placeholder="Password" required
                name="password" autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-9 pr-10 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all font-body" />
              <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-3.5 text-zinc-500 hover:text-zinc-300 transition-colors">
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Password strength — register only */}
            {tab === 'register' && form.password && (
              <div className="space-y-1.5">
                <div className="flex gap-1">
                  {['weak', 'medium', 'strong'].map((level, i) => (
                    <div key={level} className={`h-1 flex-1 rounded-full transition-all ${
                      strength === 'strong' ? 'bg-green-500' :
                      strength === 'medium' && i < 2 ? 'bg-amber-400' :
                      strength === 'weak' && i === 0 ? 'bg-red-500' : 'bg-zinc-700'
                    }`} />
                  ))}
                </div>
                <p className={`text-xs font-body flex items-center gap-1 ${
                  strength === 'strong' ? 'text-green-400' : strength === 'medium' ? 'text-amber-400' : 'text-red-400'
                }`}>
                  <Info size={11} />
                  {strength === 'strong' ? 'Strong password' :
                   strength === 'medium' ? 'Add ' + (form.password.length < 6 ? 'more characters and a symbol' : 'a special character (!@#$...)') :
                   'Min 6 characters + one symbol required'}
                </p>
              </div>
            )}

            {/* School selection — register only */}
            {tab === 'register' && (
              <div className="space-y-2">
                <p className="text-zinc-400 text-xs font-body font-semibold mb-2 flex items-center gap-1.5">
                  <BookOpen size={12} className="text-cyan-400" /> Select Your School
                </p>
                {schools.map(s => (
                  <button key={s.id} type="button"
                    data-testid={`school-card-${s.id}`}
                    disabled={!s.available}
                    onClick={() => s.available && setForm(p => ({ ...p, school: s.id }))}
                    className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-body transition-all relative ${
                      !s.available
                        ? 'border-white/5 bg-zinc-900/50 text-zinc-600 cursor-not-allowed'
                        : form.school === s.id
                          ? 'border-cyan-500/60 bg-cyan-500/10 text-white shadow-md shadow-cyan-500/10'
                          : 'border-white/10 bg-zinc-900 text-zinc-300 hover:border-white/20 hover:text-white'
                    }`}>
                    <span className="font-medium">{s.name}</span>
                    {!s.available && (
                      <span className="ml-2 text-[10px] bg-zinc-800 text-zinc-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                    )}
                    {form.school === s.id && (
                      <CheckCircle2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-400" />
                    )}
                  </button>
                ))}

                {/* Permanent warning shown once a school is selected */}
                {form.school && (
                  <div className="mt-3 flex gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-body">
                    <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                    <p>Your school selection is <strong>permanent</strong>. Changing it later requires admin approval. Choose carefully.</p>
                  </div>
                )}
              </div>
            )}

            {/* Error */}
            {error && (
              <div data-testid="auth-error"
                className="text-red-400 text-xs font-body p-3 bg-red-500/10 rounded-lg border border-red-500/20 flex gap-2">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <p>{error}</p>
              </div>
            )}

            <button type="submit" data-testid="auth-submit-btn" disabled={loading}
              className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-heading font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2">
              {loading
                ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                : <>{tab === 'login' ? 'Sign In' : 'Create Account'}<ArrowRight size={16} /></>
              }
            </button>
          </form>

          {tab === 'register' && (
            <p className="text-zinc-600 text-xs text-center mt-4 font-body">
              By signing up, you agree to learn and grow with AceIt AI
            </p>
          )}
        </div>

        <div className="mt-6 grid grid-cols-3 gap-3">
          {[['Adaptive AI', 'Personalized teaching'], ['BNPS Curriculum', 'NCERT-verified'], ['Gamified', 'XP & achievements']].map(([t, d]) => (
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
