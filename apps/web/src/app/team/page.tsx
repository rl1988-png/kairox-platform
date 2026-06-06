'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { ApiError, apiRequest } from '@/lib/api/client';
import { teamSubNav } from '@/lib/navigation';

interface TeamData {
  id: string;
  name: string;
  member_count: number;
  invite_code: string;
}

export default function TeamPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [team, setTeam] = useState<TeamData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    apiRequest<TeamData | null>('/api/v1/team')
      .then((data) => {
        if (mounted) setTeam(data);
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof ApiError ? err.message : 'Team konnte nicht geladen werden');
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [user]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell>
      <PageBanner title="Team" subtitle="Referrals & Provisionen L1-L3" accent={user.username} />

      <SubNavTabs tabs={teamSubNav} />
      <Card title="Dein Team" className="max-w-md">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
          </div>
        ) : error ? (
          <p className="text-sm text-danger">{error}</p>
        ) : team ? (
          <div className="space-y-4">
            <div>
              <p className="text-xl font-semibold text-white">{team.name}</p>
              <p className="text-sm text-text-muted">{team.member_count} Mitglieder</p>
            </div>
            <div className="invite-code-box">
              <p className="text-xs uppercase tracking-wider text-text-muted">Einladungscode</p>
              <p className="mt-2 font-mono text-2xl font-bold text-kairox-pink">
                {team.invite_code}
              </p>
            </div>
            <Link href="/account/invite" className="inline-block text-sm text-link hover:underline">
              QR-Code & teilen
            </Link>
          </div>
        ) : (
          <p className="text-sm leading-relaxed text-text-muted">
            Du bist noch keinem Team beigetreten. Nutze einen Einladungscode bei der Registrierung.
          </p>
        )}
      </Card>
    </AppShell>
  );
}
