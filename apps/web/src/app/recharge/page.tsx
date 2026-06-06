'use client';

import type { RechargeOrder, RechargeOrderStatus } from '@kairox/shared';
import { useCallback, useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { PageBanner } from '@/components/ui/PageBanner';
import { QrCode } from '@/components/ui/QrCode';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useToast } from '@/components/ui/Toast';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { rechargeApi } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { createRechargeOrderSchema } from '@/lib/validations/recharge';
import { walletSubNav } from '@/lib/navigation';

function formatCountdown(expiresAt: string): string {
  const remainingMs = new Date(expiresAt).getTime() - Date.now();
  if (remainingMs <= 0) return '00:00';
  const totalSec = Math.floor(remainingMs / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

function statusLabel(status: RechargeOrderStatus['status']): string {
  const labels: Record<RechargeOrderStatus['status'], string> = {
    pending: 'Warte auf Zahlung',
    confirming: 'Bestätigung läuft',
    confirmed: 'Bezahlt',
    paid: 'Bezahlt',
    expired: 'Abgelaufen',
    failed: 'Fehlgeschlagen',
  };
  return labels[status] ?? status;
}

export default function RechargePage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { toast } = useToast();
  const [amount, setAmount] = useState('30');
  const [order, setOrder] = useState<RechargeOrder | null>(null);
  const [status, setStatus] = useState<RechargeOrderStatus | null>(null);
  const [countdown, setCountdown] = useState('');
  const [loading, setLoading] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);

  const pollStatus = useCallback(async (orderId: string) => {
    try {
      const next = await rechargeApi.getOrderStatus(orderId);
      setPollError(null);
      setStatus(next);
      if (next.status === 'paid' || next.status === 'confirmed') {
        toast('Einzahlung erfolgreich — Guthaben gutgeschrieben', 'success');
      }
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Status konnte nicht geladen werden';
      setPollError(message);
    }
  }, [toast]);

  useEffect(() => {
    if (!order) return;
    setCountdown(formatCountdown(order.expiresAt));
    const timer = setInterval(() => setCountdown(formatCountdown(order.expiresAt)), 1000);
    return () => clearInterval(timer);
  }, [order]);

  useEffect(() => {
    if (!order) return;
    if (status?.status === 'paid' || status?.status === 'expired' || status?.status === 'confirmed') {
      return;
    }

    let mounted = true;

    const runPoll = () => {
      if (!mounted) return;
      void pollStatus(order.id);
    };

    runPoll();
    const poller = setInterval(runPoll, 5000);
    return () => {
      mounted = false;
      clearInterval(poller);
    };
  }, [order, status?.status, pollStatus]);

  const createOrder = async () => {
    const parsed = createRechargeOrderSchema.safeParse({ amount, network: 'TRC20' });
    if (!parsed.success) {
      toast(parsed.error.issues[0]?.message ?? 'Ungültig', 'error');
      return;
    }
    setLoading(true);
    try {
      const created = await rechargeApi.createOrder(parsed.data);
      setPollError(null);
      setOrder(created);
      setStatus({
        id: created.id,
        status: created.status,
        txHash: created.txHash,
        confirmations: created.confirmations,
        expiresAt: created.expiresAt,
        paidAt: null,
      });
      toast('Auftrag erstellt — sende USDT an die Adresse', 'success');
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyAddress = async () => {
    if (!order?.depositAddress) return;
    await navigator.clipboard.writeText(order.depositAddress);
    toast('Adresse kopiert', 'success');
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
        title="Aufladen"
        subtitle="On-Chain-Verifizierung · Keine Screenshots"
        accent="TRC20 USDT"
      />

      <SubNavTabs tabs={walletSubNav} />
      {!order ? (
        <Card title="Betrag wählen" className="max-w-md">
          <Input
            label="Betrag (USDT)"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="30"
          />
          <p className="mt-2 text-xs text-text-muted">Minimum 30 USDT · Netzwerk TRC20</p>
          <Button variant="pill" className="mt-5 w-full" onClick={createOrder} loading={loading}>
            Einzahlungsauftrag erstellen
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Zahlungsdetails" className="border-kairox-pink/20">
            <div className="flex flex-col items-center gap-4">
              <div className="rounded-2xl bg-white p-3">
                <QrCode value={order.depositAddress} label="TRC20 Deposit" />
              </div>
              <p className="break-all rounded-xl bg-white/[0.03] p-3 text-center font-mono text-sm text-link">
                {order.depositAddress}
              </p>
              <Button variant="secondary" onClick={copyAddress} className="w-full">
                Adresse kopieren
              </Button>
            </div>
            <dl className="mt-5 space-y-2 text-sm">
              <div className="flex justify-between border-b border-border/40 pb-2">
                <dt className="text-text-muted">Betrag</dt>
                <dd className="font-mono">{order.expectedAmount} USDT</dd>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-2">
                <dt className="text-text-muted">Netzwerk</dt>
                <dd>TRC20</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-text-muted">Gültig noch</dt>
                <dd className="font-mono text-kairox-pink">{countdown}</dd>
              </div>
            </dl>
          </Card>

          <Card title="Status">
            <p className="text-xl font-semibold text-kairox-pink">
              {status ? statusLabel(status.status) : '—'}
            </p>
            {pollError && (
              <p className="mt-2 text-sm text-danger">{pollError} — erneuter Versuch in Kürze…</p>
            )}
            {status?.txHash && (
              <p className="mt-3 break-all rounded-xl bg-white/[0.03] p-2 font-mono text-xs text-text-muted">
                TX: {status.txHash}
              </p>
            )}
            {status && status.confirmations > 0 && (
              <p className="mt-2 text-sm text-text-muted">{status.confirmations} Bestätigungen</p>
            )}
            <p className="mt-4 text-xs leading-relaxed text-text-muted">
              Der Status wird automatisch aktualisiert. Gutschrift erfolgt erst nach On-Chain-Verifizierung.
            </p>
            {(status?.status === 'paid' || status?.status === 'expired') && (
              <Button
                className="mt-4 w-full"
                variant="secondary"
                onClick={() => {
                  setOrder(null);
                  setStatus(null);
                }}
              >
                Neue Einzahlung
              </Button>
            )}
          </Card>
        </div>
      )}
    </AppShell>
  );
}
