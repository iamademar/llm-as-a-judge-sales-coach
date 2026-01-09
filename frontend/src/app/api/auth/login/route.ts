/**
 * Login API Route
 *
 * POST /api/auth/login
 * - Forwards credentials to backend API
 * - On success: returns access_token JSON and sets httpOnly refresh_token cookie
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
    // Parse request body
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Forward login request to backend
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        errorData,
        { status: response.status }
      );
    }

    // Parse response from backend
    const data = await response.json();
    const { access_token, refresh_token, token_type } = data;

    // Create response with access token
    const nextResponse = NextResponse.json({
      access_token,
      token_type,
    });

    // Set httpOnly refresh token cookie
    nextResponse.cookies.set('refresh_token', refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    return nextResponse;
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
