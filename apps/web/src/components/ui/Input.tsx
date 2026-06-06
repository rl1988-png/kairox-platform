import clsx from 'clsx';
import Image from 'next/image';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  iconSrc?: string;
}

export function Input({ label, error, className, id, iconSrc, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={inputId} className="block pl-3 text-base font-medium text-white">
          {label}
        </label>
      )}
      <div className="relative">
        {iconSrc && (
          <Image
            src={iconSrc}
            alt=""
            width={28}
            height={28}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 opacity-90"
          />
        )}
        <input
          id={inputId}
          className={clsx(
            'kairox-input',
            iconSrc && 'kairox-input-with-icon',
            error && 'border-danger ring-danger/30',
            className,
          )}
          {...props}
        />
      </div>
      {error && <p className="pl-3 text-xs text-danger">{error}</p>}
    </div>
  );
}