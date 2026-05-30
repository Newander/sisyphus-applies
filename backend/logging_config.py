import logging
from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    normalized_level = level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": normalized_level,
            },
            "loggers": {
                "backend": {
                    "handlers": ["console"],
                    "level": normalized_level,
                    "propagate": False,
                },
                "uvicorn": {
                    "level": normalized_level,
                },
                "uvicorn.access": {
                    "level": normalized_level,
                },
            },
        }
    )
    logging.getLogger(__name__).info("Logging configured", extra={"level": normalized_level})
