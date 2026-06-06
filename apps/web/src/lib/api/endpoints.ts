import type {
  CreateRechargeOrderRequest,
  LoginRequest,
  RechargeOrder,
  RechargeOrderStatus,
  RegisterRequest,
  TradeLevel,
  TradeSession,
  UserPublic,
  WalletSummary,
} from '@kairox/shared';
import { apiRequest, applyAuthResponse, clearAuthState } from './client';

interface AuthResponse {
  user: {
    id: string;
    username: string;
    email: string;
    role: UserPublic['role'];
    team_id: string | null;
    created_at: string;
    invite_code?: string | null;
    vip_level?: number;
    is_official?: boolean;
    trial_expires_at?: string | null;
  };
  access_token: string;
  expires_in: number;
  csrf_token: string;
}

interface MessageResponse {
  message: string;
}

function mapUser(data: AuthResponse['user']): UserPublic {
  return {
    id: data.id,
    username: data.username,
    email: data.email,
    role: data.role as UserPublic['role'],
    teamId: data.team_id ?? null,
    createdAt: data.created_at,
    inviteCode: data.invite_code ?? null,
    vipLevel: data.vip_level ?? 1,
    isOfficial: data.is_official ?? false,
    trialExpiresAt: data.trial_expires_at ?? null,
  };
}

function handleAuthResponse(res: AuthResponse) {
  applyAuthResponse(res);
  return {
    user: mapUser(res.user),
    tokens: { accessToken: res.access_token, expiresIn: res.expires_in },
    csrf: res.csrf_token,
  };
}

export const authApi = {
  login: async (data: LoginRequest & { rememberMe?: boolean }) => {
    const res = await apiRequest<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: {
        username: data.username,
        password: data.password,
        remember_me: data.rememberMe ?? false,
      },
      auth: false,
    });
    return handleAuthResponse(res);
  },

  register: async (data: RegisterRequest) => {
    const res = await apiRequest<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: {
        username: data.username,
        email: data.email,
        password: data.password,
        invite_code: data.inviteCode,
      },
      auth: false,
    });
    return handleAuthResponse(res);
  },

  me: async () => {
    const res = await apiRequest<AuthResponse>('/api/v1/auth/me', { auth: false });
    return handleAuthResponse(res);
  },

  logout: async () => {
    await apiRequest<MessageResponse>('/api/v1/auth/logout', {
      method: 'POST',
      csrf: true,
      auth: false,
    });
    clearAuthState();
  },

  requestPasswordReset: (email: string) =>
    apiRequest<MessageResponse>('/api/v1/auth/reset-password/request', {
      method: 'POST',
      body: { email },
      auth: false,
    }),

  confirmPasswordReset: (token: string, password: string) =>
    apiRequest<MessageResponse>('/api/v1/auth/reset-password/confirm', {
      method: 'POST',
      body: { token, password },
      auth: false,
    }),
};

interface RechargeOrderResponse {
  id: string;
  expected_amount: string;
  amount: string;
  deposit_address: string;
  network: string;
  status: RechargeOrder['status'];
  tx_hash: string | null;
  confirmations: number;
  expires_at: string;
  created_at: string;
}

interface RechargeStatusResponse {
  id: string;
  status: RechargeOrderStatus['status'];
  tx_hash: string | null;
  confirmations: number;
  expires_at: string;
  paid_at: string | null;
}

function mapRechargeOrder(data: RechargeOrderResponse): RechargeOrder {
  return {
    id: data.id,
    expectedAmount: data.expected_amount,
    amount: data.amount,
    depositAddress: data.deposit_address,
    network: 'TRC20',
    status: data.status,
    txHash: data.tx_hash,
    confirmations: data.confirmations,
    expiresAt: data.expires_at,
    createdAt: data.created_at,
  };
}

function mapRechargeStatus(data: RechargeStatusResponse): RechargeOrderStatus {
  return {
    id: data.id,
    status: data.status,
    txHash: data.tx_hash,
    confirmations: data.confirmations,
    expiresAt: data.expires_at,
    paidAt: data.paid_at,
  };
}

export const rechargeApi = {
  createOrder: async (data: CreateRechargeOrderRequest) => {
    const res = await apiRequest<RechargeOrderResponse>('/api/v1/recharge/orders', {
      method: 'POST',
      body: { amount: data.amount, network: data.network },
      csrf: true,
    });
    return mapRechargeOrder(res);
  },

  getOrder: async (orderId: string) => {
    const res = await apiRequest<RechargeOrderResponse>(`/api/v1/recharge/orders/${orderId}`);
    return mapRechargeOrder(res);
  },

  getOrderStatus: async (orderId: string) => {
    const res = await apiRequest<RechargeStatusResponse>(
      `/api/v1/recharge/orders/${orderId}/status`,
    );
    return mapRechargeStatus(res);
  },
};

