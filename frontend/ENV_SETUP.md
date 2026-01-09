# Environment Variables Setup

This document describes the optional environment variables for the frontend application.

## Optional Variables

The frontend application works with sensible defaults. To customize, create a `.env.local` file in the frontend directory:

```bash
# Backend API Configuration (optional)
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Variable Details

### `NEXT_PUBLIC_API_BASE`
- **Description**: Base URL for the backend API
- **Default**: `http://localhost:8000`
- **Required**: No (defaults to localhost:8000)
- **Usage**: Used by all API client functions in `src/lib/api.ts`

## Authentication

The application uses **JWT (JSON Web Token) authentication** for all API requests:

- Users must sign in to access protected features
- Authentication is handled automatically via the `AuthContext`
- Access tokens are included in API requests via the `Authorization` header
- No API key configuration is required in the frontend

### Protected Features
- Uploading and analyzing transcripts
- Creating and managing representatives
- Viewing assessment data
- All data operations

## Setup Instructions

1. **Optional**: Create `.env.local` in the `frontend/` directory if you need to customize the API URL
2. **Required**: Ensure the backend is running and accessible at the configured URL
3. Start the development server: `pnpm run dev`
4. Sign in using valid credentials to access protected features

## Security Notes

- Never commit `.env.local` to version control
- The `.env.local` file is already in `.gitignore`
- Only use `NEXT_PUBLIC_*` prefix for variables that need to be exposed to the browser
- JWT tokens are stored securely and managed by the authentication system
- Access tokens expire automatically and can be refreshed via refresh tokens

