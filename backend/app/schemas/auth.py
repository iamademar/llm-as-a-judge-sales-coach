"""
Authentication schemas for JWT token handling.

Pydantic models for login, token responses, and refresh operations.
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Schema for login requests.

    Used when users authenticate with email and password.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenPair(BaseModel):
    """
    Schema for JWT token pair response.

    Contains both access and refresh tokens issued upon successful authentication.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')"
    )


class RefreshRequest(BaseModel):
    """
    Schema for token refresh requests.

    Used to exchange a refresh token for a new access token.
    """

    refresh_token: str = Field(..., description="JWT refresh token")
