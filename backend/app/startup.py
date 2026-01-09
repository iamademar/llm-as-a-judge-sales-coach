"""
Startup tasks for the FastAPI application.

Handles database migrations and demo data seeding on application startup.
"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def run_startup_tasks():
    """
    Run all startup tasks.

    1. Always runs migrations (idempotent)
    2. Seeds demo data if AUTO_SEED environment variable is set to "true"
    
    Skips migrations during testing (when TESTING=true environment variable is set).
    """
    # Skip migrations during testing
    if os.getenv("TESTING") == "true":
        logger.info("TESTING mode detected, skipping migrations and seeding")
        return
    
    # Always run migrations (idempotent)
    logger.info("Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        raise

    # Demo-only seeding
    if os.getenv("AUTO_SEED") == "true":
        logger.info("AUTO_SEED is enabled, seeding demo data...")
        from app.seed import seed_demo_data
        seed_demo_data()
        logger.info("Demo data seeding completed")
    else:
        logger.info("AUTO_SEED not enabled, skipping demo data seeding")