interface DepositInfoResponse {
  address: string | null;
  network: string;
  currency: string;
}

export const walletApi = {
  summary: () => apiRequest<WalletSummary>('/api/v1/wallet'),
  get: () =>
    apiRequest<{
      user_id: string;
      balance: WalletSummary['balance'];
      deposit_address: string | null;
    }>('/api/v1/wallet'),
  ledger: () =>
    apiRequest<
      Array<{
        entry_type: string;
        amount: string;
        balance_after: string;
        created_at: string;
      }>
    >('/api/v1/wallet/ledger'),
  depositInfo: () => apiRequest<DepositInfoResponse>('/api/v1/wallet/deposit-info'),
};

interface TradeSessionResponse {
  id: string;
  user_id: string;
  state: TradeSession['state'];
  vip_level: number | null;
  amount: string;
  profit: string | null;
  expires_at: string | null;
  duration_seconds: number | null;
  started_at: string | null;
  completed_at: string | null;
}

interface TradeLevelResponse {
  level: number;
  name: string;
  trade_amount: string;
  min_balance: string;
  profit_rate: string;
  duration_seconds: number;
  available: boolean;
}

function mapTradeSession(data: TradeSessionResponse): TradeSession {
  return {
    id: data.id,
    userId: data.user_id,
    state: data.state,
    vipLevel: data.vip_level,
    amount: data.amount,
    profit: data.profit,
    expiresAt: data.expires_at,
    durationSeconds: data.duration_seconds,
    startedAt: data.started_at,
    completedAt: data.completed_at,
  };
}

function mapTradeLevel(data: TradeLevelResponse): TradeLevel {
  return {
    level: data.level,
    name: data.name,
    tradeAmount: data.trade_amount,
    minBalance: data.min_balance,
    profitRate: data.profit_rate,
    durationSeconds: data.duration_seconds,
    available: data.available,
  };
}

export const tradeApi = {
  levels: async () => {
    const res = await apiRequest<TradeLevelResponse[]>('/api/v1/trade/levels');
    return res.map(mapTradeLevel);
  },

  active: async () => {
    const res = await apiRequest<TradeSessionResponse | null>('/api/v1/trade/active');
    return res ? mapTradeSession(res) : null;
  },

  preStart: async (vipLevel: number) => {
    const res = await apiRequest<TradeSessionResponse>('/api/v1/trade/pre-start', {
      method: 'POST',
      body: { vip_level: vipLevel },
      csrf: true,
    });
    return mapTradeSession(res);
  },

  start: async (tradeId: string) => {
    const res = await apiRequest<TradeSessionResponse>('/api/v1/trade/start', {
      method: 'POST',
      body: { trade_id: tradeId },
      csrf: true,
    });
    return mapTradeSession(res);
  },

  complete: async (tradeId: string) => {
    const res = await apiRequest<TradeSessionResponse>('/api/v1/trade/complete', {
      method: 'POST',
      body: { trade_id: tradeId },
      csrf: true,
    });
    return mapTradeSession(res);
  },
};

interface WithdrawHistoryResponse {
  id: string;
  amount: string;
  to_address: string;
  status: string;
  created_at: string;
}

export const withdrawApi = {
  bindAddress: (network: string, address: string) =>
    apiRequest<{ network: string; address: string }>('/api/v1/wallet/bind-address', {
      method: 'POST',
      body: { network, address },
      csrf: true,
    }),

  request: (amount: string) =>
    apiRequest<WithdrawHistoryResponse>('/api/v1/withdraw/requests', {
      method: 'POST',
      body: { amount },
      csrf: true,
    }),

  history: () => apiRequest<WithdrawHistoryResponse[]>('/api/v1/withdraw/history'),
};

interface AdminDashboardResponse {
  users_total: number;
  users_active_today: number;
  recharge_pending: number;
  recharge_paid_today: string;
  withdraw_pending: number;
  withdraw_pending_amount: string;
  trades_today: number;
  hot_wallet_balance: string;
}

export interface AdminDashboard {
  usersTotal: number;
  usersActiveToday: number;
  rechargePending: number;
  rechargePaidToday: string;
  withdrawPending: number;
  withdrawPendingAmount: string;
  tradesToday: number;
  hotWalletBalance: string;
}

interface AdminUserResponse {
  id: string;
  username: string;
  email: string;
  role: string;
  vip_level: number;
  is_official: boolean;
  is_active: boolean;
  withdrawal_address: string | null;
  created_at: string;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  role: string;
  vipLevel: number;
  isOfficial: boolean;
  isActive: boolean;
  withdrawalAddress: string | null;
  createdAt: string;
}

