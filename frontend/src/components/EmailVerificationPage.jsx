import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, Mail, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function EmailVerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState('verifying'); // verifying | success | error | expired | resend
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendDone, setResendDone] = useState(false);

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setStatus('resend');
    }
  }, [token]);

  async function verifyToken() {
    try {
      const { data } = await axios.get(`${API}/api/auth/verify-email`, { params: { token } });
      setStatus('success');
      setMessage(data.message);
      setEmail(data.email || '');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'TOKEN_EXPIRED') {
        setStatus('expired');
        setResendEmail(detail.email || '');
        setMessage(detail.message || 'Link expired.');
      } else {
        setStatus('error');
        setMessage(detail?.message || detail || 'Invalid or already used verification link.');
      }
    }
  }

  async function handleResend(e) {
    e.preventDefault();
    setResending(true);
    try {
      await axios.post(`${API}/api/auth/resend-verification`, { email: resendEmail });
      setResendDone(true);
    } catch {
      setResendDone(true); // show success anyway to avoid enumeration
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-heading font-black text-3xl text-white">
            AceIt<span style={{ color: '#dc2626' }}> AI</span>
          </h1>
        </div>

        <div className="glass-card rounded-2xl p-8 border border-white/10">
          {/* Verifying */}
          {status === 'verifying' && (
            <div className="text-center py-4" data-testid="verifying-state">
              <Loader2 size={48} className="mx-auto mb-4 text-blue-400 animate-spin" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Verifying your email…</h2>
              <p className="text-zinc-400 text-sm">Just a moment</p>
            </div>
          )}

          {/* Success */}
          {status === 'success' && (
            <div className="text-center py-4" data-testid="verification-success">
              <CheckCircle2 size={52} className="mx-auto mb-4" style={{ color: '#22c55e' }} />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Email Verified!</h2>
              <p className="text-zinc-300 text-sm mb-6">{message || 'Your account is now active.'}</p>
              {email && <p className="text-zinc-500 text-xs mb-6">{email}</p>}
              <button
                data-testid="go-to-login-btn"
                onClick={() => navigate('/')}
                className="w-full py-3 rounded-xl font-heading font-bold text-white text-sm"
                style={{ background: '#dc2626' }}
              >
                Sign In Now
              </button>
            </div>
          )}

          {/* Error */}
          {status === 'error' && (
            <div className="text-center py-4" data-testid="verification-error">
              <XCircle size={52} className="mx-auto mb-4 text-red-500" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Link Invalid</h2>
              <p className="text-zinc-400 text-sm mb-6">{message}</p>
              <button
                onClick={() => setStatus('resend')}
                className="w-full py-3 rounded-xl font-heading font-bold text-white text-sm border border-white/20"
              >
                Request New Link
              </button>
            </div>
          )}

          {/* Expired */}
          {status === 'expired' && (
            <div className="text-center py-4" data-testid="verification-expired">
              <XCircle size={52} className="mx-auto mb-4 text-yellow-500" />
              <h2 className="text-white text-xl font-heading font-bold mb-2">Link Expired</h2>
              <p className="text-zinc-400 text-sm mb-6">{message}</p>
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
                    disabled={resending}
                    data-testid="resend-btn"
                    className="w-full py-3 rounded-xl font-bold text-white text-sm flex items-center justify-center gap-2"
                    style={{ background: '#dc2626' }}
                  >
                    {resending ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                    {resending ? 'Sending…' : 'Resend Verification Email'}
                  </button>
                </form>
              ) : (
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                  <p className="text-green-400 text-sm">New verification email sent! Check your inbox.</p>
                </div>
              )}
            </div>
          )}

          {/* Resend form */}
          {status === 'resend' && (
            <div data-testid="resend-form">
              <Mail size={48} className="mx-auto mb-4 text-blue-400 block" />
              <h2 className="text-white text-xl font-heading font-bold mb-2 text-center">Resend Verification</h2>
              <p className="text-zinc-400 text-sm mb-6 text-center">
                Enter your email to get a new verification link.
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
                    disabled={resending}
                    data-testid="resend-submit-btn"
                    className="w-full py-3 rounded-xl font-bold text-white text-sm flex items-center justify-center gap-2"
                    style={{ background: '#dc2626' }}
                  >
                    {resending ? <Loader2 size={16} className="animate-spin" /> : <Mail size={16} />}
                    {resending ? 'Sending…' : 'Send Verification Email'}
                  </button>
                </form>
              ) : (
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
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
