"""Unit tests for the pyfecto.collections module."""

from unittest import TestCase

from src.pyfecto.collections import foreach
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

    def test_foreach_with_exception_thrown(self):
        """Test foreach with a function that throws an exception."""

        def process(x):
            if x == 2:
                raise ValueError("Exception thrown on item 2")
            return PYIO.success(x * 2)

        # Should fail when the function throws
        effect = foreach([1, 2, 3], process)
        result = effect.run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Exception thrown on item 2")

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

    def test_foreach_with_async_simulation(self):
        """Test foreach with operations that simulate asynchronous behavior."""
        results = []

        def track_execution(x):
            results.append(x)
            return PYIO.success(x)

        # Should execute in sequence
        foreach([1, 2, 3], track_execution).run()
        self.assertEqual(results, [1, 2, 3])

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

    def test_foreach_with_flat_map(self):
        """Test foreach combined with flat_map."""

        def get_user_orders(user_id):
            # Simulate fetching orders for a user
            orders = {1: ["A1", "A2"], 2: ["B1"], 3: []}
            return PYIO.success(orders.get(user_id, []))

        # Get all orders for all users
        effect = foreach([1, 2, 3], get_user_orders).map(
            lambda order_lists: [order for sublist in order_lists for order in sublist]
        )

        self.assertEqual(effect.run(), ["A1", "A2", "B1"])
