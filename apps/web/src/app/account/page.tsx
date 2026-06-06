'use client';

import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useTranslations } from '@/lib/i18n';
import { accountSubNav } from '@/lib/navigation';

export default function AccountPage() {
  const { user, loading } = useRequireAuth();
  const { t } = useTranslations();

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell>
      <PageBanner
        title={t('nav.mine')}
        subtitle={user.email}
        accent={user.username}
      />

      <SubNavTabs tabs={accountSubNav} />
      {!user.isOfficial && (
        <div className="trial-banner mb-6">
          <p>{t('home.trial')}</p>
          {user.trialExpiresAt ? (
            <p className="mt-1 text-xs text-text-muted">
              Trial bis: {new Date(user.trialExpiresAt).toLocaleString('de-DE')}
            </p>
          ) : null}
        </div>
      )}

      <Card title={t('nav.profile')} className="max-w-md">
        <dl className="space-y-3 text-sm">
          <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
            <dt className="text-text-muted">Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
            <dt className="text-text-muted">VIP</dt>
            <dd>
              <Badge variant="pink">VIP{user.vipLevel ?? 1}</Badge>
            </dd>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
            <dt className="text-text-muted">Status</dt>
            <dd className={user.isOfficial ? 'text-success' : 'text-warning'}>
              {user.isOfficial ? 'Official' : 'Trial'}
            </dd>
          </div>
        </dl>
        <Link
          href="/account/invite"
          className="mt-5 inline-flex items-center text-sm font-medium text-kairox-pink hover:underline"
        >
          Invite-Code & QR →
        </Link>
      </Card>
    </AppShell>
  );
}
