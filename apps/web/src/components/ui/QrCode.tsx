'use client';

import QRCode from 'react-qr-code';

type QrCodeProps = {
  value: string;
  size?: number;
  label?: string;
  className?: string;
};

export function QrCode({ value, size = 200, label, className = '' }: QrCodeProps) {
  if (!value.trim()) {
    return null;
  }

  return (
    <div className={`inline-flex flex-col items-center gap-2 ${className}`}>
      <div
        className="rounded-lg border border-border bg-white p-3"
        role="img"
        aria-label={label ?? 'QR code'}
      >
        <QRCode value={value} size={size} level="M" />
      </div>
      {label ? <p className="text-xs text-text-muted">{label}</p> : null}
    </div>
  );
}
