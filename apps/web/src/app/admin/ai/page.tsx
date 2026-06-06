'use client';

import { useState } from 'react';
import clsx from 'clsx';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { adminApi } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';

const USE_CASES = [
  { id: 'support_assist', label: 'Support Assist' },
  { id: 'tx_fraud_check', label: 'TX Fraud Check' },
  { id: 'security_audit', label: 'Security Audit' },
] as const;

const SAMPLE_PAYLOADS: Record<string, string> = {
  support_assist: JSON.stringify({ message: 'I sent 3000 USDT but only see 30' }, null, 2),
  tx_fraud_check: JSON.stringify(
    { amount_on_chain: '30.00', claimed_amount: '3000.00', tx_hash: 'abc123' },
    null,
    2,
  ),
  security_audit: JSON.stringify({ failed_logins: 12, audit_events: 45 }, null, 2),
};

export default function AdminAiPage() {
  const { toast } = useToast();
  const [useCase, setUseCase] = useState<string>('tx_fraud_check');
  const [payload, setPayload] = useState(SAMPLE_PAYLOADS.tx_fraud_check);
  const [result, setResult] = useState<{
    data: Record<string, unknown>;
    provider: string;
    model: string;
    confidence: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const parsed = JSON.parse(payload) as Record<string, unknown>;
      const res = await adminApi.analyze(useCase, parsed);
      setResult(res);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Analyse fehlgeschlagen', 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyReply = () => {
    const reply = result?.data?.suggested_reply_de;
    if (typeof reply === 'string') {
      void navigator.clipboard.writeText(reply);
      toast('Antwort kopiert', 'success');
    }
  };

  return (
    <>
      <AdminPageHeader
        title="AI Analysis"
        subtitle="Suggestions for admin review only — no auto-reply to users"
      />

      <Card title="Analyse" className="mt-8 max-w-2xl">
        <div className="space-y-4">
          <label className="block text-sm text-text-muted">
            Use Case
            <select
              aria-label="Use case"
              className="mt-1 w-full rounded-lg border border-border bg-bg-tertiary px-3 py-2"
              value={useCase}
              onChange={(e) => {
                setUseCase(e.target.value);
                setPayload(SAMPLE_PAYLOADS[e.target.value] ?? '{}');
              }}
            >
              {USE_CASES.map((uc) => (
                <option key={uc.id} value={uc.id}>
                  {uc.label}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Payload (JSON)"
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
          />
          <Button loading={loading} onClick={run}>
            Analysieren
          </Button>
        </div>
      </Card>

      {result && (
        <Card title="Ergebnis" className="mt-6 max-w-2xl">
          <div className="mb-4 flex flex-wrap gap-2">
            <span className="rounded bg-bg-tertiary px-2 py-1 text-xs">
              Provider: {result.provider}
            </span>
            <span className="rounded bg-bg-tertiary px-2 py-1 text-xs">Model: {result.model}</span>
            <span
              className={clsx(
                'rounded px-2 py-1 text-xs',
                result.confidence >= 0.8
                  ? 'bg-success/20 text-success'
                  : 'bg-warning/20 text-warning',
              )}
            >
              Confidence: {(result.confidence * 100).toFixed(0)}%
            </span>
          </div>
          {typeof result.data.suggested_reply_de === 'string' && (
            <Button variant="ghost" className="mb-4" onClick={copyReply}>
              Copy suggested reply
            </Button>
          )}
          <pre className="overflow-x-auto rounded-lg bg-bg-tertiary p-4 text-xs">
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </Card>
      )}
    </>
  );
}
