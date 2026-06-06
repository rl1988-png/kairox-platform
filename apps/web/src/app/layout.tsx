import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { AuthProvider } from '@/hooks/useAuth';
import { ServiceWorkerRegister } from '@/components/pwa/ServiceWorkerRegister';
import { ToastProvider } from '@/components/ui/Toast';
import { I18nProvider } from '@/lib/i18n';
import './globals.css';

const inter = Inter({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Kairox AI',
  description: 'Kairox AI — Trading & Wallet Platform',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    title: 'Kairox AI',
  },
};

export const viewport: Viewport = {
  themeColor: '#0b1220',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={inter.variable}>
      <body className={`${inter.className} font-sans`}>
        <I18nProvider>
          <ToastProvider>
            <AuthProvider>
              <ServiceWorkerRegister />
              {children}
            </AuthProvider>
          </ToastProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
