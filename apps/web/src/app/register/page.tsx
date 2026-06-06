'use client';

import Link from 'next/link';
import { useState } from 'react';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';
import { registerSchema } from '@/lib/validations/auth';
import { ApiError } from '@/lib/api/client';

export default function RegisterPage() {
  const { register } = useAuth();
  const { toast } = useToast();
  const [form, setForm] = useState({ username: '', email: '', password: '', inviteCode: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = registerSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        if (issue.path[0]) fieldErrors[String(issue.path[0])] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setLoading(true);
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
        inviteCode: form.inviteCode,
      });
      toast('Konto erstellt — du bist angemeldet', 'success');
    } catch (err) {
      toast(err instanceof ApiError ? 'Registrierung fehlgeschlagen' : 'Fehler', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout showRobot>
      <div className="mx-auto w-full max-w-md space-y-5">
        <p className="pl-3 text-base font-medium text-white">Create your account</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Account"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            error={errors.username}
            iconSrc="/assets/kairox/icon-user.png"
            placeholder="Choose username"
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            error={errors.email}
            placeholder="your@email.com"
          />
          <Input
            label="Password"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            error={errors.password}
            iconSrc="/assets/kairox/icon-password.png"
            placeholder="Min. 8 characters"
          />
          <Input
            label="Invite code"
            value={form.inviteCode}
            onChange={(e) => setForm({ ...form, inviteCode: e.target.value })}
            error={errors.inviteCode}
            placeholder="KAIROX-DEV"
          />
          <button type="submit" disabled={loading} className="kairox-btn-pill disabled:opacity-60">
            {loading ? 'Register…' : 'Register'}
          </button>
        </form>
        <p className="text-center text-sm text-text-muted">
          Already registered?{' '}
          <Link href="/login" className="text-kairox-pink hover:underline">
            Login
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
