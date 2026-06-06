'use client';

import { useEffect, useState } from 'react';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { DataTable } from '@/components/admin/DataTable';
import { adminApi, type AuditLogEntry } from '@/lib/api/endpoints';

export default function AdminAuditPage() {
  const [rows, setRows] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi
      .audit()
      .then((res) => setRows(res.items))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <AdminPageHeader title="Audit Log" subtitle="Immutable admin action trail" />
      <DataTable
        loading={loading}
        rows={rows}
        rowKey={(r) => r.id}
        columns={[
          { key: 'action', header: 'Action', render: (r) => r.action },
          { key: 'target', header: 'Target', render: (r) => r.targetType },
          { key: 'ip', header: 'IP', render: (r) => r.ipAddress ?? '—' },
          {
            key: 'time',
            header: 'Time',
            render: (r) => new Date(r.createdAt).toLocaleString(),
          },
        ]}
      />
    </>
  );
}
