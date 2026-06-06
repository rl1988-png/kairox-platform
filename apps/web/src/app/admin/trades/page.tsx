'use client';

import { useEffect, useState } from 'react';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { DataTable } from '@/components/admin/DataTable';
import { adminApi, type AdminTrade } from '@/lib/api/endpoints';

export default function AdminTradesPage() {
  const [rows, setRows] = useState<AdminTrade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi
      .trades()
      .then(setRows)
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <AdminPageHeader title="Trades" subtitle="All trade sessions" />
      <DataTable
        loading={loading}
        rows={rows}
        rowKey={(r) => r.id}
        columns={[
          { key: 'state', header: 'State', render: (r) => r.state },
          { key: 'amount', header: 'Amount', render: (r) => r.amount },
          { key: 'vip', header: 'VIP', render: (r) => String(r.vipLevel ?? '—') },
          { key: 'profit', header: 'Profit', render: (r) => r.profit ?? '—' },
        ]}
      />
    </>
  );
}
