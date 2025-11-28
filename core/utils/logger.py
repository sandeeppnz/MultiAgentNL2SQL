import logging
from typing import Optional


_DEFAULT_LEVEL = logging.INFO


def _configure_root_handler() -> None:
    """
    Configure a basic stream handler once.

    Checking for existing handlers keeps the function idempotent so
    repeated imports do not duplicate log output.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(_DEFAULT_LEVEL)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger with sane defaults for the project.

    Parameters
    ----------
    name : Optional[str]
        The logger namespace.  Falls back to the root logger when omitted.
    """
    _configure_root_handler()
    return logging.getLogger(name)

