'use client';

import { useEffect, useState } from 'react';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { DataTable } from '@/components/admin/DataTable';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';
import { adminApi, type AdminWithdrawRequest } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';

export default function AdminWithdrawPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [rows, setRows] = useState<AdminWithdrawRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const isAdmin = user?.role === 'admin';

  const load = () => {
    setLoading(true);
    Promise.all([adminApi.withdrawRequests('pending'), adminApi.withdrawRequests('processing')])
      .then(([pending, processing]) => setRows([...pending, ...processing]))
      .catch((err) => toast(err instanceof ApiError ? err.message : 'Load failed', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [toast]);

  const approve = async (row: AdminWithdrawRequest) => {
    const txHash = window.prompt('TRC20 payout TX hash');
    if (!txHash) return;
    await adminApi.approveWithdraw(row.id, { adminNote: 'Broadcasted', txHash });
    toast('Processing', 'success');
    load();
  };

  const confirm = async (row: AdminWithdrawRequest) => {
    const raw = window.prompt('Confirmations', String(row.confirmations || 19));
    if (!raw) return;
    const confirmations = Number(raw);
    if (!Number.isInteger(confirmations) || confirmations < 0) {
      toast('Invalid confirmations', 'error');
      return;
    }
    await adminApi.confirmWithdraw(row.id, {
      adminNote: 'On-chain confirmed',
      confirmations,
    });
    toast('Completed', 'success');
    load();
  };

  const fail = async (row: AdminWithdrawRequest) => {
    await adminApi.failWithdraw(row.id, { adminNote: 'Broadcast failed' });
    toast('Failed', 'success');
    load();
  };

  const reject = async (row: AdminWithdrawRequest) => {
    await adminApi.rejectWithdraw(row.id, { adminNote: 'Rejected' });
    toast('Rejected', 'success');
    load();
  };

  return (
    <>
      <AdminPageHeader
        title="Withdraw Requests"
        subtitle="Pending and on-chain processing payouts"
      />
      <DataTable
        loading={loading}
        rows={rows}
        rowKey={(r) => r.id}
        emptyMessage="Keine offenen Auszahlungen"
        columns={[
          { key: 'amount', header: 'Amount', render: (r) => `${r.amount} USDT` },
          { key: 'fee', header: 'Fee', render: (r) => `${r.feeAmount} USDT` },
          { key: 'address', header: 'Address', render: (r) => `${r.toAddress.slice(0, 12)}...` },
          { key: 'status', header: 'Status', render: (r) => r.status },
          { key: 'tx', header: 'TX', render: (r) => r.txHash?.slice(0, 12) ?? '-' },
          { key: 'conf', header: 'Conf.', render: (r) => String(r.confirmations) },
          {
            key: 'actions',
            header: 'Actions',
            render: (r) =>
              isAdmin ? (
                <div className="flex flex-wrap gap-2">
                  {r.status === 'pending' && (
                    <>
                      <Button onClick={() => approve(r)}>Approve</Button>
                      <Button variant="ghost" onClick={() => reject(r)}>
                        Reject
                      </Button>
                    </>
                  )}
                  {r.status === 'processing' && (
                    <>
                      <Button onClick={() => confirm(r)}>Confirm</Button>
                      <Button variant="ghost" onClick={() => fail(r)}>
                        Fail
                      </Button>
                    </>
                  )}
                </div>
              ) : (
                <span className="text-text-muted">Read-only</span>
              ),
          },
        ]}
      />
    </>
  );
}
