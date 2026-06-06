'use client';

import { BottomNav } from '@/components/ui/BottomNav';
import { FloatingServiceBot } from '@/components/brand/FloatingServiceBot';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { MobileHeader } from '@/components/layout/MobileHeader';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <AppSidebar />

      <div className="flex min-h-screen flex-1 flex-col">
        <MobileHeader />
        <main className="flex-1 overflow-auto px-4 py-5 pb-[5.5rem] lg:px-8 lg:pb-8">
          {children}
        </main>
        <BottomNav />
        <FloatingServiceBot />
      </div>
    </div>
  );
}
