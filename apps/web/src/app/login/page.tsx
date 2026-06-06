'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import clsx from 'clsx';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';
import { loginSchema } from '@/lib/validations/auth';
import { ApiError } from '@/lib/api/client';

const GENERIC_LOGIN_ERROR = 'Ungültige Anmeldedaten';

export default function LoginPage() {
  const { login } = useAuth();
  const { toast } = useToast();
  const [tab, setTab] = useState<'username' | 'phone'>('username');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === 'phone') {
      toast('Phone login folgt in Kürze', 'error');
      return;
    }

    const result = loginSchema.safeParse({ username, password, rememberMe });
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
      await login(username, password, rememberMe);
      toast('Erfolgreich angemeldet', 'success');
    } catch (err) {
      const msg =
        err instanceof ApiError && err.status === 401 ? GENERIC_LOGIN_ERROR : 'Anmeldung fehlgeschlagen';
      toast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="mx-auto w-full max-w-md">
        <div className="login-tabs">
          <button
            type="button"
            className={clsx('login-tab', tab === 'username' && 'login-tab-active')}
            onClick={() => setTab('username')}
          >
            Username login
          </button>
          <button
            type="button"
            className={clsx('login-tab', tab === 'phone' && 'login-tab-active')}
            onClick={() => setTab('phone')}
          >
            Phone login
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {tab === 'username' ? (
            <Input
              label="Account"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              error={errors.username}
              autoComplete="username"
              placeholder="Enter your username"
              iconSrc="/assets/kairox/icon-user.png"
            />
          ) : (
            <Input
              label="Phone number"
              disabled
              placeholder="Coming soon"
              iconSrc="/assets/kairox/icon-user.png"
            />
          )}

          <div className="space-y-2">
            <label htmlFor="password" className="block pl-3 text-base font-medium text-white">
              Password
            </label>
            <div className="relative">
              <Image
                src="/assets/kairox/icon-password.png"
                alt=""
                width={28}
                height={28}
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 opacity-90"
              />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="Enter your password"
                className={clsx(
                  'kairox-input kairox-input-with-icon pr-12',
                  errors.password && 'border-danger',
                )}
              />
              <button
                type="button"
                aria-label={showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                onClick={() => setShowPassword((v) => !v)}
              >
                <Image src="/assets/kairox/icon-eye.svg" alt="" width={20} height={20} />
              </button>
            </div>
            {errors.password && <p className="pl-3 text-xs text-danger">{errors.password}</p>}
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 text-kairox-pink">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="sr-only"
              />
              <span className="flex h-5 w-5 items-center justify-center rounded border border-kairox-pink text-xs">
                {rememberMe ? '✓' : ''}
              </span>
              Remember password
            </label>
            <Link href="/reset-password" className="text-kairox-pink hover:underline">
              Reset password
            </Link>
          </div>

          <button type="submit" disabled={loading} className="kairox-btn-pill disabled:opacity-60">
            {loading ? 'Login…' : 'Login'}
          </button>
        </form>

        <div className="mt-5 flex justify-between text-sm text-kairox-pink">
          <Link href="/download" className="hover:underline">
            Download APP
          </Link>
          <Link href="/register" className="hover:underline">
            Register an account
          </Link>
        </div>
        <div className="login-yinsi mt-6 text-center">
          <Link href="/info/privacy" className="text-sm text-kairox-pink hover:underline">
            Privacy Policy
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}
