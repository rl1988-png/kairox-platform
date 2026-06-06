'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { PageBanner } from '@/components/ui/PageBanner';
import { Modal } from '@/components/ui/Modal';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useTranslations } from '@/lib/i18n';
import { walletApi } from '@/lib/api/endpoints';

export default function HomePage() {
  const { user, loading } = useRequireAuth();
  const { t } = useTranslations();
  const [showAnnouncement, setShowAnnouncement] = useState(true);
  const [balance, setBalance] = useState<string>('—');

  useEffect(() => {
    if (!user) return;
    walletApi
      .get()
      .then((w) => setBalance(w.balance.available))
      .catch(() => setBalance('—'));
  }, [user]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  const actions = [
    { href: '/trade', label: t('home.actionTrade'), sub: t('home.actionTradeSub') },
    { href: '/recharge', label: t('home.actionRecharge'), sub: t('home.actionRechargeSub') },
    { href: '/withdraw', label: t('home.actionWithdraw'), sub: t('home.actionWithdrawSub') },
    { href: '/wallet', label: t('home.actionWallet'), sub: t('home.actionWalletSub') },
    { href: '/team', label: t('home.actionTeam'), sub: t('home.actionTeamSub') },
    { href: '/account/invite', label: t('home.actionInvite'), sub: t('home.actionInviteSub') },
  ];

  return (
    <AppShell>
      <PageBanner
        accent={`Hello, ${user.username}`}
        title={t('home.title')}
        subtitle={t('home.balanceLabel')}
      >
        <p className="mt-3 stat-value">{balance} USDT</p>
      </PageBanner>

      <Modal open={showAnnouncement} onClose={() => setShowAnnouncement(false)} title={t('home.announcement')}>
        <ul className="space-y-2 text-sm text-text-muted">
          <li>• {t('home.bonus')}</li>
          <li>• {t('home.referral')}</li>
          <li>• {t('home.trial')}</li>
        </ul>
      </Modal>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {actions.map((action) => (
          <Link key={action.href} href={action.href} className="action-tile">
            <span className="text-base font-semibold text-kairox-pink">{action.label}</span>
            <span className="text-[11px] text-text-muted">{action.sub}</span>
          </Link>
        ))}
      </div>

      <div className="mt-6 kairox-card">
        <h2 className="mb-2 text-lg font-semibold text-kairox-pink">{t('home.platformNews')}</h2>
        <p className="text-sm leading-relaxed text-text-muted">{t('home.platformNewsBody')}</p>
      </div>
    </AppShell>
  );
}
