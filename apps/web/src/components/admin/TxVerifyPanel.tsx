'use client';

import { useState } from 'react';
import clsx from 'clsx';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface TxVerifyResult {
  tx_hash: string;
  found: boolean;
  amount_on_chain: string | null;
  to_address: string | null;
  confirmed: boolean;
  matches_order: boolean;
  matched_order_id: string | null;
  verdict: string;
}

interface TxVerifyPanelProps {
  onVerify: (txHash: string) => Promise<TxVerifyResult>;
}

const verdictStyles: Record<string, string> = {
  CREDIT_OK: 'bg-success/20 text-success',
  AMOUNT_MISMATCH: 'bg-warning/20 text-warning',
  WRONG_ADDRESS: 'bg-danger/20 text-danger',
  NOT_FOUND: 'bg-danger/20 text-danger',
  ALREADY_USED: 'bg-warning/20 text-warning',
};

export function TxVerifyPanel({ onVerify }: TxVerifyPanelProps) {
  const [txHash, setTxHash] = useState('');
  const [result, setResult] = useState<TxVerifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const verify = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await onVerify(txHash.trim());
      setResult(data);
    } catch {
      setError('Verifikation fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 rounded-lg border border-border bg-bg-secondary p-4">
      <Input label="TX Hash" value={txHash} onChange={(e) => setTxHash(e.target.value)} />
      <Button loading={loading} onClick={verify}>
        On-chain prüfen
      </Button>
      {error && <p className="text-danger">{error}</p>}
      {result && (
        <div className="space-y-2 text-sm">
          <span
            className={clsx(
              'inline-block rounded px-2 py-1 font-mono text-xs',
              verdictStyles[result.verdict] ?? 'bg-bg-tertiary text-text-muted',
            )}
          >
            {result.verdict}
          </span>
          <p className="text-text-muted">Found: {result.found ? 'yes' : 'no'}</p>
          {result.amount_on_chain && (
            <p className="font-mono text-text-primary">{result.amount_on_chain} USDT</p>
          )}
          {result.to_address && <p className="truncate font-mono text-xs">{result.to_address}</p>}
          {result.matched_order_id && (
            <p className="text-text-muted">Order: {result.matched_order_id}</p>
          )}
        </div>
      )}
    </div>
  );
}
