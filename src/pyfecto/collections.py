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


def collect_all(effects: list[PYIO[E, Any]]) -> PYIO[E, list[Any]]:
    """
    Collects all effects into a single effect that produces a list of results.

    This function combines multiple PYIO effects into a single effect that, when run,
    will execute all effects in sequence and collect their results. If any effect
    fails, the entire operation fails with that error. The effects can return
    different types of values.

    Args:
        effects: A list of PYIO effects to collect, potentially with different return types

    Returns:
        A PYIO effect that will produce a list of all results if all effects succeed,
        or fail with the first encountered error.

    Example:
        # Collect results from multiple heterogeneous operations
        user_effect = get_user(user_id)                # Returns User
        posts_count_effect = count_posts(user_id)      # Returns int
        is_active_effect = check_if_active(user_id)    # Returns bool

        all_data = collect_all([user_effect, posts_count_effect, is_active_effect])
        # all_data will produce [user, count, is_active] when run
    """
    results: list[Any] = []
    if not effects:
        return PYIO.attempt(lambda: results)

    # Create a PYIO that processes all items and builds a result list
    def process_all():
        for effect in effects:
            try:
                result = effect.run()
                if isinstance(result, Exception):
                    return result, None
                results.append(result)
            except Exception as e:
                return e, None
        return None, results

    return PYIO(process_all)
