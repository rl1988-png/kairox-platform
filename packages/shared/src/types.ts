/** Unified API error shape — mirrored by FastAPI error handlers and frontend client. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export type UserRole = 'user' | 'admin' | 'support';

export interface UserPublic {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  teamId: string | null;
  createdAt: string;
  inviteCode?: string | null;
  vipLevel?: number;
  isOfficial?: boolean;
  trialExpiresAt?: string | null;
}

export interface AuthTokens {
  accessToken: string;
  expiresIn: number;
}

export interface LoginRequest {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  inviteCode: string;
}

export interface WalletBalance {
  available: string;
  locked: string;
  currency: 'USDT';
}

export interface WalletSummary {
  userId: string;
  balance: WalletBalance;
  depositAddress: string | null;
}

export type LedgerEntryType =
  | 'recharge'
  | 'withdraw'
  | 'trade_lock'
  | 'trade_unlock'
  | 'trade_profit'
  | 'trade_loss'
  | 'admin_adjustment';

export interface LedgerEntry {
  id: string;
  type: LedgerEntryType;
  amount: string;
  balanceAfter: string;
  referenceId: string | null;
  createdAt: string;
}

export type TradeState =
  | 'idle'
  | 'pre_started'
  | 'pending_funds'
  | 'ready'
  | 'running'
  | 'settling'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface TradeLevel {
  level: number;
  name: string;
  tradeAmount: string;
  minBalance: string;
  profitRate: string;
  durationSeconds: number;
  available: boolean;
}

export interface TradeSession {
  id: string;
  userId: string;
  state: TradeState;
  vipLevel: number | null;
  amount: string;
  profit: string | null;
  expiresAt: string | null;
  durationSeconds: number | null;
  startedAt: string | null;
  completedAt: string | null;
}

export type RechargeStatus =
  | 'pending'
  | 'confirming'
  | 'confirmed'
  | 'paid'
  | 'expired'
  | 'failed';

export interface CreateRechargeOrderRequest {
  amount: string;
  network: 'TRC20';
}

export interface RechargeOrder {
  id: string;
  expectedAmount: string;
  amount: string;
  depositAddress: string;
  network: 'TRC20';
  status: RechargeStatus;
  txHash: string | null;
  confirmations: number;
  expiresAt: string;
  createdAt: string;
}

export interface RechargeOrderStatus {
  id: string;
  status: RechargeStatus;
  txHash: string | null;
  confirmations: number;
  expiresAt: string;
  paidAt: string | null;
}

/** @deprecated Legacy tx-hash submit flow */
export interface RechargeRequest {
  txHash: string;
}

/** @deprecated Legacy record shape */
export interface RechargeRecord {
  id: string;
  txHash: string;
  amount: string;
  status: RechargeStatus;
  confirmations: number;
  createdAt: string;
}

export type WithdrawStatus = 'pending' | 'approved' | 'processing' | 'completed' | 'rejected';

export interface WithdrawRequest {
  amount: string;
  toAddress: string;
}

export interface WithdrawRecord {
  id: string;
  amount: string;
  toAddress: string;
  status: WithdrawStatus;
  createdAt: string;
}

export interface TeamMember {
  id: string;
  username: string;
  joinedAt: string;
}

export interface TeamSummary {
  id: string;
  name: string;
  memberCount: number;
  inviteCode: string;
}

export interface SupportTxVerifyRequest {
  txHash: string;
  userId?: string;
}

export interface SupportTxVerifyResult {
  txHash: string;
  found: boolean;
  amount: string | null;
  confirmations: number;
  credited: boolean;
}
