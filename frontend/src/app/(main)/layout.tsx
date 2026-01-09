'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth/AuthContext';
import { Sidebar } from "@/components/ui/navigation/Sidebar";
import { AuthLoadingSpinner } from '@/components/AuthLoading';

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const { isAuthenticated, isLoading, refresh } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Try to refresh token on mount if needed
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
        <div className="relative">
          <div className="p-4 sm:px-6 sm:pb-10 sm:pt-10 lg:px-10 lg:pt-7">
            {children}
          </div>
        </div>
      </main>
    </>
  )
}
