import logging
import sys

from enum import Enum

LOGGER = logging.getLogger("qgis-plugin-ci")


class LogLevel(Enum):
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    NOTICE = logging.CRITICAL + 1


FORMATSTR = "[%(levelname)s] %(message)s"


def setup(log_level: LogLevel = LogLevel.WARNING):
    """Initialize log handler"""
    logging.addLevelName(LogLevel.NOTICE.value, LogLevel.NOTICE.name)

    formatter = logging.Formatter(FORMATSTR)
    channel = logging.StreamHandler(sys.stderr)
    channel.setFormatter(formatter)

    LOGGER.addHandler(channel)
    LOGGER.setLevel(log_level.value)


def logger():
    return LOGGER


#
# Shortcuts
#
warning = LOGGER.warning
info = LOGGER.info
error = LOGGER.error
critical = LOGGER.critical
debug = LOGGER.debug


def notice(msg: str, *args, **kwargs):
    LOGGER.log(LogLevel.NOTICE.value, msg, *args, **kwargs)


def is_enabled_for(level: LogLevel) -> bool:
    return LOGGER.isEnabledFor(level.value)


def log_level() -> LogLevel:
    return LogLevel(LOGGER.level)
