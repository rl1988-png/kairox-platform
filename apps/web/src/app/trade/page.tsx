'use client';

import type { TradeLevel, TradeSession } from '@kairox/shared';
import clsx from 'clsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { useToast } from '@/components/ui/Toast';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { tradeApi } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';

function formatCountdown(totalSeconds: number): string {
  const sec = Math.max(0, totalSeconds);
  const min = Math.floor(sec / 60);
  const rem = sec % 60;
  return `${String(min).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

function stateLabel(state: TradeSession['state']): string {
  const labels: Record<string, string> = {
    pre_started: 'Bestätigung ausstehend',
    running: 'Läuft',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen',
  };
  return labels[state] ?? state;
}

export default function TradePage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { toast } = useToast();
  const [levels, setLevels] = useState<TradeLevel[]>([]);
  const [active, setActive] = useState<TradeSession | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<TradeLevel | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [preStartId, setPreStartId] = useState<string | null>(null);
  const [preStartExpires, setPreStartExpires] = useState<string | null>(null);
  const [countdown, setCountdown] = useState('');
  const [loading, setLoading] = useState(false);
  const completeRequestedRef = useRef(false);

  const refresh = useCallback(async () => {
    const [lvls, current] = await Promise.all([tradeApi.levels(), tradeApi.active()]);
    setLevels(lvls);
    setActive(current);
    if (current?.state === 'pre_started') {
      setPreStartId(current.id);
      setPreStartExpires(current.expiresAt);
    }
  }, []);

  useEffect(() => {
    if (user) refresh().catch(() => undefined);
  }, [user, refresh]);

  useEffect(() => {
    if (!preStartExpires && active?.state !== 'running') return;
    const target =
      active?.state === 'running' && active.startedAt && active.durationSeconds
        ? new Date(active.startedAt).getTime() + active.durationSeconds * 1000
        : preStartExpires
          ? new Date(preStartExpires).getTime()
          : null;
    if (!target) return;

    const tick = () => setCountdown(formatCountdown(Math.floor((target - Date.now()) / 1000)));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [preStartExpires, active]);

  useEffect(() => {
    if (active?.state !== 'running' || !active.startedAt || !active.durationSeconds) {
      completeRequestedRef.current = false;
      return;
    }

    const endAt = new Date(active.startedAt).getTime() + active.durationSeconds * 1000;
    let mounted = true;
    let completeTimer: ReturnType<typeof setTimeout> | null = null;

    const fireComplete = () => {
      if (!mounted || completeRequestedRef.current) return;
      completeRequestedRef.current = true;

      tradeApi
        .complete(active.id)
        .then((done) => {
          if (!mounted) return;
          setActive(done);
          toast('Trade abgeschlossen — Profit gutgeschrieben', 'success');
        })
        .catch((err) => {
          if (!mounted) return;
          completeRequestedRef.current = false;
          toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
        });
    };

    const remainingMs = endAt - Date.now();
    if (remainingMs <= 0) {
      fireComplete();
    } else {
      completeTimer = setTimeout(fireComplete, remainingMs);
    }

    return () => {
      mounted = false;
      if (completeTimer) clearTimeout(completeTimer);
    };
  }, [active?.id, active?.state, active?.startedAt, active?.durationSeconds, toast]);

  const openDialog = async (level: TradeLevel) => {
    if (!level.available) {
      toast('Nicht genügend Guthaben für dieses Level', 'error');
      return;
    }
    setSelectedLevel(level);
    setLoading(true);
    try {
      const trade = await tradeApi.preStart(level.level);
      setPreStartId(trade.id);
      setPreStartExpires(trade.expiresAt);
      setActive(trade);
      setDialogOpen(true);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setLoading(false);
    }
  };

  const confirmStart = async () => {
    if (!preStartId) return;
    setLoading(true);
    try {
      const trade = await tradeApi.start(preStartId);
      setActive(trade);
      setDialogOpen(false);
      toast('Trade gestartet', 'success');
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
        title="Trade Center"
        subtitle="Pre-Start → Bestätigen → Laufzeit"
        accent={`VIP${user.vipLevel ?? 1}`}
      />

      {active && (active.state === 'pre_started' || active.state === 'running') && (
        <Card title="Aktiver Trade" className="mb-6 border-kairox-pink/25">
          <p className="text-lg font-semibold text-kairox-pink">{stateLabel(active.state)}</p>
          <p className="mt-1 font-mono text-white">{active.amount} USDT · VIP{active.vipLevel}</p>
          <p className="mt-3 inline-block rounded-full bg-kairox-pink/15 px-4 py-1 font-mono text-sm text-kairox-pink">
            {countdown}
          </p>
          {active.state === 'pre_started' && (
            <Button variant="pill" className="mt-4 w-full sm:w-auto" onClick={confirmStart} loading={loading}>
              Trade bestätigen
            </Button>
          )}
        </Card>
      )}

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-kairox-pink">
        VIP Levels
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {levels.map((level) => (
          <button
            key={level.level}
            type="button"
            disabled={!level.available || loading || !!active}
            onClick={() => openDialog(level)}
            className={clsx(
              'vip-card',
              (!level.available || loading || !!active) && 'vip-card-disabled',
            )}
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-kairox-pink">
              {level.name}
            </p>
            <p className="mt-2 text-2xl font-bold text-white">{level.tradeAmount} USDT</p>
            <p className="mt-2 text-xs text-text-muted">
              Min. {level.minBalance} USDT · {(Number(level.profitRate) * 100).toFixed(2)}% Profit
            </p>
          </button>
        ))}
      </div>

      {dialogOpen && selectedLevel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <Card title="Trade bestätigen" className="w-full max-w-md border-kairox-pink/30">
            <p className="text-text-primary">
              {selectedLevel.name}: {selectedLevel.tradeAmount} USDT für ca.{' '}
              {Math.floor(selectedLevel.durationSeconds / 60)} Min.
            </p>
            <p className="mt-2 text-sm text-text-muted">
              Bestätigung innerhalb von {countdown || '01:00'} erforderlich
            </p>
            <div className="mt-5 flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={() => setDialogOpen(false)}>
                Abbrechen
              </Button>
              <Button variant="pill" className="flex-1" onClick={confirmStart} loading={loading}>
                Starten
              </Button>
            </div>
          </Card>
        </div>
      )}

      {active?.state === 'completed' && (
        <Card title="Ergebnis" className="mt-6">
          <p className="stat-value text-kairox-pink">+{active.profit ?? '0'} USDT</p>
          <p className="mt-1 text-sm text-text-muted">Profit gutgeschrieben</p>
          <Button
            className="mt-4"
            variant="secondary"
            onClick={() => {
              setActive(null);
              setPreStartId(null);
              refresh();
            }}
          >
            Neuer Trade
          </Button>
        </Card>
      )}
    </AppShell>
  );
}
