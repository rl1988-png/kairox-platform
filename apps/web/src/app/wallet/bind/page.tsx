'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { PageBanner } from '@/components/ui/PageBanner';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useToast } from '@/components/ui/Toast';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { withdrawApi } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { walletSubNav } from '@/lib/navigation';

export default function WalletBindPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { toast } = useToast();
  const [address, setAddress] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      await withdrawApi.bindAddress('TRC20', address);
      toast('Adresse gebunden', 'success');
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setSubmitting(false);
    }
  };

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
        title="Auszahlungsadresse"
        subtitle="USDT TRC20 — einmalig binden"
        accent={user.username}
      />
      <SubNavTabs tabs={walletSubNav} />

      <Card className="max-w-md" title="TRC20 Adresse binden">
        <Input label="TRC20 Adresse" value={address} onChange={(e) => setAddress(e.target.value)} />
        <p className="mt-2 text-xs text-text-muted">
          Die Adresse kann nur einmal gesetzt werden. Prüfe sie sorgfältig.
        </p>
        <Button variant="pill" className="mt-4 w-full" loading={submitting} onClick={submit}>
          Adresse binden
        </Button>
      </Card>
    </AppShell>
  );
}
