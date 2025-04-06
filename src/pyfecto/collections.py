"""
Collection utilities for working with PYIO effects.

This module provides functions for working with collections of PYIO effects or
applying effects to collections of values, similar to ZIO's collection utilities.
"""

from typing import Callable, TypeVar, Any

from .pyio import PYIO

A = TypeVar("A")
B = TypeVar("B")
E = TypeVar("E", bound=Exception | None)


def foreach(items: list[A], f: Callable[[A], PYIO[E, B]]) -> PYIO[E, list[B]]:
    """
    Applies the function f to each element in the list and collects the results.
    If any effect fails, the entire operation fails with that error.

    Args:
        items: A list of items to process
        f: A function that maps each item to a PYIO effect

    Returns:
        A PYIO effect that produces a list of all results if successful

    Example:
        # Convert a list of IDs to User objects from database
        user_ids = [1, 2, 3]
        users_effect = foreach(user_ids, get_user_by_id)
        # users_effect will contain a list of User objects if all succeed
        # or fail with the first error encountered
    """

    results: list[B] = []
    if not items:
        return PYIO.attempt(lambda: results)

    # Create a PYIO that processes all items and builds a result list
    def process_all():
        for item in items:
            try:
                effect = f(item)
                result = effect.run()
                if isinstance(result, Exception):
                    return result, None
                results.append(result)
            except Exception as e:
                return e, None
        return None, results

    return PYIO(process_all)


def collectAll(effects: list[PYIO[Any, Any]]) -> PYIO[E, list[Any]]:
    results: list[Any] = []

    for e in effects:
        try:
            result = e.run()
            if isinstance(result, Exception):
                return PYIO.fail(result)
            results.append(result)
        except Exception as e:
            return PYIO.fail(e)

    return PYIO.success(results)
