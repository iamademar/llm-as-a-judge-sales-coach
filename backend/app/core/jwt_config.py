"""
JWT configuration with timedelta objects.
"""
from datetime import timedelta

from app.core.config import settings


class JWTSettings:
    """
    JWT configuration settings with timedelta objects for expiration times.
    """

    def __init__(self):
        self.secret: str = settings.JWT_SECRET
        self.algorithm: str = settings.JWT_ALGORITHM
        self.access_token_expires: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_token_expires: timedelta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )


# Global JWT settings instance
jwt_settings = JWTSettings()
