export function AdminPageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-kairox-pink/90">
        Kairox Admin
      </p>
      <h1 className="mt-1 text-2xl font-bold text-white">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-text-muted">{subtitle}</p>}
      <div
        className="mt-4 h-0.5 w-14 rounded-full bg-gradient-to-r from-kairox-pink to-kairox-pink-dark"
        aria-hidden
      />
    </header>
  );
}
