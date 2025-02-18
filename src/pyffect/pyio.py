from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Any, Optional, Union

A = TypeVar('A')
B = TypeVar('B')
E = TypeVar('E', bound=Union[Exception, None])

@dataclass
class PYIO(Generic[E, A]):
    """
    Encapsulates operations that may either complete successfully with a value or encounter an error.
    Operations remain dormant until explicitly executed via run().

    Type Variables:
        E: Error type (must be None or inherit from Exception)
        A: Return type for successful operations
    """
    _compute: Callable[[], tuple[Optional[E], Optional[A]]]

    @staticmethod
    def success(value: A) -> 'PYIO[None, A]':
        """
        Wraps a value in a successful computation.
        Useful for lifting regular values into the PYIO context when you need to combine them with other PYIO operations.

        Args:
            value: The data to wrap in a successful computation
        """
        return PYIO(lambda: (None, value))

    @staticmethod
    def fail(error: Exception) -> 'PYIO[Exception, None]':
        """
        Creates a failed computation with the specified error. Useful for early returns and error cases where you want to
        short-circuit the rest of a computation chain.

        Args:
            error: The error that caused the failure
        """
        return PYIO(lambda: (error, None))

    @staticmethod
    def attempt(f: Callable[[], A]) -> 'PYIO[Exception, A]':
        """
        Converts a function that might throw into a safe PYIO computation.

        Provides a bridge between traditional try/except error handling and
        PYIO's error channel approach.

        Args:
            f: A function that could raise an exception
        """
        def safe_compute() -> tuple[Optional[Exception], Optional[A]]:
            try:
                return None, f()
            except Exception as e:
                return e, None

        return PYIO(safe_compute)

    @staticmethod
    def unit() -> 'PYIO[None, None]':
        """
        Creates an empty successful computation. Serves as an identity element when composing PYIO operations.
        Similar to an empty list or zero in other contexts.
        """
        return PYIO.success(None)

    def map(self, f: Callable[[A], B]) -> 'PYIO[E, B]':
        """
        Transforms the successful result without changing the error handling.
        Like applying a function to each element of a list, this lets you modify successful values while
        preserving any error state.

        Args:
            f: Function to apply to successful results
        """
        def new_compute() -> tuple[Optional[E], Optional[B]]:
            error, value = self._compute()
            if error is not None:
                return error, None
            return None, f(value)

        return PYIO(new_compute)

    def map_to(self, f: Callable[[], B]) -> 'PYIO[E, B]':
        """
        Similar to 'map', but throws away the input.

        Args:
            f: Function that generates the new value
        """
        return self.map(lambda _: f())

    def flat_map(self, f: Callable[[A], 'PYIO[E, B]']) -> 'PYIO[E, B]':
        """
        Chains computations where each step depends on previous results. The core sequencing operation for PYIO - allows
        you to use the result of one computation to determine what to do next.

        Args:
            f: Function that uses the successful result to decide what to do next
        """
        def new_compute() -> tuple[Optional[E], Optional[B]]:
            error, value = self._compute()
            if error is not None:
                return error, None
            return f(value)._compute()

        return PYIO(new_compute)

    def then(self, that: 'PYIO[E, B]') -> 'PYIO[E, B]':
        """
        Similar to 'flat_map', but it throws away the input.
        """
        return self.flat_map(lambda _: that)

    def zip(self, that: 'PYIO[E, B]') -> 'PYIO[E, tuple[A, B]]':
        """
        Pairs the results of two computations. When you need the results from two independent operations,
        this combines them into a tuple.

        Args:
            that: Another computation to pair with this one
        """
        return self.flat_map(lambda a: that.map(lambda b: (a, b)))

    def recover(self, handler: Callable[[E], 'PYIO[E, A]']) -> 'PYIO[E, A]':
        """
        Recovers from errors using the provided handler. Like a catch block, this lets you intercept errors and try
        alternative approaches.

        Args:
            handler: Function that takes an error and provides a recovery strategy.
        """
        def new_compute() -> tuple[Optional[Any], Optional[A]]:
            error, value = self._compute()
            if error is not None:
                return handler(error)._compute()
            return None, value

        return PYIO(new_compute)

    def match(self, failure: Callable[[E], B], success: Callable[[A], B]) -> 'PYIO[None, B]':
        """
        Consolidates error and success cases into a single value. Provides a way to handle both outcomes uniformly,
        similar to pattern matching on a Result type.

        Args:
            failure: How to handle the error case
            success: How to handle the success case
        """
        def fold_compute() -> tuple[None, B]:
            error, value = self._compute()
            if error is not None:
                return None, failure(error)
            return None, success(value)

        return PYIO(fold_compute)

    def match_pyio(self,
                   success: Callable[[A], 'PYIO[E, B]'],
                   failure: Callable[[E], 'PYIO[E, B]']) -> 'PYIO[E, B]':
        """
        Routes to different computations based on success/failure. Like match(), but allows the handlers to start
        new computations rather than just returning values.

        Args:
            success: What to do next if this succeeds
            failure: What to do next if this fails
        """
        def fold_compute() -> tuple[Optional[E], Optional[B]]:
            error, value = self._compute()
            if error is not None:
                return failure(error)._compute()
            return success(value)._compute()

        return PYIO(fold_compute)

    def is_success(self) -> 'PYIO[None, bool]':
        """
        Checks if the computation succeeded.
        A safe way to test the outcome without actually handling the success value or error.
        """
        def compute() -> tuple[None, bool]:
            error, _ = self._compute()
            return None, error is None

        return PYIO(compute)

    def is_failure(self) -> 'PYIO[None, bool]':
        """
        Checks if the computation failed.
        A safe way to test the outcome without actually handling the success value or error.
        """
        def compute() -> tuple[None, bool]:
            error, _ = self._compute()
            return None, error is not None

        return PYIO(compute)

    @staticmethod
    def chain_all(*effects: 'PYIO[E, A]') -> 'PYIO[E, A]':
        """
        Runs multiple computations in sequence.
        Useful for batching independent operations where you don't need intermediate results.

        Args:
            *effects: The computations to run in order
        """
        if not effects:
            return PYIO.unit()

        result = effects[0]
        for effect in effects[1:]:
            result = result.then(effect)

        return result

    @staticmethod
    def pipeline(*effects: Callable[[Optional[A]], 'PYIO[E, A]']) -> 'PYIO[E, A]':
        """
        Creates a pipeline of dependent computations.
        Each function gets the result of the previous computation, allowing for more complex workflows.

        Args:
            *effects: Functions that use previous results to create new computations
        """
        if not effects:
            return PYIO.success(None)

        result = effects[0](None)
        for effect in effects[1:]:
            result = result.flat_map(effect)

        return result

    def run(self) -> Union[A, E]:
        """
        Executes the computation and returns the final outcome.
        This is where the actual work happens - everything else just builds up the recipe for what to do.
        """
        error, value = self._compute()
        if error is not None:
            return error

        return value