interface AdminWithdrawResponse {
  id: string;
  user_id: string;
  amount: string;
  fee_amount: string;
  to_address: string;
  status: string;
  admin_note: string | null;
  tx_hash: string | null;
  confirmations: number;
  broadcasted_at: string | null;
  confirmed_at: string | null;
  failed_at: string | null;
  created_at: string;
}

export interface AdminWithdrawRequest {
  id: string;
  userId: string;
  amount: string;
  feeAmount: string;
  toAddress: string;
  status: string;
  adminNote: string | null;
  txHash: string | null;
  confirmations: number;
  broadcastedAt: string | null;
  confirmedAt: string | null;
  failedAt: string | null;
  createdAt: string;
}

export interface AdminTrade {
  id: string;
  userId: string;
  state: string;
  vipLevel: number | null;
  amount: string;
  profit: string | null;
  createdAt: string;
}

export interface AuditLogEntry {
  id: string;
  actorId: string;
  action: string;
  targetType: string;
  targetId: string | null;
  ipAddress: string | null;
  userAgent: string | null;
  payloadJson: Record<string, unknown> | null;
  createdAt: string;
}

function mapAdminUser(data: AdminUserResponse): AdminUser {
  return {
    id: data.id,
    username: data.username,
    email: data.email,
    role: data.role,
    vipLevel: data.vip_level,
    isOfficial: data.is_official,
    isActive: data.is_active,
    withdrawalAddress: data.withdrawal_address,
    createdAt: data.created_at,
  };
}

function mapAdminWithdraw(data: AdminWithdrawResponse): AdminWithdrawRequest {
  return {
    id: data.id,
    userId: data.user_id,
    amount: data.amount,
    feeAmount: data.fee_amount,
    toAddress: data.to_address,
    status: data.status,
    adminNote: data.admin_note,
    txHash: data.tx_hash,
    confirmations: data.confirmations,
    broadcastedAt: data.broadcasted_at,
    confirmedAt: data.confirmed_at,
    failedAt: data.failed_at,
    createdAt: data.created_at,
  };
}

export const adminApi = {
  dashboard: async () => {
    const res = await apiRequest<AdminDashboardResponse>('/api/v1/admin/dashboard');
    return {
      usersTotal: res.users_total,
      usersActiveToday: res.users_active_today,
      rechargePending: res.recharge_pending,
      rechargePaidToday: res.recharge_paid_today,
      withdrawPending: res.withdraw_pending,
      withdrawPendingAmount: res.withdraw_pending_amount,
      tradesToday: res.trades_today,
      hotWalletBalance: res.hot_wallet_balance,
    } satisfies AdminDashboard;
  },

  users: async (search = '', page = 1, limit = 20) => {
    const qs = new URLSearchParams({ search, page: String(page), limit: String(limit) });
    const res = await apiRequest<{ items: AdminUserResponse[]; total: number }>(
      `/api/v1/admin/users?${qs}`,
    );
    return { items: res.items.map(mapAdminUser), total: res.total };
  },

  manualCredit: (
    userId: string,
    payload: { amount: string; reason: string; idempotencyKey: string },
  ) =>
    apiRequest('/api/v1/admin/users/' + userId + '/manual-credit', {
      method: 'POST',
      body: {
        amount: payload.amount,
        reason: payload.reason,
        idempotency_key: payload.idempotencyKey,
      },
      csrf: true,
    }),

  verifyTx: (txHash: string) =>
    apiRequest<{
      tx_hash: string;
      found: boolean;
      amount_on_chain: string | null;
      to_address: string | null;
      confirmed: boolean;
      matches_order: boolean;
      matched_order_id: string | null;
      verdict: string;
    }>(`/api/v1/admin/recharge/verify?tx_hash=${encodeURIComponent(txHash)}`),

  withdrawRequests: async (status = 'pending') => {
    const res = await apiRequest<AdminWithdrawResponse[]>(
      `/api/v1/admin/withdraw/requests?status=${status}`,
    );
    return res.map(mapAdminWithdraw);
  },

  approveWithdraw: (id: string, opts: { adminNote?: string; txHash: string }) =>
    apiRequest(`/api/v1/admin/withdraw/requests/${id}/approve`, {
      method: 'POST',
      body: { admin_note: opts.adminNote, tx_hash: opts.txHash },
      csrf: true,
    }),

  confirmWithdraw: (id: string, opts: { adminNote?: string; confirmations: number }) =>
    apiRequest(`/api/v1/admin/withdraw/requests/${id}/confirm`, {
      method: 'POST',
      body: { admin_note: opts.adminNote, confirmations: opts.confirmations },
      csrf: true,
    }),

  failWithdraw: (id: string, opts: { adminNote?: string }) =>
    apiRequest(`/api/v1/admin/withdraw/requests/${id}/fail`, {
      method: 'POST',
      body: { admin_note: opts.adminNote },
      csrf: true,
    }),

  rejectWithdraw: (id: string, opts: { adminNote?: string }) =>
    apiRequest(`/api/v1/admin/withdraw/requests/${id}/reject`, {
      method: 'POST',
      body: { admin_note: opts.adminNote },
      csrf: true,
    }),

  trades: async () => {
    const res = await apiRequest<
      {
        id: string;
        user_id: string;
        state: string;
        vip_level: number | null;
        amount: string;
        profit: string | null;
        created_at: string;
      }[]
    >('/api/v1/admin/trades');
    return res.map(
      (t): AdminTrade => ({
        id: t.id,
        userId: t.user_id,
        state: t.state,
        vipLevel: t.vip_level,
        amount: t.amount,
        profit: t.profit,
        createdAt: t.created_at,
      }),
    );
  },

  audit: async (page = 1) => {
    const res = await apiRequest<{
      items: {
        id: string;
        actor_id: string;
        action: string;
        target_type: string;
        target_id: string | null;
        ip_address: string | null;
        user_agent: string | null;
        payload_json: Record<string, unknown> | null;
        created_at: string;
      }[];
      total: number;
    }>(`/api/v1/admin/audit?page=${page}`);
    return {
      total: res.total,
      items: res.items.map(
        (e): AuditLogEntry => ({
          id: e.id,
          actorId: e.actor_id,
          action: e.action,
          targetType: e.target_type,
          targetId: e.target_id,
          ipAddress: e.ip_address,
          userAgent: e.user_agent,
          payloadJson: e.payload_json,
          createdAt: e.created_at,
        }),
      ),
    };
  },

  analyze: async (useCase: string, payload: Record<string, unknown>) => {
    const res = await apiRequest<{
      use_case: string;
      data: Record<string, unknown>;
      provider: string;
      model: string;
      confidence: number;
    }>('/api/v1/admin/ai/analyze', {
      method: 'POST',
      body: {
        use_case: useCase,
        payload,
        provider_preference: 'auto',
      },
      csrf: true,
    });
    return {
      data: res.data,
      provider: res.provider,
      model: res.model,
      confidence: res.confidence,
    };
  },

  aiHealth: () =>
    apiRequest<{ openai: boolean; anthropic: boolean; fallback: string }>(
      '/api/v1/admin/ai/health',
    ),
};

