/**
 * Refresh Token API Route
 *
 * POST /api/auth/refresh
 * - Reads refresh_token from httpOnly cookie
 * - Calls backend /auth/refresh endpoint
 * - Rotates refresh token cookie
 * - Returns new access_token
 */
import { NextRequest, NextResponse } from 'next/server';

// Use internal API base for server-side calls (Docker service name)
// Fallback to NEXT_PUBLIC_API_BASE so builds that only set the public var still work
const API_BASE =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Read refresh token from httpOnly cookie
    const refreshToken = request.cookies.get('refresh_token')?.value;

    if (!refreshToken) {
      return NextResponse.json(
        { error: 'No refresh token found' },
        { status: 401 }
      );
    }

    // Call backend refresh endpoint
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      const errorData = await response.json();

      // If refresh token is invalid/expired, clear the cookie
      if (response.status === 401) {
        const nextResponse = NextResponse.json(
          errorData,
          { status: 401 }
        );
        nextResponse.cookies.delete('refresh_token');
        return nextResponse;
      }

      return NextResponse.json(
        errorData,
        { status: response.status }
      );
    }

    // Parse response from backend
    const data = await response.json();
    const { access_token, refresh_token, token_type } = data;

    // Create response with new access token
    const nextResponse = NextResponse.json({
      access_token,
      token_type,
    });

    // Rotate refresh token cookie with new token
    nextResponse.cookies.set('refresh_token', refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    return nextResponse;
  } catch (error) {
    console.error('Refresh token error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
