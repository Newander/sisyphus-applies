import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from backend.config import get_settings

logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    root_dir = Path(__file__).resolve().parent.parent
    config = Config(str(root_dir / "alembic.ini"))
    config.set_main_option("script_location", str(root_dir / "migrations"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    return config


def upgrade_database() -> None:
    logger.info("Running database migrations")
    command.upgrade(get_alembic_config(), "heads")
    logger.info("Database migrations complete")