interface TeamStatsResponse {
  team_register_num: number;
  team_valid_num: number;
  team_commission: string;
  lv1_valid_num: number;
  lv2_valid_num: number;
  lv3_valid_num: number;
  lv1_register_num: number;
  lv2_register_num: number;
  lv3_register_num: number;
}

interface TeamMemberResponse {
  id: string;
  username: string;
  is_official: boolean;
  vip_level: number;
  created_at: string;
}

interface TeamMemberListResponse {
  items: TeamMemberResponse[];
  total: number;
  page: number;
  limit: number;
  level: number;
}

export interface TeamMember {
  id: string;
  username: string;
  isOfficial: boolean;
  vipLevel: number;
  createdAt: string;
}

export interface TeamMemberList {
  items: TeamMember[];
  total: number;
  page: number;
  limit: number;
  level: number;
}

function mapTeamMember(data: TeamMemberResponse): TeamMember {
  return {
    id: data.id,
    username: data.username,
    isOfficial: data.is_official,
    vipLevel: data.vip_level,
    createdAt: data.created_at,
  };
}

function mapTeamMemberList(data: TeamMemberListResponse): TeamMemberList {
  return {
    items: data.items.map(mapTeamMember),
    total: data.total,
    page: data.page,
    limit: data.limit,
    level: data.level,
  };
}

export const teamApi = {
  summary: () =>
    apiRequest<{ id: string; name: string; member_count: number; invite_code: string } | null>(
      '/api/v1/team',
    ),

  stats: async (days = 0) => {
    const res = await apiRequest<TeamStatsResponse>(`/api/v1/team/stats?days=${days}`);
    return {
      teamRegisterNum: res.team_register_num,
      teamValidNum: res.team_valid_num,
      teamCommission: res.team_commission,
      lv1ValidNum: res.lv1_valid_num,
      lv2ValidNum: res.lv2_valid_num,
      lv3ValidNum: res.lv3_valid_num,
    };
  },

  members: async (level = 1, page = 1, limit = 20) => {
    const qs = new URLSearchParams({
      level: String(level),
      page: String(page),
      limit: String(limit),
    });
    const res = await apiRequest<TeamMemberListResponse>(`/api/v1/team/members?${qs}`);
    return mapTeamMemberList(res);
  },

  unfinished: async (level = 1, page = 1, limit = 20) => {
    const qs = new URLSearchParams({
      level: String(level),
      page: String(page),
      limit: String(limit),
    });
    const res = await apiRequest<TeamMemberListResponse>(`/api/v1/team/unfinished?${qs}`);
    return mapTeamMemberList(res);
  },
};
