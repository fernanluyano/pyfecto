"""Unit tests for verifying the laziness of the pyfecto.collections functions."""

from unittest import TestCase

from src.pyfecto.collections import (collect_all, filter_, forall, foreach,
                                     partition)
from src.pyfecto.pyio import PYIO


class TestCollectionLaziness(TestCase):
    def test_forall_laziness(self):
        """Test that forall is lazy and doesn't evaluate predicates until run() is called."""
        # Setup a tracking list to record function calls
        calls = []

        def tracking_predicate(x):
            # This function records that it was called
            calls.append(x)
            return PYIO.success(x % 2 == 0)

        # Create a list of items
        items = [2, 4, 6, 8, 10]

        # Call forall to create the effect
        effect = forall(items, tracking_predicate)

        # At this point, the predicate should not have been called yet
        self.assertEqual(
            calls, [], "Predicate was evaluated eagerly before run() was called"
        )

        # Now run the effect
        result = effect.run()

        # Verify the effect worked correctly
        self.assertTrue(result)

        # Verify all items were processed (since all pass the predicate)
        self.assertEqual(
            calls,
            items,
            "Not all items were processed or they were processed out of order",
        )

        # Reset tracking
        calls.clear()

        # Test with an item that will fail the predicate
        items_with_failure = [2, 4, 5, 8, 10]  # 5 will fail

        # Create another effect
        effect2 = forall(items_with_failure, tracking_predicate)

        # Verify still lazy
        self.assertEqual(calls, [], "Second predicate was evaluated eagerly")

        # Run the effect
        result2 = effect2.run()

        # Verify it failed as expected
        self.assertFalse(result2)

        # Verify short-circuit behavior - only items up to and including the first failure should be processed
        self.assertEqual(
            calls,
            [2, 4, 5],
            "Short-circuit behavior not working or items processed out of order",
        )

    def test_foreach_laziness(self):
        """Test that foreach is lazy and doesn't evaluate functions until run() is called."""
        # Setup a tracking list to record function calls
        calls = []

        def tracking_function(x):
            # This function records that it was called
            calls.append(x)
            return PYIO.success(x * 2)

        # Create a list of items
        items = [1, 2, 3, 4, 5]

        # Call foreach to create the effect
        effect = foreach(items, tracking_function)

        # At this point, the function should not have been called yet
        self.assertEqual(
            calls, [], "Function was evaluated eagerly before run() was called"
        )

        # Now run the effect
        result = effect.run()

        # Verify the effect worked correctly
        self.assertEqual(result, [2, 4, 6, 8, 10])

        # Verify all items were processed
        self.assertEqual(
            calls,
            items,
            "Not all items were processed or they were processed out of order",
        )

        # Reset tracking
        calls.clear()

        # Test with a function that will fail for one item
        def failing_function(x):
            calls.append(x)
            if x == 3:
                return PYIO.fail(ValueError(f"Error with {x}"))
            return PYIO.success(x * 2)

        # Create another effect
        effect2 = foreach([1, 2, 3, 4, 5], failing_function)

        # Verify still lazy
        self.assertEqual(calls, [], "Failing function was evaluated eagerly")

        # Run the effect
        result2 = effect2.run()

        # Verify it failed as expected
        self.assertIsInstance(result2, ValueError)
        self.assertEqual(str(result2), "Error with 3")

        # Verify it processed items until the error
        self.assertEqual(calls, [1, 2, 3], "Should process items until the error")

    def test_collect_all_laziness(self):
        """Test that collect_all is lazy and doesn't evaluate effects until run() is called."""
        # Setup tracking variables
        effect1_evaluated = False
        effect2_evaluated = False
        effect3_evaluated = False

        def create_effect1():
            nonlocal effect1_evaluated
            effect1_evaluated = True
            return 1

        def create_effect2():
            nonlocal effect2_evaluated
            effect2_evaluated = True
            return "hello"

        def create_effect3():
            nonlocal effect3_evaluated
            effect3_evaluated = True
            return True

        # Create PYIO effects
        effect1 = PYIO.attempt(create_effect1)
        effect2 = PYIO.attempt(create_effect2)
        effect3 = PYIO.attempt(create_effect3)

        # At this point, none of the effects should be evaluated
        self.assertFalse(effect1_evaluated, "Effect1 was evaluated eagerly")
        self.assertFalse(effect2_evaluated, "Effect2 was evaluated eagerly")
        self.assertFalse(effect3_evaluated, "Effect3 was evaluated eagerly")

        # Combine effects using collect_all
        combined = collect_all([effect1, effect2, effect3])

        # Still, none of the effects should be evaluated
        self.assertFalse(
            effect1_evaluated, "Effect1 was evaluated when collect_all was called"
        )
        self.assertFalse(
            effect2_evaluated, "Effect2 was evaluated when collect_all was called"
        )
        self.assertFalse(
            effect3_evaluated, "Effect3 was evaluated when collect_all was called"
        )

        # Run the combined effect
        result = combined.run()

        # Verify the effect worked correctly
        self.assertEqual(result, [1, "hello", True])

        # Now the effects should have been evaluated
        self.assertTrue(
            effect1_evaluated, "Effect1 was not evaluated when run() was called"
        )
        self.assertTrue(
            effect2_evaluated, "Effect2 was not evaluated when run() was called"
        )
        self.assertTrue(
            effect3_evaluated, "Effect3 was not evaluated when run() was called"
        )

        # Test with an effect that will fail
        effect1_evaluated = False
        effect2_evaluated = False
        effect3_evaluated = False

        def failing_effect():
            nonlocal effect2_evaluated
            effect2_evaluated = True
            raise ValueError("Test error")

        # Create effects
        effect1 = PYIO.attempt(create_effect1)
        effect2 = PYIO.attempt(failing_effect)
        effect3 = PYIO.attempt(create_effect3)

        # Combine effects
        combined = collect_all([effect1, effect2, effect3])

        # Run the combined effect
        result = combined.run()

        # Verify it failed as expected
        self.assertIsInstance(result, ValueError)

        # Verify effects were evaluated in order until the failure
        self.assertTrue(effect1_evaluated, "Effect1 was not evaluated")
        self.assertTrue(effect2_evaluated, "Failing effect was not evaluated")
        self.assertFalse(
            effect3_evaluated, "Effect3 should not be evaluated after failure"
        )

    def test_filter_laziness(self):
        """Test that filter_ is lazy and doesn't evaluate predicates until run() is called."""
        # Setup a tracking list to record function calls
        calls = []

        def tracking_predicate(x):
            # This function records that it was called
            calls.append(x)
            return PYIO.success(x % 2 == 0)

        # Create a list of items
        items = [1, 2, 3, 4, 5]

        # Call filter_ to create the effect
        effect = filter_(items, tracking_predicate)

        # At this point, the predicate should not have been called yet
        self.assertEqual(
            calls, [], "Predicate was evaluated eagerly before run() was called"
        )

        # Now run the effect
        result = effect.run()

        # Verify the effect worked correctly
        self.assertEqual(result, [2, 4])

        # Verify all items were processed
        self.assertEqual(
            calls,
            items,
            "Not all items were processed or they were processed out of order",
        )

        # Reset tracking
        calls.clear()

        # Test with a predicate that will fail for one item
        def failing_predicate(x):
            calls.append(x)
            if x == 3:
                return PYIO.fail(ValueError(f"Error with {x}"))
            return PYIO.success(x % 2 == 0)

        # Create another effect
        effect2 = filter_(items, failing_predicate)

        # Verify still lazy
        self.assertEqual(calls, [], "Failing predicate was evaluated eagerly")

        # Run the effect
        result2 = effect2.run()

        # Verify it failed as expected
        self.assertIsInstance(result2, ValueError)
        self.assertEqual(str(result2), "Error with 3")

        # Verify it processed items until the error
        self.assertEqual(calls, [1, 2, 3], "Should process items until the error")

    def test_partition_laziness(self):
        """Test that partition is lazy and doesn't evaluate functions until run() is called."""
        # Setup a tracking list to record function calls
        calls = []

        def tracking_function(x):
            # This function records that it was called
            calls.append(x)
            if x % 2 == 0:
                return PYIO.success(x * 10)
            else:
                return PYIO.fail(ValueError(f"Odd number: {x}"))

        # Create a list of items
        items = [1, 2, 3, 4, 5]

        # Call partition to create the effect
        effect = partition(items, tracking_function)

        # At this point, the function should not have been called yet
        self.assertEqual(
            calls, [], "Function was evaluated eagerly before run() was called"
        )

        # Now run the effect
        failures, successes = effect.run()

        # Verify the effect worked correctly
        self.assertEqual(len(failures), 3)
        self.assertEqual(len(successes), 2)
        self.assertEqual(successes, [20, 40])
        self.assertEqual(str(failures[0]), "Odd number: 1")
        self.assertEqual(str(failures[1]), "Odd number: 3")
        self.assertEqual(str(failures[2]), "Odd number: 5")

        # Verify all items were processed
        self.assertEqual(
            calls,
            items,
            "Not all items were processed or they were processed out of order",
        )

        # Reset tracking
        calls.clear()

        # Test with a function that throws an exception
        def throwing_function(x):
            calls.append(x)
            if x == 3:
                raise RuntimeError(f"Runtime error with {x}")
            return PYIO.success(x * 10)

        # Create another effect
        effect2 = partition(items, throwing_function)

        # Verify still lazy
        self.assertEqual(calls, [], "Throwing function was evaluated eagerly")

        # Run the effect
        failures, successes = effect2.run()

        # Verify the effect handled the exception correctly
        self.assertEqual(len(failures), 1)
        self.assertEqual(len(successes), 4)
        self.assertEqual(successes, [10, 20, 40, 50])
        self.assertIsInstance(failures[0], RuntimeError)
        self.assertEqual(str(failures[0]), "Runtime error with 3")

        # Verify all items were processed (partition doesn't short-circuit)
        self.assertEqual(
            calls,
            items,
            "Not all items were processed or they were processed out of order",
        )
