import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from backend.config import get_settings
from backend.logging_config import configure_logging
from backend.migrations import upgrade_database
from backend.services.ssh_sync import make_sync_config, sync_documents

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def heartbeat() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Worker heartbeat storage_dir=%s", settings.storage_dir)


def ssh_sync_job() -> None:
    config = make_sync_config(settings)
    if config is None:
        return
    sync_documents(settings.storage_dir, config)


def main() -> None:
    upgrade_database()
    configure_logging(settings.log_level)  # alembic's fileConfig resets root to WARNING
    logger.info("Worker starting")
    scheduler = BlockingScheduler(timezone="Europe/Warsaw")
    scheduler.add_job(heartbeat, "interval", minutes=5, id="heartbeat", replace_existing=True)
    if settings.ssh_sync_configured:
        scheduler.add_job(
            ssh_sync_job,
            "interval",
            seconds=settings.ssh_sync_interval_seconds,
            id="ssh_sync",
            replace_existing=True,
        )
        logger.info(
            "SSH sync scheduled interval_seconds=%s host=%s",
            settings.ssh_sync_interval_seconds,
            settings.ssh_sync_host,
        )
    heartbeat()
    ssh_sync_job()
    logger.info("Worker scheduler started")
    scheduler.start()


if __name__ == "__main__":
    main()
