'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  NavAccountIcon,
  NavHomeIcon,
  NavRechargeIcon,
  NavTeamIcon,
  NavTradeIcon,
  NavWalletIcon,
  NavWithdrawIcon,
} from '@/components/ui/NavIcons';
import { useTranslations } from '@/lib/i18n';
import {
  isNavActive,
  sidebarExtraItems,
  sidebarNavItems,
  type NavItem,
} from '@/lib/navigation';

type SidebarLinkProps = {
  href: string;
  label: string;
  active: boolean;
  icon: ReactNode;
  compact?: boolean;
};

function SidebarLink({ href, label, active, icon, compact }: SidebarLinkProps) {
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={clsx('app-sidebar-link', active && 'app-sidebar-link-active', compact && 'py-2')}
    >
      <span className="app-sidebar-link-icon">{icon}</span>
      <span className="truncate">{label}</span>
    </Link>
  );
}

function mainNavIcon(href: string, active: boolean) {
  const props = { active, className: 'h-5 w-5' };
  switch (href) {
    case '/home':
      return <NavHomeIcon {...props} />;
    case '/wallet':
      return <NavWalletIcon {...props} />;
    case '/trade':
      return <NavTradeIcon {...props} />;
    case '/team':
      return <NavTeamIcon {...props} />;
    case '/account':
      return <NavAccountIcon {...props} />;
    default:
      return <NavHomeIcon {...props} />;
  }
}

function extraNavIcon(href: string, active: boolean) {
  const props = { active, className: 'h-[18px] w-[18px]' };
  if (href === '/recharge') return <NavRechargeIcon {...props} />;
  if (href === '/withdraw') return <NavWithdrawIcon {...props} />;
  if (href === '/wallet/bill') return <NavWalletIcon {...props} />;
  if (href === '/wallet/bind') return <NavWalletIcon {...props} />;
  if (href === '/team/list') return <NavTeamIcon {...props} />;
  if (href === '/account/invite') return <NavAccountIcon {...props} />;
  return <NavWalletIcon {...props} />;
}

function isExtraActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function renderMainItems(
  pathname: string,
  items: NavItem[],
  t: (key: string) => string,
) {
  return items.map((item) => {
    const active = isNavActive(pathname, item);
    const label = item.labelKey ? t(item.labelKey) : item.label;
    return (
      <SidebarLink
        key={item.href}
        href={item.href}
        label={label}
        active={active}
        icon={mainNavIcon(item.href, active)}
      />
    );
  });
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { t } = useTranslations();

  const initials = user?.username?.slice(0, 2).toUpperCase() ?? '?';

  return (
    <aside className="app-sidebar hidden lg:flex">
      <div className="app-sidebar-brand">
        <Link href="/home" className="app-sidebar-brand-link">
          <Image src="/assets/kairox/logo.png" alt="Kairox AI" width={48} height={48} priority />
          <div className="text-left">
            <span className="block text-base font-bold tracking-tight text-kairox-pink">Kairox AI</span>
            <span className="block text-[11px] text-text-muted">Trading & Wallet</span>
          </div>
        </Link>
      </div>

      <nav className="app-sidebar-nav" aria-label="Hauptnavigation">
        <div className="app-sidebar-group">
          <p className="app-sidebar-section">{t('sidebar.main')}</p>
          <div className="space-y-0.5">{renderMainItems(pathname, sidebarNavItems, t)}</div>
        </div>

        <div className="app-sidebar-group">
          <p className="app-sidebar-section">{t('sidebar.more')}</p>
          <div className="space-y-0.5">
            {sidebarExtraItems.map((item) => {
              const active = isExtraActive(pathname, item.href);
              const label = item.labelKey ? t(item.labelKey) : item.label;
              return (
                <SidebarLink
                  key={item.href}
                  href={item.href}
                  label={label}
                  active={active}
                  icon={extraNavIcon(item.href, active)}
                  compact
                />
              );
            })}
          </div>
        </div>

        {(user?.role === 'admin' || user?.role === 'support') && (
          <div className="app-sidebar-group">
            <p className="app-sidebar-section">{t('sidebar.admin')}</p>
            <SidebarLink
              href="/admin"
              label="Admin Console"
              active={pathname.startsWith('/admin')}
              icon={<NavTradeIcon active={pathname.startsWith('/admin')} className="h-5 w-5" />}
            />
          </div>
        )}
      </nav>

      <div className="app-sidebar-footer">
        {user ? (
          <div className="app-sidebar-user">
            <div className="app-sidebar-avatar" aria-hidden>
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-text-primary">{user.username}</p>
              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                <Badge variant="pink">VIP{user.vipLevel ?? 1}</Badge>
                <Badge variant={user.isOfficial ? 'success' : 'warning'}>
                  {user.isOfficial ? 'Official' : 'Trial'}
                </Badge>
              </div>
            </div>
          </div>
        ) : null}

        <Link href="/download" className="app-sidebar-meta-link">
          {t('sidebar.download')}
        </Link>

        <Button variant="ghost" className="mt-2 w-full justify-center" onClick={() => logout()}>
          {t('sidebar.logout')}
        </Button>
      </div>
    </aside>
  );
}
