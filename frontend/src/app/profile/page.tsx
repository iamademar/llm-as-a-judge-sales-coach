'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth/AuthContext';
import { AuthLoadingSpinner } from '@/components/AuthLoading';
import { Sidebar } from "@/components/ui/navigation/Sidebar";
import ProfileDemo from '@/components/ProfileDemo';

export default function ProfilePage() {
  const { isAuthenticated, isLoading, refresh } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      refresh();
    }
  }, [isLoading, isAuthenticated, refresh]);

  if (isLoading) {
    return <AuthLoadingSpinner />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <Sidebar />
      <main className="lg:pl-72">
        <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
          <ProfileDemo />
        </div>
      </main>
    </>
  );
}
