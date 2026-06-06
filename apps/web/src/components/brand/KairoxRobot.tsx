'use client';

import Image from 'next/image';
import clsx from 'clsx';

type KairoxRobotProps = {
  size?: number;
  className?: string;
  floating?: boolean;
  priority?: boolean;
};

export function KairoxRobot({
  size = 120,
  className,
  floating = true,
  priority = false,
}: KairoxRobotProps) {
  return (
    <div
      className={clsx(
        'relative inline-flex items-center justify-center',
        floating && 'animate-kairox-float',
        className,
      )}
    >
      <div
        className="absolute inset-0 rounded-full bg-kairox-pink/20 blur-2xl"
        aria-hidden
      />
      <Image
        src="/assets/kairox/service.png"
        alt="Kairox AI Assistant"
        width={size}
        height={size}
        priority={priority}
        className="relative z-10 drop-shadow-[0_8px_24px_rgba(252,129,185,0.35)]"
      />
    </div>
  );
}
