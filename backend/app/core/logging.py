import json
import logging
from pathlib import Path
from typing import Any


def configure_logging(
    *,
    log_level: str = "INFO",
    log_file_path: str | None = None,
) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not any(
        isinstance(handler, logging.StreamHandler) and getattr(handler, "_wanderlust_handler", False)
        for handler in root_logger.handlers
    ):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(message)s"))
        stream_handler._wanderlust_handler = True  # type: ignore[attr-defined]
        root_logger.addHandler(stream_handler)

    if log_file_path and not any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None) == str(Path(log_file_path).resolve())
        for handler in root_logger.handlers
    ):
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: str,
    event: str,
    **fields: Any,
) -> None:
    payload = {
        "event": event,
        **fields,
    }
    getattr(logger, level)(json.dumps(payload, default=str))
