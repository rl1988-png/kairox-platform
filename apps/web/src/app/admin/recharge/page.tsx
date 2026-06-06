'use client';

import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { TxVerifyPanel } from '@/components/admin/TxVerifyPanel';
import { adminApi } from '@/lib/api/endpoints';

export default function AdminRechargePage() {
  return (
    <>
      <AdminPageHeader title="Recharge — TX Verify" subtitle="On-chain verification, no screenshots" />
      <div className="mt-8 max-w-xl">
        <TxVerifyPanel onVerify={(txHash) => adminApi.verifyTx(txHash)} />
      </div>
    </>
  );
}
