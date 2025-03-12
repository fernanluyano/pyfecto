import sys
from typing import (TYPE_CHECKING, Any, Callable, Dict, List, Optional,
                    TypeVar, Union)

from loguru import logger as loguru_logger

# Import PyfectoApp only for type checking
if TYPE_CHECKING:
    from .app import PyfectoApp

LOGGER = loguru_logger
E = TypeVar("E", bound=Exception)


class Runtime:
    """
    Runtime environment for executing Pyfecto applications.

    The Runtime is responsible for managing the execution environment for Pyfecto
    applications, including logging configuration, error handling, and effect execution.
    It follows the Singleton pattern to ensure a single runtime instance per application.

    The Runtime separates environmental concerns from application logic, following the
    functional effect pattern of separating what to do (defined in PyfectoApp) from
    how to do it (handled by Runtime).

    Features:
        - Singleton instance management
        - Configurable logging with multiple sinks
        - Support for span timing
        - Application execution with error handling
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """
        Ensure only one Runtime instance exists per application (Singleton pattern).

        This method implements the Singleton pattern to ensure that only one Runtime
        instance exists, providing a consistent execution environment across the application.

        Returns:
            Runtime: The singleton Runtime instance
        """
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

        This method configures the logging system with the specified settings.
        If the Runtime instance has already been initialized, this method
        will return without making changes to preserve the existing configuration.

        Args:
            log_level: Default minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Custom log format string (if None, a default format is used)
            sinks: List of sinks to add (if None, a default stderr sink is added)
                Each sink can be either:
                - A callable function that accepts a message string
                - A dict with parameters to pass to logger.add() (must include 'sink')

        Example:
            # Custom runtime with file logging
            runtime = Runtime(
                log_level="DEBUG",
                sinks=[
                    {"sink": sys.stderr, "level": "INFO"},
                    {"sink": "app.log", "rotation": "10 MB", "level": "DEBUG"}
                ]
            )
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
        """
        Configure the logger with provided sinks or default configuration.

        This internal method sets up the Loguru logger with the specified format
        and sinks. If no format is provided, a default format is used that includes
        timestamp, log level, message, and any extra context. If no sinks are provided,
        a default stderr sink is configured.

        Args:
            log_format: Format string for log messages
            sinks: List of sink configurations or callable sinks
        """

        def configure_sinks():
            """Configure multiple sinks with appropriate settings."""
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
            configure_sinks()

    @staticmethod
    def run_app(
        app: "PyfectoApp[E]", exit_on_error: bool = True, error_code: int = 1
    ) -> None:
        """
        Execute a PyfectoApp with the runtime environment.

        This method is the main entry point for running Pyfecto applications.
        It takes a PyfectoApp instance, runs its effect, and handles the result
        appropriately, including logging errors and optionally exiting the
        process in case of failure.

        Args:
            app: The PyfectoApp instance to run
            exit_on_error: If True, will exit the process when an error occurs
            error_code: Exit code to use when exiting on error

        Returns:
            None
        """
        result = app.run().run()
        if isinstance(result, Exception):
            LOGGER.error(f"Application failed: {result}")
            if exit_on_error:
                sys.exit(error_code)
            else:
                raise result
        else:
            LOGGER.info("Application completed successfully")
