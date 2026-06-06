'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';

const navItems = [
  { href: '/admin', label: 'Dashboard', exact: true },
  { href: '/admin/users', label: 'Users' },
  { href: '/admin/recharge', label: 'Recharge' },
  { href: '/admin/withdraw', label: 'Withdraw' },
  { href: '/admin/trades', label: 'Trades' },
  { href: '/admin/audit', label: 'Audit' },
  { href: '/admin/ai', label: 'AI' },
];

function isActive(pathname: string, href: string, exact?: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-bg-primary">
      <aside className="hidden w-64 flex-col border-r border-border/80 bg-bg-secondary/95 lg:flex">
        <div className="border-b border-border/80 p-6 text-center">
          <Link href="/admin" className="inline-flex flex-col items-center gap-2">
            <Image src="/assets/kairox/logo.png" alt="Kairox" width={52} height={52} />
            <span className="text-lg font-bold text-kairox-pink">Kairox Admin</span>
          </Link>
          <p className="mt-1 text-xs text-text-muted">Operations Console</p>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'block rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                isActive(pathname, item.href, item.exact)
                  ? 'bg-kairox-pink/15 text-kairox-pink'
                  : 'text-text-muted hover:bg-bg-tertiary hover:text-text-primary',
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-border/80 p-4">
          <p className="truncate text-sm font-medium text-text-primary">{user?.username}</p>
          <p className="text-xs capitalize text-text-muted">{user?.role}</p>
          <Link href="/home" className="mt-2 block text-xs text-link hover:underline">
            User area →
          </Link>
          <Button variant="ghost" className="mt-2 w-full" onClick={() => logout()}>
            Abmelden
          </Button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="border-b border-border/60 bg-bg-secondary/90 px-4 py-3 lg:hidden">
          <div className="flex items-center justify-between gap-3">
            <Link href="/admin" className="flex items-center gap-2">
              <Image src="/assets/kairox/logo.png" alt="" width={32} height={32} />
              <span className="font-bold text-kairox-pink">Admin</span>
            </Link>
            <Link href="/home" className="text-xs text-link">
              App
            </Link>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'shrink-0 rounded-full px-3 py-1 text-xs font-medium',
                  isActive(pathname, item.href, item.exact)
                    ? 'bg-kairox-pink/20 text-kairox-pink'
                    : 'bg-bg-tertiary text-text-muted',
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="flex-1 overflow-auto p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
