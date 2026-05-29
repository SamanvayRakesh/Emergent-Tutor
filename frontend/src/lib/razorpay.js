// Tiny helper: inject Razorpay Checkout SDK once and resolve when ready.
// No npm dep needed — Razorpay docs recommend the script tag approach.
let _loadPromise = null;

export function loadRazorpayCheckout() {
  if (typeof window === 'undefined') return Promise.reject(new Error('no window'));
  if (window.Razorpay) return Promise.resolve(window.Razorpay);
  if (_loadPromise) return _loadPromise;
  _loadPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = 'https://checkout.razorpay.com/v1/checkout.js';
    s.async = true;
    s.onload = () => resolve(window.Razorpay);
    s.onerror = () => { _loadPromise = null; reject(new Error('Razorpay SDK failed to load')); };
    document.body.appendChild(s);
  });
  return _loadPromise;
}
