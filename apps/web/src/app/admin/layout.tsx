'use client';

import { useRequireStaff } from '@/hooks/useRequireStaff';
import { AdminShell } from '@/components/admin/AdminShell';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { loading, isStaff } = useRequireStaff();

  if (loading || !isStaff) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kairox-pink border-t-transparent" />
      </div>
    );
  }

  return <AdminShell>{children}</AdminShell>;
}
