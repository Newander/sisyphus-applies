import logging

from backend.config import get_settings
from backend.logging_config import configure_logging
from backend.services.gmail import connect_gmail

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Gmail connect command started")
    email_address = connect_gmail()
    logger.info("Gmail connect command finished email_address=%s", email_address)
    print(f"Gmail connected: {email_address}")
