import clsx from 'clsx';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'pink';

const styles: Record<BadgeVariant, string> = {
  default: 'bg-bg-tertiary text-text-muted',
  success: 'bg-success/20 text-success',
  warning: 'bg-warning/20 text-warning',
  danger: 'bg-danger/20 text-danger',
  pink: 'bg-kairox-pink/20 text-kairox-pink',
};

export function Badge({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?: BadgeVariant;
}) {
  return (
    <span className={clsx('inline-block rounded px-2 py-0.5 text-xs font-medium', styles[variant])}>
      {children}
    </span>
  );
}
