'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { ApiError } from '@/lib/api/client';
import { authApi } from '@/lib/api/endpoints';
import { resetConfirmSchema, resetRequestSchema } from '@/lib/validations/auth';
import { useTranslations } from '@/lib/i18n';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const tokenFromUrl = searchParams.get('token') ?? '';
  const { toast } = useToast();
  const { t } = useTranslations();
  const [email, setEmail] = useState('');
  const [token, setToken] = useState(tokenFromUrl);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const requestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = resetRequestSchema.safeParse({ email });
    if (!parsed.success) {
      toast(parsed.error.issues[0]?.message ?? t('common.invalid'), 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await authApi.requestPasswordReset(email);
      toast(res.message, 'success');
    } catch {
      toast('Anfrage konnte nicht gesendet werden', 'error');
    } finally {
      setLoading(false);
    }
  };

  const confirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = resetConfirmSchema.safeParse({ token, password });
    if (!parsed.success) {
      toast(parsed.error.issues[0]?.message ?? t('common.invalid'), 'error');
      return;
    }
    setLoading(true);
    try {
      await authApi.confirmPasswordReset(token, password);
      toast('Passwort aktualisiert - bitte anmelden', 'success');
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Fehler', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      <Card title="Passwort zurücksetzen">
        <form onSubmit={requestReset} className="space-y-4">
          <Input
            label="E-Mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button type="submit" loading={loading} className="w-full" variant="secondary">
            Link anfordern
          </Button>
        </form>
      </Card>

      <Card title="Neues Passwort setzen">
        <form onSubmit={confirmReset} className="space-y-4">
          <Input label="Token" value={token} onChange={(e) => setToken(e.target.value)} />
          <Input
            label="Neues Passwort"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" loading={loading} className="w-full">
            Passwort speichern
          </Button>
        </form>
      </Card>

      <p className="text-center text-sm text-text-muted">
        <Link href="/login" className="text-link hover:underline">
          Zurück zur Anmeldung
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Suspense fallback={<div className="text-text-muted">Laden...</div>}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
