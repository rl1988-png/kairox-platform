'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export function MobileHeader() {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-border/60 bg-bg-primary/90 backdrop-blur-md lg:hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <Link href="/home" className="flex items-center gap-2">
          <Image src="/assets/kairox/logo.png" alt="Kairox" width={36} height={36} />
          <span className="text-lg font-bold text-kairox-pink">Kairox AI</span>
        </Link>
        <div className="text-right">
          <p className="text-sm font-medium text-text-primary">{user?.username}</p>
          <p className="text-[10px] uppercase tracking-wider text-text-muted">
            {user?.isOfficial ? 'Official' : 'Trial'}
          </p>
        </div>
      </div>
    </header>
  );
}
