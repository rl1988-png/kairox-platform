'use client';

import { useEffect, useMemo, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { StatGrid } from '@/components/ui/StatGrid';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { ApiError } from '@/lib/api/client';
import { teamApi, type TeamMemberList } from '@/lib/api/endpoints';
import { useTranslations } from '@/lib/i18n';
import { teamSubNav } from '@/lib/navigation';

const PAGE_SIZE = 10;
const levelOptions = [1, 2, 3] as const;
type MemberFilter = 'all' | 'unfinished';

const dateFormatter = new Intl.DateTimeFormat('de-DE', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

export default function TeamListPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const { t } = useTranslations();
  const [stats, setStats] = useState<Record<string, string | number> | null>(null);
  const [members, setMembers] = useState<TeamMemberList | null>(null);
  const [level, setLevel] = useState<(typeof levelOptions)[number]>(1);
  const [filter, setFilter] = useState<MemberFilter>('all');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const totalPages = useMemo(() => {
    if (!members) return 1;
    return Math.max(1, Math.ceil(members.total / members.limit));
  }, [members]);

  useEffect(() => {
    if (!user) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    const listRequest =
      filter === 'unfinished'
        ? teamApi.unfinished(level, page, PAGE_SIZE)
        : teamApi.members(level, page, PAGE_SIZE);

    Promise.all([teamApi.stats(7), listRequest])
      .then(([statsData, memberData]) => {
        if (!mounted) return;
        setStats(statsData);
        setMembers(memberData);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err instanceof ApiError ? err.message : 'Teamdaten konnten nicht geladen werden');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [filter, level, page, user]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell>
      <PageBanner
        title={t('nav.teamStats')}
        subtitle="Letzte 7 Tage - L1 / L2 / L3"
        accent={user.username}
      />
      <SubNavTabs tabs={teamSubNav} />

      {stats ? (
        <StatGrid
          items={[
            { label: 'Registriert', value: String(stats.teamRegisterNum) },
            { label: 'Valid', value: String(stats.teamValidNum) },
            { label: 'Commission', value: `${stats.teamCommission} USDT` },
            { label: 'LV1 Valid', value: String(stats.lv1ValidNum) },
          ]}
        />
      ) : null}

      <Card
        className="mt-6"
        title={t('team.members')}
        subtitle="Level, Aktivierung und VIP-Status deiner Downline."
      >
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-2">
            {levelOptions.map((item) => (
              <Button
                key={item}
                type="button"
                variant={level === item ? 'primary' : 'secondary'}
                className="min-w-14 px-3"
                onClick={() => {
                  setLevel(item);
                  setPage(1);
                }}
              >
                L{item}
              </Button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2 sm:w-auto">
            <Button
              type="button"
              variant={filter === 'all' ? 'primary' : 'secondary'}
              onClick={() => {
                setFilter('all');
                setPage(1);
              }}
            >
              Alle
            </Button>
            <Button
              type="button"
              variant={filter === 'unfinished' ? 'primary' : 'secondary'}
              onClick={() => {
                setFilter('unfinished');
                setPage(1);
              }}
            >
              Offen
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-10">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
            {error}
          </div>
        ) : members && members.items.length > 0 ? (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-border text-xs uppercase text-text-muted">
                  <tr>
                    <th className="px-3 py-3 font-medium">User</th>
                    <th className="px-3 py-3 font-medium">Status</th>
                    <th className="px-3 py-3 font-medium">VIP</th>
                    <th className="px-3 py-3 font-medium">Registriert</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {members.items.map((member) => (
                    <tr key={member.id} className="text-text-primary">
                      <td className="px-3 py-3 font-semibold">{member.username}</td>
                      <td className="px-3 py-3">
                        <span
                          className={
                            member.isOfficial
                              ? 'rounded-full bg-success/15 px-2.5 py-1 text-xs font-semibold text-success'
                              : 'rounded-full bg-warning/15 px-2.5 py-1 text-xs font-semibold text-warning'
                          }
                        >
                          {member.isOfficial ? 'Valid' : 'Offen'}
                        </span>
                      </td>
                      <td className="px-3 py-3 font-mono text-kairox-pink">VIP{member.vipLevel}</td>
                      <td className="px-3 py-3 text-text-muted">
                        {dateFormatter.format(new Date(member.createdAt))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border pt-4 text-sm text-text-muted sm:flex-row sm:items-center sm:justify-between">
              <span>
                {members.total} Einträge · Seite {members.page} / {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                >
                  {t('common.back')}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  {t('common.next')}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-bg-tertiary p-5 text-sm text-text-muted">
            {t('team.noMembers')}
          </div>
        )}
      </Card>
    </AppShell>
  );
}
