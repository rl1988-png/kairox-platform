interface StatItem {
  label: string;
  value: string;
}

export function StatGrid({ items }: { items: StatItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="kairox-card p-4">
          <p className="text-xs text-text-muted">{item.label}</p>
          <p className="mt-1 font-mono text-lg font-semibold text-kairox-pink">{item.value}</p>
        </div>
      ))}
    </div>
  );
}
