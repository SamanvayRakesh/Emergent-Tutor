import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, Mail, RefreshCw, Clock } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function EmailVerificationPage() {
  const [searchParams]   = useSearchParams();
  const navigate         = useNavigate();
  const token            = searchParams.get('token');

  const [status, setStatus]       = useState('verifying'); // verifying | success | error | expired | resend
  const [message, setMessage]     = useState('');
  const [email, setEmail]         = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendDone, setResendDone] = useState(false);
  const [cooldownSecs, setCooldownSecs] = useState(0);
  const timerRef = useRef(null);

  // Countdown timer for resend cooldown
  useEffect(() => {
    if (cooldownSecs > 0) {
      timerRef.current = setTimeout(() => setCooldownSecs(s => s - 1), 1000);
    }
    return () => clearTimeout(timerRef.current);
  }, [cooldownSecs]);

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setStatus('resend');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function verifyToken() {
    try {
      const { data } = await axios.get(`${API}/api/auth/verify-email`, { params: { token } });
      setStatus('success');
      setMessage(data.message || 'Email verified successfully. Welcome to AceIt AI.');
      setEmail(data.email || '');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'TOKEN_EXPIRED') {
        setStatus('expired');
        setResendEmail(detail.email || '');
        setMessage(detail.message || 'This verification link has expired. Please request a new verification email.');
      } else {
        setStatus('error');
        setMessage(detail?.message || detail || 'This verification link is invalid or has already been used.');
      }
    }
  }

  async function handleResend(e) {
    if (e) e.preventDefault();
    if (cooldownSecs > 0) return;
    setResending(true);
    try {
      const { data } = await axios.post(`${API}/api/auth/resend-verification`, { email: resendEmail });
      setResendDone(true);
      if (data?.cooldown_seconds) setCooldownSecs(data.cooldown_seconds);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'RESEND_COOLDOWN') {
        setCooldownSecs(detail.remaining_seconds || 60);
        // Don't set resendDone yet, let them try again after cooldown
      } else {
        setResendDone(true); // show success anyway to avoid enumeration
      }
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-heading font-black text-3xl text-white">
            AceIt<span style={{ color: '#dc2626' }}> AI</span>
          </h1>
        </div>

        <div className="glass-card rounded-2xl p-8 border border-white/10">

          {/* ── Verifying ─────────────────────────────── */}
          {status === 'verifying' && (
            <div className="text-center py-4" data-testid="verifying-state">
              <Loader2 size={48} className="mx-auto mb-4 text-blue-400 animate-spin" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Verifying your email…</h2>
              <p className="text-zinc-400 text-sm">Just a moment</p>
            </div>
          )}

          {/* ── Success ───────────────────────────────── */}
          {status === 'success' && (
            <div className="text-center py-4" data-testid="verification-success">
              <CheckCircle2 size={52} className="mx-auto mb-4" style={{ color: '#22c55e' }} />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Email Verified!</h2>
              <p className="text-zinc-300 text-sm mb-2">
                {message || 'Email verified successfully. Welcome to AceIt AI.'}
              </p>
              {email && <p className="text-zinc-500 text-xs mb-6">{email}</p>}
              <button
                data-testid="go-to-login-btn"
                onClick={() => navigate('/')}
                className="w-full py-3 rounded-xl font-heading font-bold text-white text-sm transition-all hover:opacity-90"
                style={{ background: '#dc2626' }}
              >
                Sign In Now
              </button>
            </div>
          )}

          {/* ── Error (invalid / used link) ───────────── */}
          {status === 'error' && (
            <div className="text-center py-4" data-testid="verification-error">
              <XCircle size={52} className="mx-auto mb-4 text-red-500" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Link Invalid</h2>
              <p className="text-zinc-400 text-sm mb-6">{message}</p>
              <button
                onClick={() => { setStatus('resend'); }}
                className="w-full py-3 rounded-xl font-heading font-bold text-white text-sm border border-white/20 hover:bg-white/5 transition-all"
              >
                Request New Verification Link
              </button>
            </div>
          )}

          {/* ── Expired ───────────────────────────────── */}
          {status === 'expired' && (
            <div className="text-center py-4" data-testid="verification-expired">
              <XCircle size={52} className="mx-auto mb-4 text-yellow-500" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Link Expired</h2>
              <p className="text-zinc-400 text-sm mb-6">
                {message || 'This verification link has expired. Please request a new verification email.'}
              </p>
              {!resendDone ? (
                <form onSubmit={handleResend} className="space-y-3">
                  <input
                    type="email"
                    placeholder="Your email address"
                    value={resendEmail}
                    onChange={e => setResendEmail(e.target.value)}
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={resending || cooldownSecs > 0}
                    data-testid="resend-btn"
                    className="w-full py-3 rounded-xl font-bold text-white text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                    style={{ background: cooldownSecs > 0 ? '#374151' : '#dc2626' }}
                  >
                    {cooldownSecs > 0 ? (
                      <><Clock size={16} />{`Resend available in ${cooldownSecs}s`}</>
                    ) : resending ? (
                      <><Loader2 size={16} className="animate-spin" />Sending…</>
                    ) : (
                      <><RefreshCw size={16} />Resend Verification Email</>
                    )}
                  </button>
                </form>
              ) : (
                <div className="rounded-xl p-4" style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.35)' }}>
                  <p className="text-green-400 text-sm">New verification email sent! Check your inbox.</p>
                </div>
              )}
            </div>
          )}

          {/* ── Resend form (no token in URL) ─────────── */}
          {status === 'resend' && (
            <div data-testid="resend-form">
              <div className="text-center mb-6">
                <Mail size={48} className="mx-auto mb-4 text-blue-400" />
                <h2 className="text-white text-xl font-heading font-bold mb-2">Resend Verification</h2>
                <p className="text-zinc-400 text-sm">Enter your email to get a new verification link.</p>
              </div>
              {!resendDone ? (
                <form onSubmit={handleResend} className="space-y-3">
                  <input
                    type="email"
                    placeholder="Your email address"
                    value={resendEmail}
                    onChange={e => setResendEmail(e.target.value)}
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={resending || cooldownSecs > 0}
                    data-testid="resend-submit-btn"
                    className="w-full py-3 rounded-xl font-bold text-white text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                    style={{ background: cooldownSecs > 0 ? '#374151' : '#dc2626' }}
                  >
                    {cooldownSecs > 0 ? (
                      <><Clock size={16} />{`Resend available in ${cooldownSecs}s`}</>
                    ) : resending ? (
                      <><Loader2 size={16} className="animate-spin" />Sending…</>
                    ) : (
                      <><Mail size={16} />Send Verification Email</>
                    )}
                  </button>
                </form>
              ) : (
                <div className="rounded-xl p-4 text-center" style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.35)' }}>
                  <CheckCircle2 size={28} className="mx-auto mb-2 text-green-400" />
                  <p className="text-green-400 text-sm">Verification email sent! Check your inbox.</p>
                  <button onClick={() => navigate('/')} className="mt-4 text-zinc-400 text-sm underline">
                    Back to Sign In
                  </button>
                </div>
              )}
            </div>
          )}

        </div>

        <p className="text-center text-zinc-600 text-xs mt-6">
          <button onClick={() => navigate('/')} className="hover:text-zinc-400 transition-colors">
            ← Back to AceIt AI
          </button>
        </p>
      </motion.div>
    </div>
  );
}
