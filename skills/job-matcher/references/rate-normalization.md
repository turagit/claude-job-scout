# Rate / Salary Normalization

When job listings display compensation in different formats, normalize to a **daily rate** for consistent comparison. This allows apples-to-apples comparison across freelance, contract, and even permanent roles.

## Conversion Table

| Source Format | Normalization Formula | Example |
|---------------|----------------------|---------|
| Daily rate | Use as-is | £550/day → £550/day |
| Hourly rate | hourly × 8 | £70/hr → £560/day |
| Weekly rate | weekly ÷ 5 | £2,750/week → £550/day |
| Monthly rate | monthly ÷ 20 | £11,000/month → £550/day |
| Annual salary | annual ÷ 220 | £121,000/year → £550/day |

## Working Days Assumptions

- **220 working days/year** (52 weeks × 5 days - 30 days holidays/bank holidays - 10 days unbillable)
- **20 working days/month**
- **5 working days/week**
- **8 hours/working day**

These are UK-standard assumptions. Adjust for other markets if the user specifies a different country.

## Currency Handling

- Always note the currency when displaying rates
- Do NOT convert between currencies — just normalize the time period
- If a listing shows multiple currencies, use the one matching the user's profile preference (from `user-profile.json` → `requirements.rate_currency`)
- If no currency is specified in the listing, flag: "⚠ Currency not specified"

## Permanent vs Freelance Rate Comparison

When a permanent salary is shown but the user is looking for freelance work, the normalized daily rate provides a rough equivalence. However, note these differences:

- **Freelance rates should be ~30-50% higher** than permanent equivalents to account for: no paid holidays, no pension, no benefits, self-employment costs, gaps between contracts
- A permanent role at £121k/year (£550/day equivalent) would need to be a £715-£825/day freelance rate to be equivalent in total compensation
- Flag this in the report: "Permanent equivalent: ~£550/day — Freelance should be £715+/day for parity"

## Display Format

In reports and conversation output, always show:

1. The **original stated compensation** (as the listing shows it)
2. The **normalized daily rate** (for comparison)
3. Any **warnings** about missing or unclear compensation

Example:

```
💰 £550/day (stated) | ⚠ IR35 status unclear
💰 £121,000/year (= ~£550/day) | Permanent role
💰 ⚠ Does not mention rate
```
