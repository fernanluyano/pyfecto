"""
Collection utilities for working with PYIO effects.

This module provides functions for working with collections of PYIO effects or
applying effects to collections of values, similar to ZIO's collection utilities.
"""

from typing import Any, Callable, TypeVar

from .pyio import PYIO

A = TypeVar("A")
B = TypeVar("B")
E = TypeVar("E", bound=Exception | None)


def forall(items: list[A], f: Callable[[A], PYIO[E, bool]]) -> PYIO[E, bool]:
    """
    Checks if all items in a list satisfy a predicate function.

    This function evaluates whether every item in the list satisfies the provided predicate.
    It implements short-circuit evaluation, stopping immediately when it encounters an item
    that fails the predicate. If the input list is empty or None, it returns True (vacuous truth).

    Args:
        items: A list of items to check, or None
        f: A function that takes an item and returns a PYIO effect containing a boolean

    Returns:
        A PYIO effect that produces:
        - True if all items satisfy the predicate
        - False if any item fails the predicate
        - The first encountered error if any predicate evaluation fails
    """
    if items is None:
        return PYIO.attempt(lambda: True)

    def process_all():
        for item in items:
            try:
                result = f(item).run()
                if isinstance(result, Exception):
                    return result, None
                # interrupt the loop early, since the current predicate didn't pass
                elif not result:
                    return None, False
            except Exception as e:
                return e, None
        return None, True

    return PYIO(process_all)


def foreach(items: list[A], f: Callable[[A], PYIO[E, B]]) -> PYIO[E, list[B]]:
    """
    Applies the function f to each element in the list and collects the results.
    If any effect fails, the entire operation fails with that error.

    Args:
        items: A list of items to process
        f: A function that maps each item to a PYIO effect

    Returns:
        A PYIO effect that produces a list of all results if successful
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


def filter_(items: list[A], f: Callable[[A], PYIO[E, bool]]) -> PYIO[E, list[A]]:
    """
    Filters items in a list based on a predicate function that returns a PYIO effect.

    This function applies the predicate function to each item in the list and keeps only
    the items for which the predicate returns true. If any effect fails during evaluation,
    the entire operation fails with that error.

    Args:
        items: A list of items to filter
        f: A function that takes an item and returns a PYIO effect containing a boolean

    Returns:
        A PYIO effect that produces a list of the items that passed the filter if successful
    """
    results: list[A] = []
    if not items:
        return PYIO.attempt(lambda: results)

    def process_all():
        for item in items:
            try:
                result = f(item).run()
                if isinstance(result, Exception):
                    return result, None
                if result:
                    results.append(item)
            except Exception as e:
                return e, None
        return None, results

    return PYIO(process_all)


def partition(
    items: list[A], f: Callable[[A], PYIO[E, B]]
) -> PYIO[None, tuple[list[Exception], list[B]]]:
    """
    Partitions a list of items into successes and failures based on processing with a function.

    Unlike other collection functions that fail on the first error, partition collects all
    results - both successful outcomes and errors - and groups them into separate lists.
    This is useful when you want to process a batch of items and handle failures later
    rather than stopping at the first error.

    Args:
        items: A list of items to process
        f: A function that maps each item to a PYIO effect

    Returns:
        A PYIO effect that produces a tuple of (failures_list, successes_list)
        where failures_list contains all exceptions encountered and successes_list
        contains all successful results.
    """
    failures: list[Exception] = []
    successes: list[B] = []
    if not items:
        return PYIO.attempt(lambda: (failures, successes))

    def process_all():
        for item in items:
            try:
                result = f(item).run()
                if isinstance(result, Exception):
                    failures.append(result)
                else:
                    successes.append(result)
            except Exception as e:
                failures.append(e)
        return None, (failures, successes)

    return PYIO(process_all)
