'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { walletApi } from '@/lib/api/endpoints';
import { walletSubNav } from '@/lib/navigation';
import type { WalletSummary } from '@kairox/shared';

export default function WalletPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [wallet, setWallet] = useState<WalletSummary | null>(null);
  const [ledger, setLedger] = useState<
    Array<{ entry_type: string; amount: string; balance_after: string; created_at: string }>
  >([]);

  useEffect(() => {
    if (!user) return;
    walletApi.get().then((w) =>
      setWallet({
        userId: w.user_id,
        balance: w.balance,
        depositAddress: w.deposit_address,
      }),
    );
    walletApi.ledger().then(setLedger);
  }, [user]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell>
      <PageBanner
        title="Wallet"
        subtitle="TRC20 USDT · On-Chain"
        accent={user.username}
      >
        <p className="mt-3 stat-value">{wallet?.balance.available ?? '—'} USDT</p>
        <p className="text-xs text-text-muted">Verfügbar · Gesperrt {wallet?.balance.locked ?? '—'} USDT</p>
      </PageBanner>

      <SubNavTabs tabs={walletSubNav} />
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Guthaben">
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
              <span className="text-text-muted">Verfügbar</span>
              <span className="font-mono font-semibold text-success">
                {wallet?.balance.available ?? '—'} USDT
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
              <span className="text-text-muted">Gesperrt</span>
              <span className="font-mono font-semibold text-warning">
                {wallet?.balance.locked ?? '—'} USDT
              </span>
            </div>
          </div>
        </Card>

        <Card title="Einzahlungsadresse" subtitle="TRC20 USDT">
          <p className="break-all rounded-xl bg-white/[0.03] p-3 font-mono text-sm text-link">
            {wallet?.depositAddress ?? 'Nicht konfiguriert'}
          </p>
        </Card>
      </div>

      <Card title="Ledger" className="mt-6">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Typ</th>
                <th>Betrag</th>
                <th>Saldo</th>
                <th>Datum</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((entry, i) => (
                <tr key={i}>
                  <td className="capitalize text-text-primary">{entry.entry_type.replace(/_/g, ' ')}</td>
                  <td className="font-mono">{entry.amount}</td>
                  <td className="font-mono">{entry.balance_after}</td>
                  <td className="text-text-muted">{new Date(entry.created_at).toLocaleString('de')}</td>
                </tr>
              ))}
              {ledger.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-text-muted">
                    Keine Einträge
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}
