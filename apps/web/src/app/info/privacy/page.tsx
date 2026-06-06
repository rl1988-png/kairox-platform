'use client';

import Link from 'next/link';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function PrivacyPage() {
  return (
    <AuthLayout showRobot={false}>
      <div className="mx-auto max-w-md">
        <h1 className="text-xl font-bold text-kairox-pink">Privacy Policy</h1>
        <div className="mt-4 space-y-3 text-sm leading-relaxed text-text-muted">
          <p>
            Kairox AI verarbeitet Kontodaten (Username, E-Mail), Wallet-Transaktionen und
            Sitzungsinformationen ausschließlich zum Betrieb der Plattform.
          </p>
          <p>
            Zahlungsdaten (TRC20-Adressen, TX-Hashes) werden für On-Chain-Verifizierung
            gespeichert. Passwörter werden gehasht — niemals im Klartext.
          </p>
          <p>
            Admin-Aktionen werden im Audit-Log protokolliert. API-Anfragen können rate-limitiert
            und zu Sicherheitszwecken geloggt werden.
          </p>
          <p className="text-xs text-text-muted/80">
            Platzhalter — rechtlicher Text vor Production durch Legal ersetzen.
          </p>
        </div>
        <Link href="/login" className="mt-8 inline-block text-sm text-kairox-pink hover:underline">
          ← Back to login
        </Link>
      </div>
    </AuthLayout>
  );
}
