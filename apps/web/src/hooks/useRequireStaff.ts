'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

const STAFF_ROLES = new Set(['admin', 'support']);

export function useRequireStaff() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push('/login');
      return;
    }
    if (!STAFF_ROLES.has(user.role)) {
      router.push('/dashboard');
    }
  }, [user, loading, router]);

  const isStaff = user ? STAFF_ROLES.has(user.role) : false;
  return { user, loading, isStaff };
}
