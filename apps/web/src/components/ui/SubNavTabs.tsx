'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { isSubNavActive, type SubNavItem } from '@/lib/navigation';
import { useTranslations } from '@/lib/i18n';

type SubNavTabsProps = {
  tabs: SubNavItem[];
  className?: string;
};

export function SubNavTabs({ tabs, className }: SubNavTabsProps) {
  const pathname = usePathname();
  const { t } = useTranslations();

  return (
    <nav
      className={clsx('login-tabs mb-6 flex-nowrap overflow-x-auto pb-1', className)}
      aria-label="Unternavigation"
    >
      {tabs.map((tab) => {
        const active = isSubNavActive(pathname, tab);
        const label = tab.labelKey ? t(tab.labelKey) : tab.label;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={clsx('login-tab shrink-0 whitespace-nowrap', active && 'login-tab-active')}
            aria-current={active ? 'page' : undefined}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
