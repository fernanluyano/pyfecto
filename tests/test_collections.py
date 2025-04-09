"""Unit tests for the pyfecto.collections module."""

from unittest import TestCase

from src.pyfecto.collections import collect_all, filter_, foreach
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
