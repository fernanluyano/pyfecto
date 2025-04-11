"""Unit tests for the pyfecto.collections module."""

from unittest import TestCase

from src.pyfecto.collections import (collect_all, filter_, forall, foreach,
                                     partition)
from src.pyfecto.pyio import PYIO


class TestCollections(TestCase):
    def test_foreach_empty_list(self):
        # Should return an empty list
        effect = foreach([], lambda x: PYIO.success(x * 2))
        self.assertEqual(effect.run(), [])

    def test_foreach_success(self):
        # Double each number
        effect = foreach([1, 2, 3], lambda x: PYIO.success(x * 2))
        self.assertEqual(effect.run(), [2, 4, 6])

    def test_foreach_failure(self):
        """Test foreach with an operation that fails."""

        def process(x):
            if x == 2:
                return PYIO.fail(ValueError("Error on item 2"))
            return PYIO.success(x * 2)

        # Should fail on the item with value 2
        effect = foreach([1, 2, 3], process)
        result = effect.run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Error on item 2")

    def test_foreach_with_complex_types(self):
        """Test foreach with complex types."""

        class User:
            def __init__(self, id, name):
                self.id = id
                self.name = name

            def __eq__(self, other):
                if not isinstance(other, User):
                    return False
                return self.id == other.id and self.name == other.name

        def get_user(id):
            return PYIO.success(User(id, f"User {id}"))

        # Convert IDs to User objects
        user_ids = [1, 2, 3]
        effect = foreach(user_ids, get_user)
        result = effect.run()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "User 1")
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[1].name, "User 2")
        self.assertEqual(result[2].id, 3)
        self.assertEqual(result[2].name, "User 3")

    def test_foreach_preserves_order(self):
        """Test that foreach preserves the order of the input list."""
        # Process in reverse but should maintain original order
        effect = foreach([3, 1, 2], lambda x: PYIO.success(x))
        self.assertEqual(effect.run(), [3, 1, 2])

    def test_foreach_within_foreach(self):
        """Test nested foreach operations."""

        def process_matrix(matrix):
            # For each row, sum its elements
            return foreach(
                matrix,
                lambda row: foreach(row, lambda x: PYIO.success(x)).map(
                    lambda nums: sum(nums)
                ),
            )

        matrix = [[1, 2], [3, 4], [5, 6]]
        effect = process_matrix(matrix)
        self.assertEqual(effect.run(), [3, 7, 11])

    def test_collect_all_empty_list(self):
        """Test collect_all with an empty list."""
        effect = collect_all([])
        self.assertEqual(effect.run(), [])

    def test_collect_all_success(self):
        """Test collect_all with successful effects."""
        effect1 = PYIO.success(1)
        effect2 = PYIO.success("hello")
        effect3 = PYIO.attempt(lambda: True)

        combined = collect_all([effect1, effect2, effect3])
        result = combined.run()

        self.assertEqual(result, [1, "hello", True])

    def test_collect_all_preserves_order(self):
        """Test that collect_all preserves the order of effects."""
        effects = [PYIO.success(i) for i in range(5)]
        result = collect_all(effects).run()
        self.assertEqual(result, [0, 1, 2, 3, 4])

    def test_collect_all_failure(self):
        """Test collect_all with a failing effect."""
        effect1 = PYIO.success(1)
        effect2 = PYIO.fail(ValueError("test error"))
        effect3 = PYIO.success(3)

        combined = collect_all([effect1, effect2, effect3])
        result = combined.run()

        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "test error")

    def test_collect_all_single_effect(self):
        """Test collect_all with a single effect."""
        effect = PYIO.success(42)
        result = collect_all([effect]).run()
        self.assertEqual(result, [42])

    def test_filter_empty_list(self):
        """Test filter_ with an empty list."""
        effect = filter_([], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), [])

    def test_filter_success(self):
        """Test filter_ with a successful predicate."""
        # Keep only even numbers
        effect = filter_([1, 2, 3, 4, 5], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), [2, 4])

    def test_filter_all_pass(self):
        """Test filter_ when all items pass the filter."""
        effect = filter_([2, 4, 6, 8], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), [2, 4, 6, 8])

    def test_filter_none_pass(self):
        """Test filter_ when no items pass the filter."""
        effect = filter_([1, 3, 5, 7], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), [])

    def test_filter_failure(self):
        """Test filter_ with a predicate that fails for some input."""

        def check_even(x):
            if x == 3:
                return PYIO.fail(ValueError("Error on item 3"))
            return PYIO.success(x % 2 == 0)

        # Should fail on the item with value 3
        effect = filter_([1, 2, 3, 4, 5], check_even)
        result = effect.run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Error on item 3")

    def test_partition_empty_list(self):
        """Test partition with an empty list."""
        # Should return empty lists for both failures and successes
        effect = partition([], lambda x: PYIO.success(x * 2))
        failures, successes = effect.run()

        self.assertEqual(failures, [])
        self.assertEqual(successes, [])

    def test_partition_all_success(self):
        """Test partition when all items succeed."""
        # Double each number, all should succeed
        effect = partition([1, 2, 3], lambda x: PYIO.success(x * 2))
        failures, successes = effect.run()

        self.assertEqual(failures, [])
        self.assertEqual(successes, [2, 4, 6])

    def test_partition_all_failures(self):
        """Test partition when all items fail."""

        # All operations fail
        def error_fn(x):
            return PYIO.fail(ValueError(f"Error with {x}"))

        effect = partition([1, 2, 3], error_fn)
        failures, successes = effect.run()

        self.assertEqual(len(failures), 3)
        self.assertEqual(len(successes), 0)

        # Verify error messages
        self.assertEqual(str(failures[0]), "Error with 1")
        self.assertEqual(str(failures[1]), "Error with 2")
        self.assertEqual(str(failures[2]), "Error with 3")

    def test_partition_mixed_results(self):
        """Test partition with a mix of successes and failures."""

        def process(x):
            if x % 2 == 0:
                return PYIO.success(x * 10)
            else:
                return PYIO.fail(ValueError(f"Odd number: {x}"))

        effect = partition([1, 2, 3, 4, 5], process)
        failures, successes = effect.run()

        # Should have 3 failures (for odd numbers) and 2 successes (for even numbers)
        self.assertEqual(len(failures), 3)
        self.assertEqual(len(successes), 2)

        # Check success values
        self.assertEqual(successes, [20, 40])

        # Check error messages
        self.assertEqual(str(failures[0]), "Odd number: 1")
        self.assertEqual(str(failures[1]), "Odd number: 3")
        self.assertEqual(str(failures[2]), "Odd number: 5")

    def test_partition_operation_throwing_exception(self):
        """Test partition with operations that throw exceptions rather than returning PYIO failures."""

        def buggy_process(x):
            if x == 3:
                # This will be caught by the try/except in partition
                raise RuntimeError("Unexpected error")
            return PYIO.success(x)

        effect = partition([1, 2, 3, 4], buggy_process)
        failures, successes = effect.run()

        # Should have 1 failure and 3 successes
        self.assertEqual(len(failures), 1)
        self.assertEqual(len(successes), 3)

        # Check success values
        self.assertEqual(successes, [1, 2, 4])

        # Check error
        self.assertIsInstance(failures[0], RuntimeError)
        self.assertEqual(str(failures[0]), "Unexpected error")

    def test_partition_preserves_order(self):
        """Test that partition preserves the order in both success and failure lists."""

        def process(x):
            if x in [2, 4, 6]:
                return PYIO.fail(ValueError(f"Error: {x}"))
            return PYIO.success(x)

        items = [1, 2, 3, 4, 5, 6, 7]
        effect = partition(items, process)
        failures, successes = effect.run()

        # Check order preservation
        self.assertEqual(successes, [1, 3, 5, 7])

        # Check errors are in the right order
        self.assertEqual(len(failures), 3)
        self.assertEqual(str(failures[0]), "Error: 2")
        self.assertEqual(str(failures[1]), "Error: 4")
        self.assertEqual(str(failures[2]), "Error: 6")

    def test_forall_empty_list(self):
        """Test forall with an empty list should return True."""
        effect = forall([], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), True)

    def test_forall_none_input(self):
        """Test forall with None input should return True."""
        effect = forall(None, lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), True)

    def test_forall_all_true(self):
        """Test forall when all items pass the predicate."""
        effect = forall([2, 4, 6, 8], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), True)

    def test_forall_one_false(self):
        """Test forall when one item fails the predicate."""
        effect = forall([2, 4, 5, 8], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), False)

    def test_forall_all_false(self):
        """Test forall when all items fail the predicate."""
        effect = forall([1, 3, 5, 7], lambda x: PYIO.success(x % 2 == 0))
        self.assertEqual(effect.run(), False)

    def test_forall_short_circuit(self):
        """Test forall short-circuits when it finds a failing predicate."""
        counter = 0

        def count_and_check(x):
            nonlocal counter
            counter += 1
            return PYIO.success(x % 2 == 0)

        # The 3rd item (5) fails the predicate, so we should only process 3 items
        effect = forall([2, 4, 5, 8, 10], count_and_check)
        self.assertEqual(effect.run(), False)
        self.assertEqual(counter, 3)  # Only processed items until failure

    def test_forall_error_in_predicate(self):
        """Test forall when the predicate function raises an error."""

        def buggy_predicate(x):
            if x == 3:
                return PYIO.fail(ValueError("Error processing item 3"))
            return PYIO.success(x % 2 == 0)

        effect = forall([2, 4, 3, 6], buggy_predicate)
        result = effect.run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Error processing item 3")

    def test_forall_exception_in_predicate(self):
        """Test forall when the predicate function throws an exception."""

        def throwing_predicate(x):
            if x == 3:
                raise RuntimeError("Unexpected runtime error")
            return PYIO.success(x % 2 == 0)

        effect = forall([2, 4, 3, 6], throwing_predicate)
        result = effect.run()
        self.assertIsInstance(result, RuntimeError)
        self.assertEqual(str(result), "Unexpected runtime error")
