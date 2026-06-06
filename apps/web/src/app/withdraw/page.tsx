'use client';

import { useEffect, useState } from 'react';
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

interface WithdrawHistoryItem {
  id: string;
  amount: string;
  to_address: string;
  status: string;
  created_at: string;
}

export default function WithdrawPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { toast } = useToast();
  const [amount, setAmount] = useState('');
  const [bindAddress, setBindAddress] = useState('');
  const [boundAddress, setBoundAddress] = useState<string | null>(null);
  const [history, setHistory] = useState<WithdrawHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [binding, setBinding] = useState(false);

  useEffect(() => {
    if (!user) return;
    withdrawApi
      .history()
      .then(setHistory)
      .catch((err) => {
        toast(
          err instanceof ApiError ? err.message : 'Verlauf konnte nicht geladen werden',
          'error',
        );
      });
  }, [user, toast]);

  const submitBind = async () => {
    if (bindAddress.length < 34) {
      toast('Ungültige TRC20-Adresse', 'error');
      return;
    }
    setBinding(true);
    try {
      const res = await withdrawApi.bindAddress('TRC20', bindAddress);
      setBoundAddress(res.address);
      toast('Auszahlungsadresse gebunden', 'success');
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setBinding(false);
    }
  };

  const submitWithdraw = async () => {
    if (!amount || Number(amount) < 10) {
      toast('Mindestbetrag 10 USDT', 'error');
      return;
    }
    setLoading(true);
    try {
      await withdrawApi.request(amount);
      toast('Auszahlung beantragt — Admin-Freigabe erforderlich', 'success');
      setAmount('');
      const items = await withdrawApi.history();
      setHistory(items);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setLoading(false);
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
        title="Auszahlen"
        subtitle="Min. 10 USDT · Fee 1 USDT · Admin-Freigabe"
        accent="TRC20"
      />

      <SubNavTabs tabs={walletSubNav} />
      {!boundAddress && (
        <Card title="Auszahlungsadresse binden (einmalig)" className="max-w-md">
          <Input
            label="TRC20 Empfängeradresse"
            value={bindAddress}
            onChange={(e) => setBindAddress(e.target.value)}
          />
          <Button variant="pill" className="mt-4 w-full" onClick={submitBind} loading={binding}>
            Adresse binden
          </Button>
        </Card>
      )}

      {boundAddress && (
        <div className="invite-code-box mb-4 max-w-md">
          <p className="text-xs text-text-muted">Gebundene Adresse</p>
          <p className="mt-1 break-all font-mono text-sm text-white">{boundAddress}</p>
        </div>
      )}

      <Card title="Auszahlung beantragen" className="max-w-md">
        <Input label="Betrag (USDT)" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <Button
          variant="pill"
          className="mt-4 w-full"
          onClick={submitWithdraw}
          loading={loading}
          disabled={!boundAddress}
        >
          Beantragen
        </Button>
      </Card>

      <Card title="Verlauf" className="mt-6">
        {history.length === 0 ? (
          <p className="text-text-muted">Keine Auszahlungen</p>
        ) : (
          <ul className="space-y-1">
            {history.map((w) => (
              <li
                key={w.id}
                className="flex items-center justify-between rounded-xl bg-white/[0.02] px-3 py-2.5 text-sm"
              >
                <span className="font-mono text-success">{w.amount} USDT</span>
                <span className="text-text-muted">{w.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}
