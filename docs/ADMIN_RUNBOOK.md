# Admin Runbook — Phase 6

Operational guide for support and admin staff on Kairox Platform v2.

## Roles

| Role | Access |
|------|--------|
| `user` | Standard app only — no `/admin` |
| `support` | Read-only admin + TX verify — **no** manual credit or withdraw approve/confirm/fail/reject |
| `admin` | Full admin including ledger credits and withdraw decisions |

## TX Verify workflow (anti-screenshot)

1. User creates recharge order in app (min **30 USDT**).
2. User pays on-chain to the displayed deposit address.
3. Support opens **Admin → Recharge** and enters the **TX hash** (never a screenshot).
4. Read the **verdict badge**:
   - `CREDIT_OK` — amount and address match a pending order; watcher should credit automatically, or escalate if stuck.
   - `AMOUNT_MISMATCH` — on-chain amount does not match any pending order.
   - `WRONG_ADDRESS` — payment sent to wrong address.
   - `NOT_FOUND` — TX not found on TronGrid (wait for confirmations or invalid hash).
   - `ALREADY_USED` — TX already credited; reject duplicate claims.

## Manual credit (admin only)

1. **Admin → Users** → open user detail.
2. Enter amount, reason (min 10 chars), confirm dialog.
3. Every credit creates **ledger CREDIT + audit log** in one DB transaction.
4. Re-submitting with the same `idempotency_key` is safe (no double credit).

## Withdraw approve / reject (admin only)

User flow:

1. User binds TRC20 address once (`POST /wallet/bind-address`).
2. User submits amount (`POST /withdraw/requests`) — funds **locked** (amount + 1 USDT fee).
3. Admin reviews **Admin → Withdraw**.

**Approve:** enter the TRC20 payout `tx_hash`; status becomes `processing` and funds
stay locked. This records broadcast evidence but does not debit the ledger yet.

**Confirm:** after on-chain confirmations reach `TRON_MIN_CONFIRMATIONS`, confirm the
withdrawal. The system unlocks then debits the locked funds and marks the request
`completed`.

**Fail:** if the broadcast fails or the TX cannot settle, mark the processing request
failed. The system unlocks the funds and keeps the TX hash/audit trail.

**Reject:** unlock funds back to available, status `rejected`, add note for user/support.

## Typical support scenarios

| Scenario | Action |
|----------|--------|
| “I paid but balance unchanged” | TX Verify → if `CREDIT_OK`, check order expiry; if `ALREADY_USED`, explain replay |
| “Wrong amount sent” | Verdict `AMOUNT_MISMATCH` — do not manual credit without admin approval |
| “Withdraw stuck pending” | Admin checks queue; approve after on-chain send or reject with reason |
| Trial user withdraw blocked | Expected when `BLOCK_TRIAL_WITHDRAW=true`; user must become official |

## Audit

All admin mutations log to **Admin → Audit** with actor, IP, user-agent, and payload JSON.
