'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth/AuthContext';
import { siteConfig } from "@/app/siteConfig";
import { TabNavigation, TabNavigationLink } from "@/components/TabNavigation";
import { AuthLoadingSpinner } from '@/components/AuthLoading';
import { Sidebar } from "@/components/ui/navigation/Sidebar";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigationSettings = [
  { name: "General", href: siteConfig.baseLinks.settings.general },
  { name: "LLM Integrations", href: siteConfig.baseLinks.settings.integrations },
  { name: "Prompt Templates", href: siteConfig.baseLinks.settings.promptTemplates },
  { name: "Evaluations", href: siteConfig.baseLinks.settings.evaluations },
];

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const { isAuthenticated, isLoading, refresh } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

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
        <div className="p-4 sm:px-6 sm:pb-10 sm:pt-10 lg:px-10 lg:pt-7">
          <h1 className="text-lg font-semibold text-gray-900 sm:text-xl dark:text-gray-50">
            Settings
          </h1>
          <TabNavigation className="mt-4 sm:mt-6 lg:mt-10">
            {navigationSettings.map((item) => (
              <TabNavigationLink
                key={item.name}
                asChild
                active={pathname === item.href}
              >
                <Link href={item.href}>{item.name}</Link>
              </TabNavigationLink>
            ))}
          </TabNavigation>
          <div className="pt-6">{children}</div>
        </div>
      </main>
    </>
  );
}
