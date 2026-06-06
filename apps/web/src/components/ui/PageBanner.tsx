import type { ReactNode } from 'react';

type PageBannerProps = {
  title: string;
  subtitle?: string;
  accent?: string;
  children?: ReactNode;
};

export function PageBanner({ title, subtitle, accent, children }: PageBannerProps) {
  return (
    <section className="kairox-card-glow mb-6 overflow-hidden p-0">
      <div
        className="relative bg-cover bg-center px-5 py-7"
        style={{ backgroundImage: "url('/assets/kairox/login-bg.jpg')" }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-overlay/95 via-overlay/70 to-overlay/30" />
        <div className="relative">
          {accent && <p className="text-sm font-medium text-kairox-pink">{accent}</p>}
          <h1 className="text-xl font-bold text-white sm:text-2xl">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-text-muted">{subtitle}</p>}
          {children}
        </div>
      </div>
    </section>
  );
}
