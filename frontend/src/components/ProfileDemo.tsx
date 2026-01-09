'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/auth/AuthContext';
import { apiFetch, API_BASE } from '@/lib/api';

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

export default function ProfileDemo() {
  const router = useRouter();
  const { accessToken, isAuthenticated, refresh, logout } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchProfile();
  }, [isAuthenticated]);

  const fetchProfile = async (retried = false) => {
    if (!accessToken) {
      setLoading(false);
      return;
    }

    try {
      const response = await apiFetch(
        `${API_BASE}/auth/me`,
        { method: 'GET' },
        accessToken
      );

      // Handle 401: try to refresh token
      if (response.status === 401 && !retried) {
        const refreshed = await refresh();
        if (refreshed) {
          // Retry the request after successful refresh
          return fetchProfile(true);
        } else {
          // Refresh failed, redirect to login
          router.push('/login');
          return;
        }
      }

      if (!response.ok) {
        setError('Failed to load profile');
        setLoading(false);
        return;
      }

      const data = await response.json();
      setProfile(data);
      setError('');
      setLoading(false);
    } catch (err) {
      setError('Network error');
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <p className="text-gray-600 dark:text-gray-400">Loading profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-900/20">
        <p className="text-red-800 dark:text-red-400">{error}</p>
        <button
          onClick={() => fetchProfile()}
          className="mt-2 text-sm text-red-600 hover:text-red-500 dark:text-red-400"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Your Profile
        </h2>
        <button
          onClick={handleLogout}
          className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-500 dark:bg-red-500 dark:hover:bg-red-400"
        >
          Logout
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Email
          </p>
          <p className="text-gray-900 dark:text-white">{profile.email}</p>
        </div>

        {profile.full_name && (
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Full Name
            </p>
            <p className="text-gray-900 dark:text-white">{profile.full_name}</p>
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            User ID
          </p>
          <p className="font-mono text-sm text-gray-900 dark:text-white">
            {profile.id}
          </p>
        </div>

        <div className="flex gap-4">
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Status
            </p>
            <p className="text-gray-900 dark:text-white">
              {profile.is_active ? (
                <span className="text-green-600 dark:text-green-400">Active</span>
              ) : (
                <span className="text-red-600 dark:text-red-400">Inactive</span>
              )}
            </p>
          </div>

          {profile.is_superuser && (
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Role
              </p>
              <p className="text-blue-600 dark:text-blue-400">Superuser</p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 rounded-md bg-green-50 p-4 dark:bg-green-900/20">
        <p className="text-sm text-green-800 dark:text-green-400">
          Authentication working! This data was fetched from{' '}
          <code className="font-mono">/auth/me</code> using your JWT access token.
        </p>
      </div>
    </div>
  );
}
