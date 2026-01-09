'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_BASE } from '@/lib/api';

type Organization = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

type RegistrationMode = 'create' | 'join';

export default function RegisterPage() {
  const router = useRouter();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [mode, setMode] = useState<RegistrationMode>('create');
  const [organizationName, setOrganizationName] = useState('');
  const [selectedOrgId, setSelectedOrgId] = useState('');

  // UI state
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(false);

  // Fetch organizations for "join" mode
  useEffect(() => {
    if (mode === 'join') {
      setLoadingOrgs(true);
      fetch(`${API_BASE}/auth/organizations`)
        .then((res) => res.json())
        .then((data) => {
          setOrganizations(data);
          if (data.length > 0) setSelectedOrgId(data[0].id);
        })
        .catch(() => setError('Failed to load organizations'))
        .finally(() => setLoadingOrgs(false));
    }
  }, [mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Prepare request body
    const body: any = {
      email,
      password,
      full_name: fullName || undefined,
    };

    if (mode === 'create') {
      if (!organizationName.trim()) {
        setError('Organization name is required');
        setLoading(false);
        return;
      }
      body.organization_name = organizationName.trim();
    } else {
      if (!selectedOrgId) {
        setError('Please select an organization');
        setLoading(false);
        return;
      }
      body.organization_id = selectedOrgId;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || 'Registration failed');
        setLoading(false);
        return;
      }

      // Registration successful, redirect to login
      router.push('/login');
    } catch (err) {
      setError('Network error. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
            >
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
              <p className="text-sm text-red-800 dark:text-red-400">{error}</p>
            </div>
          )}

          <div className="space-y-4 rounded-md shadow-sm">
            {/* Email */}
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="relative block w-full rounded-md border-0 px-3 py-2 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 dark:bg-gray-800 dark:text-white dark:ring-gray-700 sm:text-sm sm:leading-6"
                placeholder="Email address"
              />
            </div>

            {/* Full Name */}
            <div>
              <label htmlFor="full-name" className="sr-only">
                Full name
              </label>
              <input
                id="full-name"
                name="full-name"
                type="text"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="relative block w-full rounded-md border-0 px-3 py-2 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 dark:bg-gray-800 dark:text-white dark:ring-gray-700 sm:text-sm sm:leading-6"
                placeholder="Full name (optional)"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="relative block w-full rounded-md border-0 px-3 py-2 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-blue-600 dark:bg-gray-800 dark:text-white dark:ring-gray-700 sm:text-sm sm:leading-6"
                placeholder="Password (min 8 characters)"
              />
            </div>

            {/* Organization Mode Toggle */}
            <div className="border-t border-gray-300 dark:border-gray-700 pt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Organization
              </label>
              <div className="flex space-x-4 mb-4">
                <button
                  type="button"
                  onClick={() => setMode('create')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md ${
                    mode === 'create'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Create New
                </button>
                <button
                  type="button"
                  onClick={() => setMode('join')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md ${
                    mode === 'join'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Join Existing
                </button>
              </div>

              {/* Create Mode: Organization Name Input */}
              {mode === 'create' && (
                <input
                  type="text"
                  required
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  className="block w-full rounded-md border-0 px-3 py-2 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 dark:bg-gray-800 dark:text-white dark:ring-gray-700 sm:text-sm sm:leading-6"
                  placeholder="Your organization name"
                />
              )}

              {/* Join Mode: Organization Dropdown */}
              {mode === 'join' && (
                <div>
                  {loadingOrgs ? (
                    <p className="text-sm text-gray-500">Loading organizations...</p>
                  ) : organizations.length === 0 ? (
                    <p className="text-sm text-gray-500">No organizations available</p>
                  ) : (
                    <select
                      required
                      value={selectedOrgId}
                      onChange={(e) => setSelectedOrgId(e.target.value)}
                      className="block w-full rounded-md border-0 px-3 py-2 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-blue-600 dark:bg-gray-800 dark:text-white dark:ring-gray-700 sm:text-sm sm:leading-6"
                    >
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:bg-blue-400 dark:bg-blue-500 dark:hover:bg-blue-400"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
