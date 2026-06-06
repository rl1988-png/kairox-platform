'use client';

import Image from 'next/image';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { KairoxRobot } from '@/components/brand/KairoxRobot';

type AuthLayoutProps = {
  children: ReactNode;
  showRobot?: boolean;
};

export function AuthLayout({ children, showRobot = true }: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-overlay">
      <div className="auth-bg absolute inset-0" aria-hidden />
      <div className="auth-bg-overlay absolute inset-0" aria-hidden />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="flex items-center justify-center pt-10">
          <Link href="/" className="flex flex-col items-center gap-3">
            <Image
              src="/assets/kairox/logo.png"
              alt="Kairox AI"
              width={90}
              height={90}
              priority
              className="drop-shadow-[0_0_16px_rgba(252,129,185,0.35)]"
            />
            <span className="text-sm font-medium tracking-[0.2em] text-kairox-pink/90">
              KAIROX AI
            </span>
          </Link>
        </header>

        {showRobot && (
          <div className="mt-4 flex justify-center">
            <KairoxRobot size={110} priority />
          </div>
        )}

        <div className="welcome-text px-6 pt-4">
          <p className="text-2xl font-semibold leading-tight text-kairox-pink">Hello,</p>
          <p className="text-2xl font-semibold leading-tight text-kairox-pink">
            welcome to Kairox
          </p>
        </div>

        <main className="flex flex-1 flex-col px-4 pb-10 pt-6">{children}</main>
      </div>
    </div>
  );
}
