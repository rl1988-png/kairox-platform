import clsx from 'clsx';

type IconProps = { className?: string; active?: boolean };

const base = 'h-6 w-6';

export function NavHomeIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <path
        d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        fill={active ? 'currentColor' : 'none'}
        opacity={active ? 0.15 : 1}
      />
    </svg>
  );
}

export function NavTradeIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <path
        d="M4 18V6l8-3 8 3v12l-8 3-8-3Z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path d="M12 3v18M4 6l8 3 8-3M4 12l8 3 8-3" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

export function NavWalletIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <rect x="3" y="6" width="18" height="14" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M3 10h18" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="17" cy="14" r="1.2" fill="currentColor" />
    </svg>
  );
}

export function NavTeamIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <circle cx="9" cy="9" r="3" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="17" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M4 19c0-2.8 2.2-5 5-5s5 2.2 5 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path d="M14 19c.3-1.8 1.6-3 3.5-3 1.2 0 2.2.5 3 1.4" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

export function NavAccountIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M5 20c0-3.9 3.1-7 7-7s7 3.1 7 7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function NavRechargeIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <path
        d="M12 3v18M5 10l7-7 7 7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect
        x="4"
        y="14"
        width="16"
        height="7"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.6"
        fill={active ? 'currentColor' : 'none'}
        opacity={active ? 0.12 : 1}
      />
    </svg>
  );
}

export function NavWithdrawIcon({ className, active }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={clsx(base, className)} aria-hidden>
      <path
        d="M12 21V3M5 14l7 7 7-7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect
        x="4"
        y="3"
        width="16"
        height="7"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.6"
        fill={active ? 'currentColor' : 'none'}
        opacity={active ? 0.12 : 1}
      />
    </svg>
  );
}
