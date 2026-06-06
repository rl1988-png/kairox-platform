'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { Skeleton } from '@/components/ui/Skeleton';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useTranslations } from '@/lib/i18n';
import { walletApi } from '@/lib/api/endpoints';
import { walletSubNav } from '@/lib/navigation';

interface LedgerRow {
  entry_type: string;
  amount: string;
  balance_after: string;
  created_at: string;
}

export default function WalletBillPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { t } = useTranslations();
  const [rows, setRows] = useState<LedgerRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    walletApi
      .ledger()
      .then(setRows)
      .finally(() => setLoading(false));
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
        title={t('nav.bill')}
        subtitle="Recharge · Trade · Withdraw · Bonus"
        accent={user.username}
      />
      <SubNavTabs tabs={walletSubNav} />

      <Card title={t('wallet.bill')}>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-8" />
            <Skeleton className="h-8" />
          </div>
        ) : rows.length === 0 ? (
          <p className="text-text-muted">{t('common.empty')}</p>
        ) : (
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
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td className="capitalize">{r.entry_type.replace(/_/g, ' ')}</td>
                    <td className="font-mono">{r.amount} USDT</td>
                    <td className="font-mono">{r.balance_after}</td>
                    <td className="text-text-muted">
                      {new Date(r.created_at).toLocaleString('de')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AppShell>
  );
}
