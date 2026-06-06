'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';

interface ManualCreditFormProps {
  userId: string;
  onSubmit: (payload: { amount: string; reason: string; idempotencyKey: string }) => Promise<void>;
  disabled?: boolean;
}

export function ManualCreditForm({ userId, onSubmit, disabled = false }: ManualCreditFormProps) {
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onSubmit({
        amount,
        reason,
        idempotencyKey: crypto.randomUUID(),
      });
      setAmount('');
      setReason('');
      setConfirmOpen(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3 rounded-lg border border-border bg-bg-secondary p-4">
      <p className="text-sm text-text-muted">Manual credit for user {userId.slice(0, 8)}…</p>
      <Input label="Betrag (USDT)" value={amount} onChange={(e) => setAmount(e.target.value)} />
      <Input label="Grund (min. 10 Zeichen)" value={reason} onChange={(e) => setReason(e.target.value)} />
      <Button disabled={disabled} onClick={() => setConfirmOpen(true)}>
        Gutschrift vorbereiten
      </Button>

      <Modal open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Gutschrift bestätigen">
        <p className="text-sm text-text-muted">
          Diese Aktion ist auditierbar und kann nicht rückgängig gemacht werden.
        </p>
        <p className="mt-2 font-mono text-text-primary">
          {amount} USDT — {reason}
        </p>
        <div className="mt-4 flex gap-2">
          <Button variant="ghost" onClick={() => setConfirmOpen(false)}>
            Abbrechen
          </Button>
          <Button loading={loading} onClick={handleConfirm}>
            Bestätigen
          </Button>
        </div>
      </Modal>
    </div>
  );
}
