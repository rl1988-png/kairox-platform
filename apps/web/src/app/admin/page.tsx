'use client';

import { useEffect, useState } from 'react';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { StatGrid } from '@/components/ui/StatGrid';
import { adminApi, type AdminDashboard } from '@/lib/api/endpoints';

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi
      .dashboard()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const stats = data
    ? [
        { label: 'Users total', value: String(data.usersTotal) },
        { label: 'Active today', value: String(data.usersActiveToday) },
        { label: 'Recharge pending', value: String(data.rechargePending) },
        { label: 'Recharge paid today', value: `${data.rechargePaidToday} USDT` },
        { label: 'Withdraw pending', value: String(data.withdrawPending) },
        { label: 'Withdraw pending amount', value: `${data.withdrawPendingAmount} USDT` },
        { label: 'Trades today', value: String(data.tradesToday) },
        { label: 'Hot wallet', value: `${data.hotWalletBalance} USDT` },
      ]
    : [];

  return (
    <>
      <AdminPageHeader title="Dashboard" subtitle="Operative Kennzahlen" />
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
        </div>
      ) : data ? (
        <StatGrid items={stats} />
      ) : (
        <p className="text-text-muted">Dashboard konnte nicht geladen werden.</p>
      )}
    </>
  );
}
