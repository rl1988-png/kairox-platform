'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import {
  NavAccountIcon,
  NavHomeIcon,
  NavTeamIcon,
  NavTradeIcon,
  NavWalletIcon,
} from '@/components/ui/NavIcons';
import { useTranslations } from '@/lib/i18n';
import { bottomNavItems, isNavActive } from '@/lib/navigation';

const iconMap = {
  '/home': NavHomeIcon,
  '/wallet': NavWalletIcon,
  '/trade': NavTradeIcon,
  '/team': NavTeamIcon,
  '/account': NavAccountIcon,
} as const;

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useTranslations();

  return (
    <nav className="wa-footer lg:hidden" aria-label="Hauptnavigation">
      {bottomNavItems.map((item) => {
        const active = isNavActive(pathname, item);
        const Icon = iconMap[item.href as keyof typeof iconMap];
        const label = item.labelKey ? t(item.labelKey) : item.label;
        const isCenter = item.center === true;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-label={label}
            aria-current={active ? 'page' : undefined}
            className={clsx('item', active && 'active', isCenter && 'item-trade')}
          >
            <span className={clsx('icon', isCenter && 'icon-trade')}>
              <Icon active={active} className={isCenter ? 'h-[50px] w-[50px]' : undefined} />
            </span>
            {!isCenter && <span className="text">{label}</span>}
          </Link>
        );
      })}
    </nav>
  );
}
