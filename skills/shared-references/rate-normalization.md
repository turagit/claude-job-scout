# Rate / Salary Normalization

Normalize all compensation to **daily rate** for consistent comparison.

## Conversion Table

| Source | Formula | Example |
|--------|---------|---------|
| Daily rate | As-is | £550/day |
| Hourly | x8 | £70/hr = £560/day |
| Weekly | /5 | £2,750/wk = £550/day |
| Monthly | /20 | £11,000/mo = £550/day |
| Annual | /220 | £121,000/yr = £550/day |

**Assumptions (UK-standard):** 220 days/year, 20/month, 5/week, 8 hrs/day. Adjust for other markets.

## Currency

- Always note currency, never convert between currencies
- Use user's preference from `user-profile.json` → `requirements.rate_currency`
- Flag if currency not specified

## Permanent vs Freelance

Freelance rates should be ~30-50% above permanent equivalent (no holidays, pension, benefits, gaps). Flag in reports: "Permanent equivalent: ~£550/day — Freelance parity: £715+/day"

## Display

Always show: original stated compensation, normalized daily rate, any warnings (missing rate, IR35 unclear).
