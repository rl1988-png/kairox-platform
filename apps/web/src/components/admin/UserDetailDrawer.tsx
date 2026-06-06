'use client';

import { ManualCreditForm } from '@/components/admin/ManualCreditForm';
import { Button } from '@/components/ui/Button';
import type { AdminUser } from '@/lib/api/endpoints';

interface UserDetailDrawerProps {
  user: AdminUser | null;
  open: boolean;
  onClose: () => void;
  canCredit: boolean;
  onManualCredit: (payload: {
    amount: string;
    reason: string;
    idempotencyKey: string;
  }) => Promise<void>;
}

export function UserDetailDrawer({
  user,
  open,
  onClose,
  canCredit,
  onManualCredit,
}: UserDetailDrawerProps) {
  if (!open || !user) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-overlay/60">
      <div className="h-full w-full max-w-md overflow-y-auto border-l border-border bg-bg-primary p-6 shadow-card">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{user.username}</h2>
          <Button variant="ghost" onClick={onClose}>
            Schließen
          </Button>
        </div>
        <dl className="mt-4 space-y-2 text-sm">
          <div>
            <dt className="text-text-muted">Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Role</dt>
            <dd>{user.role}</dd>
          </div>
          <div>
            <dt className="text-text-muted">VIP</dt>
            <dd>{user.vipLevel}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Official</dt>
            <dd>{user.isOfficial ? 'yes' : 'trial'}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Withdraw address</dt>
            <dd className="break-all font-mono text-xs">{user.withdrawalAddress ?? '—'}</dd>
          </div>
        </dl>
        {canCredit && (
          <div className="mt-6">
            <ManualCreditForm userId={user.id} onSubmit={onManualCredit} />
          </div>
        )}
      </div>
    </div>
  );
}
