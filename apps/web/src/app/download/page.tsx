'use client';

import Link from 'next/link';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { KairoxRobot } from '@/components/brand/KairoxRobot';

export default function DownloadPage() {
  return (
    <AuthLayout showRobot={false}>
      <div className="mx-auto max-w-md text-center">
        <KairoxRobot size={90} />
        <h1 className="mt-4 text-xl font-bold text-white">Download APP</h1>
        <p className="mt-3 text-sm leading-relaxed text-text-muted">
          Kairox AI läuft als Progressive Web App. Öffne die Seite im Browser und wähle
          „Zum Home-Bildschirm hinzufügen“ (iOS) bzw. „App installieren“ (Android/Chrome).
        </p>
        <ol className="mt-6 space-y-2 text-left text-sm text-text-muted">
          <li>1. Einloggen unter /login</li>
          <li>2. Browser-Menü → Installieren / Add to Home Screen</li>
          <li>3. App-Icon auf dem Startbildschirm nutzen</li>
        </ol>
        <Link href="/login" className="kairox-btn-pill mt-8 inline-block text-center">
          Zum Login
        </Link>
      </div>
    </AuthLayout>
  );
}
