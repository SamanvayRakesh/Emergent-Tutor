import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, CheckCircle, Sparkles, Crown, Zap, ArrowRight, X, ShieldCheck, Star, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useCredits } from '../contexts/CreditsContext';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from './ui/alert-dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLAN_VISUALS = {
  free:    { gradient: 'from-slate-700 to-slate-900',             glow: '#64748b', icon: Sparkles, accent: '#94a3b8' },
  starter: { gradient: 'from-blue-600 via-indigo-700 to-blue-900', glow: '#2563eb', icon: Zap,      accent: '#3b82f6' },
  pro:     { gradient: 'from-violet-600 via-purple-700 to-indigo-900', glow: '#7c3aed', icon: Crown, accent: '#a78bfa' },
  elite:   { gradient: 'from-rose-600 via-amber-600 to-yellow-500', glow: '#dc2626', icon: Crown,    accent: '#fbbf24' },
};

export default function PricingPage() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const { plan: myPlan, refresh } = useSubscription();
  const { refresh: refreshCredits } = useCredits();
  const [plans, setPlans] = useState([]);
  const [billing, setBilling] = useState('monthly');
  const [subscribing, setSubscribing] = useState(null);
  const [success, setSuccess] = useState(null);
  const [cancelTarget, setCancelTarget] = useState(null);   // plan being cancelled
  const [cancelling, setCancelling] = useState(false);

  const formatDate = (iso) => iso
    ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    : '';

  const handleCancelConfirm = async () => {
    setCancelling(true);
    try {
      const { data } = await axios.post(`${API}/subscription/cancel`, {}, { withCredentials: true });
      toast.success(`Plan cancelled. You have full access until ${formatDate(data.access_until)}.`);
      refresh?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Could not cancel. Please try again.');
    } finally {
      setCancelling(false);
      setCancelTarget(null);
    }
  };

  useEffect(() => {
    axios.get(`${API}/subscription/plans`)
      .then(r => {
        const paid = (r.data.plans || []).filter(p => p.id === 'starter' || p.id === 'pro');
        setPlans(paid);
      })
      .catch(() => setPlans([]));
  }, []);

  // Handle return from PayU checkout
  useEffect(() => {
    const payment = searchParams.get('payment');
    const planId  = searchParams.get('plan');
    if (payment === 'success' && planId) {
      const planDetails = { starter: { name: 'Starter', amount: 399, credits: 500 }, pro: { name: 'Pro', amount: 699, credits: 1000 } };
      const p = planDetails[planId] || { name: planId, amount: 0, credits: 0 };
      setSuccess({ message: `You're now on ${p.name}!`, billing_cycle: 'monthly', amount_inr: p.amount, credits_added: p.credits });
      refresh?.();
      refreshCredits?.();
      // Clean up URL params
      nav('/upgrade', { replace: true });
    } else if (payment === 'failed') {
      toast.error('Payment was not completed. Please try again.');
      nav('/upgrade', { replace: true });
    }
  }, [searchParams]); // eslint-disable-line

  const handleSubscribe = async (planId) => {
    if (planId === 'free') return;
    setSubscribing(planId);
    try {
      // Get PayU form fields from backend
      const { data } = await axios.post(
        `${API}/payments/payu-initiate`,
        { plan: planId },
        { withCredentials: true },
      );

      // Build and auto-submit hidden form to PayU hosted checkout
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = data.action;
      Object.entries(data.fields).forEach(([name, value]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = String(value ?? '');
        form.appendChild(input);
      });
      document.body.appendChild(form);
      form.submit();
      // Browser navigates away — no setSubscribing(null) needed
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Could not start payment. Please try again.');
      setSubscribing(null);
    }
  };

  const priceOf = (p) => billing === 'yearly' ? p.price_yearly : p.price_monthly;
  const monthlyEquivalent = (p) => billing === 'yearly' && p.price_yearly ? Math.round(p.price_yearly / 12) : null;

  return (
    <div className="min-h-screen p-4 sm:p-6 max-w-6xl mx-auto" data-testid="pricing-page">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/15 border border-amber-400/30 mb-3">
          <Sparkles size={12} className="text-amber-400" />
          <span className="text-amber-400 text-[10px] font-body uppercase tracking-widest font-bold">Choose your plan</span>
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-black text-white mb-3">
          Become a <span style={{ color: '#fbbf24' }}>top performer</span>
        </h1>
        <p className="text-zinc-400 text-base sm:text-lg font-body max-w-xl mx-auto">
          Unlimited AI tutoring, adaptive mocks, and exam-day intensive mode — built for serious learners.
        </p>

        {/* Billing toggle */}
        <div className="inline-flex items-center gap-1 mt-6 p-1 rounded-full bg-zinc-900/60 border border-amber-400/20" data-testid="billing-toggle">
          {['monthly', 'yearly'].map(c => (
            <button key={c} onClick={() => setBilling(c)} data-testid={`billing-${c}`}
              className={`px-4 py-2 rounded-full text-sm font-body font-semibold transition-all relative ${billing === c ? 'bg-amber-500 text-black' : 'text-zinc-400 hover:text-white'}`}>
              {c === 'monthly' ? 'Monthly' : 'Yearly'}
              {c === 'yearly' && (
                <span className="absolute -top-2 -right-1 px-1.5 py-0.5 rounded-full bg-green-500 text-white text-[9px] font-bold">SAVE 20%</span>
              )}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Plan cards — 2 plans side-by-side */}
      <div className="grid md:grid-cols-2 gap-5 max-w-3xl mx-auto">
        {plans.map((p, i) => {
          const v = PLAN_VISUALS[p.id] || PLAN_VISUALS.free;
          const Icon = v.icon;
          const isCurrent = myPlan?.plan_id === p.id;
          const isPopular = p.badge === 'MOST POPULAR';
          const price = priceOf(p);
          const monthlyEq = monthlyEquivalent(p);

          return (
            <motion.div key={p.id}
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`relative rounded-3xl border-2 overflow-hidden transition-all ${isPopular ? 'md:scale-105 md:-mt-2' : ''}`}
              style={{ borderColor: v.accent + (isPopular ? 'aa' : '40'),
                boxShadow: isPopular ? `0 0 40px ${v.glow}50` : 'none' }}
              data-testid={`plan-card-${p.id}`}>

              {p.badge && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 px-4 py-1 rounded-b-2xl text-[10px] font-heading font-black uppercase tracking-widest text-white"
                  style={{ background: v.accent }}>
                  {p.badge}
                </div>
              )}

              <div className={`bg-gradient-to-br ${v.gradient} p-6 relative`}>
                <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-40" style={{ background: v.glow }} />

                <div className="relative z-10">
                  <div className="flex items-center gap-2.5 mb-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.15)', border: `1px solid ${v.accent}80` }}>
                      <Icon size={18} style={{ color: v.accent }} />
                    </div>
                    <h3 className="text-white text-2xl font-heading font-black">{p.name}</h3>
                  </div>
                  <p className="text-white/70 text-sm font-body mb-4">{p.tagline}</p>

                  <div className="flex items-baseline gap-1">
                    <span className="text-white text-4xl font-heading font-black">₹{price}</span>
                    <span className="text-white/60 text-sm font-body">/{billing === 'yearly' ? 'yr' : 'mo'}</span>
                  </div>
                  {monthlyEq && p.id !== 'free' && (
                    <p className="text-amber-300 text-xs font-body mt-1">Just ₹{monthlyEq}/mo, billed annually</p>
                  )}
                </div>
              </div>

              <div className="p-6 bg-zinc-950/40 backdrop-blur-md">
                <ul className="space-y-2 mb-5">
                  {p.highlights?.map(h => (
                    <li key={h} className="flex items-start gap-2 text-sm font-body text-zinc-200">
                      <Check size={14} className="flex-shrink-0 mt-0.5" style={{ color: v.accent }} /> {h}
                    </li>
                  ))}
                  {p.locked?.map(l => (
                    <li key={l} className="flex items-start gap-2 text-sm font-body text-zinc-600">
                      <X size={14} className="flex-shrink-0 mt-0.5" /> {l}
                    </li>
                  ))}
                </ul>

                {/* Computed state for this card */}
                {(() => {
                  const sub = myPlan?.subscription;
                  const isCancelledPlan = isCurrent && sub?.cancel_at_period_end;
                  const accessUntil = isCurrent ? sub?.expires_at : null;
                  return (
                    <>
                      {/* Access-until badge for cancelled plans */}
                      {isCancelledPlan && accessUntil && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 mb-3">
                          <AlertTriangle size={12} className="text-amber-400 shrink-0" />
                          <span className="text-amber-300 text-xs font-body">
                            Access ends {formatDate(accessUntil)}
                          </span>
                        </div>
                      )}

                      {/* Renews-on badge for active paid plans */}
                      {isCurrent && !isCancelledPlan && p.id !== 'free' && accessUntil && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 mb-3" data-testid="renews-on-badge">
                          <CheckCircle size={12} className="text-green-400 shrink-0" />
                          <span className="text-green-300 text-xs font-body">
                            Renews {formatDate(accessUntil)} · Payment via PayU
                          </span>
                        </div>
                      )}

                      <button onClick={() => !isCurrent && handleSubscribe(p.id)}
                        disabled={isCurrent || subscribing === p.id || p.id === 'free'}
                        data-testid={`subscribe-${p.id}`}
                        className="w-full py-3 rounded-xl font-heading font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        style={{
                          background: p.id === 'free' ? 'rgba(255,255,255,0.08)' : v.accent,
                          color: p.id === 'free' ? '#94a3b8' : 'white',
                        }}>
                        {subscribing === p.id ? (
                          <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                        ) : isCancelledPlan ? (
                          <><ShieldCheck size={14} /> Active until {formatDate(accessUntil)}</>
                        ) : isCurrent ? (
                          <><ShieldCheck size={14} /> Your Current Plan</>
                        ) : p.id === 'free' ? (
                          <>Always Free</>
                        ) : (
                          <>Upgrade to {p.name} <ArrowRight size={14} /></>
                        )}
                      </button>

                      {/* Cancel link — only for active (non-cancelled) paid plan */}
                      {isCurrent && !isCancelledPlan && p.id !== 'free' && (
                        <button
                          data-testid={`cancel-plan-${p.id}`}
                          onClick={() => setCancelTarget({ planId: p.id, planName: p.name, accessUntil })}
                          className="w-full mt-2 text-xs text-zinc-500 hover:text-red-400 font-body transition-colors py-1">
                          Cancel subscription
                        </button>
                      )}
                    </>
                  );
                })()}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Trust footer */}
      <div className="text-center mt-8 mb-4 text-zinc-500 text-xs font-body">
        <div className="inline-flex items-center gap-2">
          <Star size={12} className="text-amber-400" />
          Cancel anytime · Access continues until billing period ends · Secured by PayU
        </div>
      </div>

      {/* Cancel confirmation dialog */}
      <AlertDialog open={!!cancelTarget} onOpenChange={(o) => !o && setCancelTarget(null)}>
        <AlertDialogContent className="bg-zinc-900 border border-zinc-800 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white font-heading">
              Cancel {cancelTarget?.planName} plan?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-400 font-body">
              {cancelTarget?.accessUntil
                ? <>You&apos;ll keep <strong className="text-white">full access</strong> to all {cancelTarget.planName} features until <strong className="text-white">{formatDate(cancelTarget.accessUntil)}</strong>. After that your account reverts to Free.</>
                : <>Your subscription will be cancelled at the end of your current billing period.</>
              }
              <br /><br />
              No further charges will be made after your current period ends.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              data-testid="cancel-dialog-keep"
              className="bg-zinc-800 text-white border-zinc-700 hover:bg-zinc-700 font-body">
              Keep my plan
            </AlertDialogCancel>
            <AlertDialogAction
              data-testid="cancel-dialog-confirm"
              disabled={cancelling}
              onClick={handleCancelConfirm}
              className="bg-red-600 hover:bg-red-700 text-white font-body">
              {cancelling ? 'Cancelling…' : 'Yes, cancel'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Success overlay */}
      <AnimatePresence>
        {success && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
            data-testid="upgrade-success">
            <motion.div initial={{ scale: 0.7 }} animate={{ scale: 1 }}
              className="bg-gradient-to-br from-amber-500 via-rose-500 to-violet-600 p-1 rounded-3xl max-w-sm w-full">
              <div className="rounded-[20px] p-6 bg-zinc-950 text-center">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1, rotate: [0, -10, 10, 0] }}
                  className="w-16 h-16 mx-auto mb-3 rounded-full flex items-center justify-center bg-gradient-to-br from-amber-400 to-rose-500">
                  <Crown size={32} className="text-white" />
                </motion.div>
                <h3 className="text-white text-2xl font-heading font-black mb-1">{success.message}</h3>
                <p className="text-zinc-400 text-sm font-body mb-4">
                  ₹{success.amount_inr} • {success.billing_cycle === 'yearly' ? '1 year' : '1 month'} of premium learning
                </p>
                <button onClick={() => { setSuccess(null); nav('/'); }} data-testid="upgrade-success-cta"
                  className="px-5 py-2.5 rounded-xl bg-amber-500 text-black font-heading font-bold text-sm">
                  Start Learning →
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
