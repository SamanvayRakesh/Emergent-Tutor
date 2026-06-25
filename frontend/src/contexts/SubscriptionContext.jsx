import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const SubscriptionContext = createContext(null);

export function SubscriptionProvider({ children }) {
  const { user } = useAuth();
  const [plan, setPlan] = useState(null);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgradePrompt, setUpgradePrompt] = useState(null); // {feature, message, upgrade_to}

  const refresh = useCallback(async () => {
    if (!user) { setPlan(null); setUsage(null); setLoading(false); return; }
    try {
      const { data } = await axios.get(`${API}/subscription/me`, { withCredentials: true });
      setPlan(data);
      setUsage(data.usage);
    } catch (e) { console.warn('Subscription refresh failed:', e); }
    setLoading(false);
  }, [user]);

  useEffect(() => { refresh(); }, [refresh]);

  const triggerUpgrade = useCallback((opts) => setUpgradePrompt(opts), []);
  const dismissUpgrade = useCallback(() => setUpgradePrompt(null), []);

  // Helper: check if user has a feature
  const hasFeature = (key) => !!plan?.limits?.[key];
  const isPaid = plan?.plan_id && plan.plan_id !== 'free';

  return (
    <SubscriptionContext.Provider value={{
      plan, usage, loading, refresh,
      hasFeature, isPaid,
      upgradePrompt, triggerUpgrade, dismissUpgrade,
    }}>
      {children}
    </SubscriptionContext.Provider>
  );
}

export function useSubscription() {
  return useContext(SubscriptionContext) || {};
}
