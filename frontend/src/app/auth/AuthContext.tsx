'use client';

/**
 * Authentication Context
 *
 * Manages authentication state including:
 * - Access token (stored in non-httpOnly cookie for reload survival)
 * - User email
 * - Token refresh logic
 * - Login/logout functionality
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import Cookies from 'js-cookie';
import { apiFetch } from '@/lib/api';

/**
 * User data returned from /auth/me endpoint
 */
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  organization_id: string | null;
}

interface AuthContextType {
  accessToken: string | null;
  email: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, email: string) => void;
  refresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Cookie names
const ACCESS_TOKEN_COOKIE = 'access_token';
const EMAIL_COOKIE = 'user_email';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Fetch user data from /auth/me endpoint
   */
  const fetchUser = useCallback(async (token: string): Promise<User | null> => {
    try {
      const response = await apiFetch('/auth/me', {}, token);
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return userData;
      }
      return null;
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      return null;
    }
  }, []);

  /**
   * Hydrate state from cookies on mount
   * If no access token, try to refresh
   */
  useEffect(() => {
    const storedToken = Cookies.get(ACCESS_TOKEN_COOKIE);
    const storedEmail = Cookies.get(EMAIL_COOKIE);

    if (storedToken && storedEmail) {
      setAccessToken(storedToken);
      setEmail(storedEmail);
      // Fetch user data with the stored token
      fetchUser(storedToken).finally(() => setIsLoading(false));
    } else {
      // Try to refresh token if we don't have one
      refresh().finally(() => setIsLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Set authentication state and persist to cookies
   */
  const setAuth = (token: string, userEmail: string) => {
    setAccessToken(token);
    setEmail(userEmail);

    // Store in non-httpOnly cookies for client access and reload survival
    Cookies.set(ACCESS_TOKEN_COOKIE, token, {
      expires: 1 / 96, // 15 minutes (1/96 of a day)
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
    });

    Cookies.set(EMAIL_COOKIE, userEmail, {
      expires: 7, // 7 days
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
    });

    // Fetch full user data
    fetchUser(token);
  };

  /**
   * Refresh access token using refresh token from httpOnly cookie
   * Returns true if refresh succeeded, false otherwise
   */
  const refresh = async (): Promise<boolean> => {
    try {
      const response = await apiFetch('/api/auth/refresh', {
        method: 'POST',
      });

      if (!response.ok) {
        // Refresh failed - clear auth state
        clearAuth();
        return false;
      }

      const data = await response.json();
      const { access_token } = data;

      // Update access token (email stays the same)
      if (email) {
        setAuth(access_token, email);
      } else {
        // If we don't have email, just update the token
        setAccessToken(access_token);
        Cookies.set(ACCESS_TOKEN_COOKIE, access_token, {
          expires: 1 / 96,
          sameSite: 'lax',
          secure: process.env.NODE_ENV === 'production',
        });
      }

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      clearAuth();
      return false;
    }
  };

  /**
   * Clear authentication state and cookies
   */
  const clearAuth = () => {
    setAccessToken(null);
    setEmail(null);
    setUser(null);
    Cookies.remove(ACCESS_TOKEN_COOKIE);
    Cookies.remove(EMAIL_COOKIE);
  };

  /**
   * Logout user - calls backend and clears all auth state
   */
  const logout = async () => {
    try {
      // Call logout endpoint to clear httpOnly refresh token cookie
      await apiFetch('/api/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      // Always clear client-side auth state
      clearAuth();
    }
  };

  const value: AuthContextType = {
    accessToken,
    email,
    user,
    isAuthenticated: !!accessToken && !!email,
    setAuth,
    refresh,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 * Must be used within AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
