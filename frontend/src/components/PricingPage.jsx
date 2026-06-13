import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Sparkles, Crown, Zap, ArrowRight, X, ShieldCheck, Star } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useCredits } from '../contexts/CreditsContext';
import { loadRazorpayCheckout } from '../lib/razorpay';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLAN_VISUALS = {
  free:  { gradient: 'from-slate-700 to-slate-900',         glow: '#64748b', icon: Sparkles, accent: '#94a3b8' },
  pro:   { gradient: 'from-blue-600 via-indigo-700 to-blue-900', glow: '#2563eb', icon: Zap,      accent: '#3b82f6' },
  elite: { gradient: 'from-rose-600 via-amber-600 to-yellow-500', glow: '#dc2626', icon: Crown,    accent: '#fbbf24' },
};

export default function PricingPage() {
  const nav = useNavigate();
  const { plan: myPlan, refresh } = useSubscription();
  const { refresh: refreshCredits } = useCredits();
  const [plans, setPlans] = useState([]);
  const [billing, setBilling] = useState('monthly'); // 'monthly' | 'yearly'
  const [subscribing, setSubscribing] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    axios.get(`${API}/subscription/plans`)
      .then(r => setPlans(r.data.plans))
      .catch(() => setPlans([]));
  }, []);

  const handleSubscribe = async (planId) => {
    if (planId === 'free') return;
    setSubscribing(planId);
    try {
      // 1. Ask backend for an order (or mock_mode fallback)
      const { data: order } = await axios.post(`${API}/subscription/create-order`,
        { plan: planId, billing_cycle: billing }, { withCredentials: true });

      if (order.mock_mode) {
        // No Razorpay keys configured — use the legacy mock subscribe
        const { data } = await axios.post(`${API}/subscription/subscribe`,
          { plan: planId, billing_cycle: billing }, { withCredentials: true });
        toast.success(`Subscription activated — ${data.credits_added} bonus credits added!`);
        setSuccess(data);
        refresh?.(); refreshCredits?.();
        setSubscribing(null);
        return;
      }

      // 2. Open Razorpay checkout
      const Razorpay = await loadRazorpayCheckout();
      const rzp = new Razorpay({
        key: order.key_id || process.env.REACT_APP_RAZORPAY_KEY_ID,
        amount: order.amount_paise, currency: order.currency || 'INR',
        order_id: order.order_id,
        name: 'AceIt AI', description: `${planId.toUpperCase()} • ${billing}`,
        image: '/favicon.ico',
        prefill: order.prefill || {},
        theme: { color: '#dc2626' },
        handler: async (rsp) => {
          try {
            const { data: verified } = await axios.post(`${API}/subscription/verify-payment`,
              { ...rsp, plan: planId, billing_cycle: billing },
              { withCredentials: true });
            toast.success(`Payment verified! +${verified.credits_added} bonus credits.`);
            setSuccess(verified);
            refresh?.(); refreshCredits?.();
          } catch (e) {
            toast.error('Payment verification failed. Please contact support if charged.');
          }
          setSubscribing(null);
        },
        modal: { ondismiss: () => { setSubscribing(null); toast('Payment cancelled', { icon: '✖' }); } },
      });
      rzp.on('payment.failed', (resp) => {
        toast.error(`Payment failed: ${resp.error?.description || 'Try again'}`);
        setSubscribing(null);
      });
      rzp.open();
    } catch (e) {
      console.error(e);
      toast.error(e?.response?.data?.detail || 'Could not start payment. Try again.');
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

      {/* Plan cards */}
      <div className="grid md:grid-cols-3 gap-4 sm:gap-5">
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

                <button onClick={() => handleSubscribe(p.id)}
                  disabled={isCurrent || subscribing === p.id || p.id === 'free'}
                  data-testid={`subscribe-${p.id}`}
                  className="w-full py-3 rounded-xl font-heading font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    background: p.id === 'free' ? 'rgba(255,255,255,0.08)' : v.accent,
                    color: p.id === 'free' ? '#94a3b8' : 'white',
                  }}>
                  {subscribing === p.id ? (
                    <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  ) : isCurrent ? (
                    <><ShieldCheck size={14} /> Your Current Plan</>
                  ) : p.id === 'free' ? (
                    <>Always Free</>
                  ) : (
                    <>Upgrade to {p.name} <ArrowRight size={14} /></>
                  )}
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Trust footer */}
      <div className="text-center mt-8 mb-4 text-zinc-500 text-xs font-body">
        <div className="inline-flex items-center gap-2">
          <Star size={12} className="text-amber-400" />
          Cancel anytime · 7-day money-back guarantee · Mocked payment in this demo
        </div>
      </div>

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
