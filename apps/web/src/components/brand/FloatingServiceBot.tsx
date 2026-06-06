'use client';

import { useRef, useState } from 'react';
import Image from 'next/image';
import { KairoxRobot } from '@/components/brand/KairoxRobot';
import { Modal } from '@/components/ui/Modal';

export function FloatingServiceBot() {
  const [open, setOpen] = useState(false);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const drag = useRef<{ sx: number; sy: number; ox: number; oy: number } | null>(null);
  const moved = useRef(false);

  const onPointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    drag.current = { sx: e.clientX, sy: e.clientY, ox: offset.x, oy: offset.y };
    moved.current = false;
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.sx;
    const dy = e.clientY - drag.current.sy;
    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved.current = true;
    setOffset({ x: drag.current.ox + dx, y: drag.current.oy + dy });
  };

  const onPointerUp = () => {
    if (!moved.current) setOpen(true);
    drag.current = null;
  };

  return (
    <>
      <button
        type="button"
        aria-label="Kairox AI Assistant"
        className="fixed bottom-[5.5rem] right-4 z-50 touch-none md:bottom-[5.5rem] md:right-8"
        style={{ transform: `translate(${offset.x}px, ${offset.y}px)` }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <span className="relative block animate-kairox-float">
          <span className="absolute inset-0 rounded-full bg-kairox-pink/30 blur-xl" aria-hidden />
          <Image
            src="/assets/kairox/service.png"
            alt=""
            width={72}
            height={72}
            draggable={false}
            className="relative select-none drop-shadow-[0_6px_20px_rgba(252,129,185,0.45)]"
          />
        </span>
      </button>

      <Modal open={open} onClose={() => setOpen(false)} title="Kairox AI Assistant">
        <div className="flex flex-col items-center gap-4 text-center">
          <KairoxRobot size={100} floating />
          <p className="text-sm leading-relaxed text-text-muted">
            Willkommen bei Kairox AI. Unser intelligenter Service-Bot begleitet dich durch Trading,
            Einzahlungen und Team-Features — genau wie auf kairox.cc.
          </p>
          <p className="text-xs text-kairox-pink">24/7 Support · Sicher · On-Chain</p>
        </div>
      </Modal>
    </>
  );
}
