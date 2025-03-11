import sys
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger as loguru_logger


LOGGER = loguru_logger


class Runtime:
    """
    Simple runtime environment for Pyfecto applications.

    Provides logging configuration with support for spans timing and custom sinks.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Runtime, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        log_level: str = "INFO",
        log_format: Optional[str] = None,
        sinks: Optional[List[Union[Dict[str, Any], Callable]]] = None,
    ):
        """
        Initialize the runtime with configurable logging.

        Args:
            log_level: Default minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Custom log format string (if None, a default format is used)
            sinks: List of sinks to add (if None, a default stderr sink is added)
                Each sink can be either:
                - A callable function that accepts a message string
                - A dict with parameters to pass to logger.add() (must include 'sink')
        """
        if self._initialized:
            return
        self.log_level = log_level
        self._configure_logger(log_format, sinks)
        self.logger = loguru_logger
        self._initialized = True

        # Update the module-level logger variable
        global LOGGER
        LOGGER = loguru_logger

    def _configure_logger(
        self,
        log_format: Optional[str] = None,
        sinks: Optional[List[Union[Dict[str, Any], Callable]]] = None,
    ) -> None:
        """Configure the logger with provided sinks or default configuration."""
        loguru_logger.remove()

        if log_format is None:
            # Default format showing all bound context with {extra}
            log_format = (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message} {extra}"
            )
        elif "{extra}" not in log_format:
            # User provided a format but didn't include extra context, add it
            log_format += " {extra}"

        if not sinks:
            loguru_logger.add(sink=sys.stderr, format=log_format, level=self.log_level)
        else:
            for sink in sinks:
                if callable(sink):
                    loguru_logger.add(
                        sink=sink, format=log_format, level=self.log_level
                    )
                else:
                    sink_config = sink.copy()

                    if "format" not in sink_config:
                        sink_config["format"] = log_format
                    if "level" not in sink_config:
                        sink_config["level"] = self.log_level

                    loguru_logger.add(**sink_config)
