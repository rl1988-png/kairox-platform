# TX Fraud Check Prompt

Analyze recharge fraud claims using on-chain data vs user claims.

Known fraud pattern (reference only): user claims 3000 USDT but on-chain transfer is 30 USDT.

Respond JSON:
- verdict: LIKELY_FRAUD | SUSPICIOUS | LIKELY_LEGIT
- reasons: string array
- recommended_action: REJECT_AND_EDUCATE | MANUAL_REVIEW | APPROVE_CREDIT
- confidence: 0-1

Always prefer on-chain amount over user screenshots.
