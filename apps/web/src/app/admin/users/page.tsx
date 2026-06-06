'use client';

import { useEffect, useState } from 'react';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { DataTable } from '@/components/admin/DataTable';
import { UserDetailDrawer } from '@/components/admin/UserDetailDrawer';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';
import { adminApi, type AdminUser } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';

export default function AdminUsersPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [rows, setRows] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AdminUser | null>(null);

  const load = () => {
    setLoading(true);
    adminApi
      .users()
      .then((res) => setRows(res.items))
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Load failed'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <AdminPageHeader title="Users" subtitle="Accounts, VIP, manual credit" />
      <DataTable
        loading={loading}
        error={error}
        rows={rows}
        rowKey={(r) => r.id}
        columns={[
          { key: 'username', header: 'User', render: (r) => r.username },
          { key: 'role', header: 'Role', render: (r) => r.role },
          { key: 'vip', header: 'VIP', render: (r) => String(r.vipLevel) },
          {
            key: 'actions',
            header: '',
            render: (r) => (
              <Button variant="ghost" onClick={() => setSelected(r)}>
                Details
              </Button>
            ),
          },
        ]}
      />
      <UserDetailDrawer
        user={selected}
        open={selected !== null}
        onClose={() => setSelected(null)}
        canCredit={user?.role === 'admin'}
        onManualCredit={async (payload) => {
          if (!selected) return;
          await adminApi.manualCredit(selected.id, payload);
          toast('Gutschrift gebucht', 'success');
          load();
        }}
      />
    </>
  );
}
