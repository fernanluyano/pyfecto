from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from .pyio import PYIO
from .runtime import Runtime

E = TypeVar("E", bound=Exception)


class PyfectoApp(Generic[E], ABC):
    """
    Base class for creating Pyfecto applications with a standardized structure.

    PyfectoApp follows a functional effect pattern by separating the description
    of what an application does (the effect) from the execution of that effect.
    This approach enables better testing, composition, and error handling.

    Type Variables:
        E: The error type this application may produce (must be an Exception type)

    Usage:
        class MyApp(PyfectoApp[ValueError, str]):
            def run(self) -> PYIO[ValueError, None]:
                PYIO.attempt(...)

        # Create and run the application
        app = MyApp()
        Runtime.run_app(app)
    """

    def __init__(self, runtime: Optional[Runtime] = None):
        """
        Initialize a Pyfecto application with an optional runtime configuration.

        If no runtime is provided, a default Runtime instance will be created.
        Custom runtime configurations can be provided to customize logging,
        error handling, and other environment-specific concerns.

        Args:
            runtime: An optional Runtime instance for configuring the execution
                    environment. If None, a default Runtime will be used.
        """
        if not runtime:
            self._runtime = Runtime()
        else:
            self._runtime = runtime

    @abstractmethod
    def run(self) -> PYIO[E, None]:
        """
        Define the main logic of the application as a PYIO effect.

        This abstract method must be implemented by concrete application classes.
        It should return a PYIO effect that describes what the application does
        without actually executing any side effects. The effect will only be
        executed when the Runtime's run_app method is called.

        Returns:
            A PYIO effect representing the application's main logic, with
            error type E or None on success.

        Example:
            def run(self) -> PYIO[Exception, int]:
                return (
                    PYIO.log_info("Starting calculation")
                    .then(self._load_data())
                    .flat_map(lambda data: self._process_data(data))
                )
        """
        pass
