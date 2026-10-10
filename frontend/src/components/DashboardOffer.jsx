import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import axios from 'axios';
import { useSubscription } from '../contexts/SubscriptionContext';
import { getMonthlyOffer } from '../lib/pricingOffers';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const currency = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(value);

export default function DashboardOffer() {
  const { plan, loading } = useSubscription();
  const nav = useNavigate();
  const [starter, setStarter] = useState(null);
  const eligible = !loading && plan?.plan_id === 'free';

  useEffect(() => {
    if (!eligible) return;
    const controller = new AbortController();
    let active = true;
    axios.get(`${API}/subscription/plans`, { signal: controller.signal })
      .then(({ data }) => {
        if (active) setStarter((data.plans || []).find(p => p.id === 'starter') || null);
      })
      .catch(() => { if (active) setStarter(null); });
    return () => { active = false; controller.abort(); };
  }, [eligible]);

  const offer = eligible ? getMonthlyOffer(starter) : null;
  if (!offer) return null;

  return (
    <section className="ace-dashboard-offer" aria-labelledby="dashboard-offer-title" data-testid="dashboard-offer">
      <div className="ace-offer-icon" aria-hidden="true"><Sparkles size={20} /></div>
      <div className="ace-offer-copy">
        <span className="ace-offer-eyebrow">STARTER MONTHLY OFFER</span>
        <h2 id="dashboard-offer-title">More learning, for less.</h2>
        <p>{starter.tagline || 'Explore what’s included in the Starter plan.'}</p>
      </div>
      <div className="ace-offer-price">
        <div><strong>{currency(offer.price)}</strong><span> /month</span></div>
        <p><del>{currency(offer.originalPrice)}</del> <span>Save {currency(offer.savings)}/month</span></p>
      </div>
      <button type="button" data-ace-primary="true" data-testid="dashboard-offer-cta"
        className="ace-offer-cta" onClick={() => nav('/upgrade')}>
        Explore Starter <ArrowRight size={16} aria-hidden="true" />
      </button>
    </section>
  );
}
