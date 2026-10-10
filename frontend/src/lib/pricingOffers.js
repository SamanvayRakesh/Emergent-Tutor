// Keep dashboard promotions aligned with the existing pricing comparison.
export const MONTHLY_ORIGINAL_PRICES = { starter: 499, pro: 999 };

export function getMonthlyOffer(plan) {
  const price = plan?.price_monthly;
  const originalPrice = MONTHLY_ORIGINAL_PRICES[plan?.id];
  if (typeof price !== 'number' || !Number.isFinite(price) || price <= 0 || !(originalPrice > price)) return null;
  return { price, originalPrice, savings: originalPrice - price };
}
