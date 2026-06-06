'use client';

import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { PageBanner } from '@/components/ui/PageBanner';
import { QrCode } from '@/components/ui/QrCode';
import { SubNavTabs } from '@/components/ui/SubNavTabs';
import { useToast } from '@/components/ui/Toast';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { accountSubNav } from '@/lib/navigation';

export default function AccountInvitePage() {
  const { user, loading } = useRequireAuth();
  const { toast } = useToast();
  const code = user?.inviteCode ?? '—';

  const copy = async () => {
    if (code === '—') return;
    await navigator.clipboard.writeText(code);
    toast('Invite-Code kopiert', 'success');
  };

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell>
      <PageBanner title="Invite" subtitle="Teile deinen Code mit Freunden" accent={user.username} />

      <SubNavTabs tabs={accountSubNav} />
      <Card title="Dein Invite-Code" className="max-w-md">
        <div className="invite-code-box">
          <p className="font-mono text-2xl font-bold text-kairox-pink">{code}</p>
        </div>
        {code !== '—' ? (
          <div className="mt-5 flex justify-center rounded-2xl bg-white p-4">
            <QrCode value={code} size={180} label="Invite-Code QR" />
          </div>
        ) : null}
        <Button variant="pill" className="mt-5 w-full" onClick={copy}>
          Code kopieren
        </Button>
      </Card>
    </AppShell>
  );
}
