from dataclasses import dataclass
from typing import Optional
from unittest import TestCase

from src.pyfecto.pyio import PYIO


@dataclass
class User:
    id: int
    name: str


class DatabaseError(Exception):
    pass


class TestPYIO(TestCase):

    def test_dummy(self):
        def get_user(
            user_id: int,
        ) -> PYIO[None, User] | PYIO[None, None] | PYIO[Exception, None]:
            try:
                # Simulate DB lookup
                if user_id == 1:
                    return PYIO.success(User(1, "Alice"))
                return PYIO.success(None)
            except Exception as e:
                return PYIO.fail(DatabaseError(str(e)))

        def update_user(
            user: User, new_name: str
        ) -> PYIO[None, User] | PYIO[Exception, None]:
            try:
                # Simulate DB update
                return PYIO.success(User(user.id, new_name))
            except Exception as e:
                return PYIO.fail(DatabaseError(str(e)))

        # Usage
        def rename_user(user_id: int, new_name: str):
            return get_user(user_id).flat_map(
                lambda maybe_user: (
                    PYIO.success(None)
                    if maybe_user is None
                    else update_user(maybe_user, new_name)
                )
            )

        # Run it
        result = rename_user(2, "Alicia").run()
        print(result)

    def test_success(self):
        effect = PYIO.success(42)
        self.assertEqual(effect.run(), 42)

    def test_fail(self):
        error = ValueError("test error")
        effect = PYIO.fail(error)
        self.assertEqual(effect.run(), error)

    def test_attempt_success(self):
        effect = PYIO.attempt(lambda: 42)
        self.assertEqual(effect.run(), 42)

    def test_effect_failure(self):
        def failing_function():
            raise ValueError("test error")

        effect = PYIO.attempt(failing_function)
        result = effect.run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "test error")

    def test_map_success(self):
        effect = PYIO.success(42).map(lambda x: x * 2)
        self.assertEqual(effect.run(), 84)

    def test_map_failure(self):
        error = ValueError("test error")
        effect = PYIO.fail(error).map(lambda x: x * 2)
        self.assertEqual(effect.run(), error)

    def test_map_to(self):
        effect = PYIO.success(42).map_to(lambda: "hello")
        self.assertEqual(effect.run(), "hello")

        # Should work with failures too
        error = ValueError("test error")
        failed_effect = PYIO.fail(error).map_to(lambda: "hello")
        self.assertEqual(failed_effect.run(), error)

        # Should evaluate the function
        counter = 0

        def increment():
            nonlocal counter
            counter += 1
            return counter

        effect = PYIO.success(42).map_to(increment)
        self.assertEqual(effect.run(), 1)
        self.assertEqual(counter, 1)

    def test_then(self):
        # Test success case
        effect = PYIO.success(42).then(PYIO.success("hello"))
        self.assertEqual(effect.run(), "hello")

        # Test that first value is discarded
        def increment():
            nonlocal counter
            counter += 1
            return counter

        counter = 0
        first = PYIO.attempt(increment)
        second = PYIO.success("done")
        result = first.then(second).run()

        self.assertEqual(result, "done")
        self.assertEqual(counter, 1)  # Ensures first effect ran

        # Test failure in first effect
        error = ValueError("test error")
        failed_effect = PYIO.fail(error).then(PYIO.success("hello"))
        self.assertEqual(failed_effect.run(), error)

        # Test failure in second effect
        error2 = ValueError("second error")
        failed_effect2 = PYIO.success(42).then(PYIO.fail(error2))
        self.assertEqual(failed_effect2.run(), error2)

    def test_flat_map_success(self):
        effect = PYIO.success(42).flat_map(lambda x: PYIO.success(x * 2))
        self.assertEqual(effect.run(), 84)

    def test_flat_map_failure(self):
        error = ValueError("test error")
        effect = PYIO.fail(error).flat_map(lambda x: PYIO.success(x * 2))
        self.assertEqual(effect.run(), error)

    def test_zip_success(self):
        effect1 = PYIO.success(42)
        effect2 = PYIO.success("hello")
        combined = effect1.zip(effect2)
        self.assertEqual(combined.run(), (42, "hello"))

    def test_zip_failure_first(self):
        error = ValueError("test error")
        effect1 = PYIO.fail(error)
        effect2 = PYIO.success("hello")
        combined = effect1.zip(effect2)
        self.assertEqual(combined.run(), error)

    def test_zip_failure_second(self):
        error = ValueError("test error")
        effect1 = PYIO.success(42)
        effect2 = PYIO.fail(error)
        combined = effect1.zip(effect2)
        self.assertEqual(combined.run(), error)

    def test_recover_success(self):
        effect = PYIO.success(42).recover(lambda e: PYIO.success(0))
        self.assertEqual(effect.run(), 42)

    def test_recover_failure(self):
        error = ValueError("test error")
        effect = PYIO.fail(error).recover(lambda e: PYIO.success(0))
        self.assertEqual(effect.run(), 0)

    def test_fold_success(self):
        effect = PYIO.success(42).match(
            failure=lambda e: f"Error: {e}", success=lambda x: f"Value: {x}"
        )
        self.assertEqual(effect.run(), "Value: 42")

    def test_match_failure(self):
        error = ValueError("test error")
        effect = PYIO.fail(error).match(
            failure=lambda e: f"Error: {e}", success=lambda x: f"Value: {x}"
        )
        self.assertEqual(effect.run(), "Error: test error")

    def test_match_pyio(self):
        # Test success path
        success_effect = PYIO.success(42).match_pyio(
            success=lambda x: PYIO.success(f"Success: {x}"),
            failure=lambda e: PYIO.success(f"Error: {e}"),
        )
        self.assertEqual(success_effect.run(), "Success: 42")

        # Test failure path
        error = ValueError("test error")
        failure_effect = PYIO.fail(error).match_pyio(
            success=lambda x: PYIO.success(f"Success: {x}"),
            failure=lambda e: PYIO.fail(e),
        )
        self.assertEqual(failure_effect.run(), error)

    def test_complex_composition(self):
        @dataclass
        class User:
            id: int
            name: str

        def get_user(id: int):
            if id == 1:
                return PYIO.success(User(1, "Alice"))
            return PYIO.fail(ValueError("User not found"))

        def get_greeting(user: User):
            return PYIO.success(f"Hello, {user.name}!")

        # Test successful path
        effect1 = get_user(1).flat_map(get_greeting)
        self.assertEqual(effect1.run(), "Hello, Alice!")

        # Test failure path
        effect2 = get_user(2).flat_map(get_greeting)
        self.assertIsInstance(effect2.run(), ValueError)
        self.assertEqual(str(effect2.run()), "User not found")

    def test_long_successful_flow(self):
        def validate_user(name: str):
            return (
                PYIO.success(name)
                if len(name) >= 3
                else PYIO.fail(ValueError("Name too short"))
            )

        def create_email(name: str):
            return PYIO.success(f"{name.lower()}@example.com")

        def check_permissions(email: str):
            return (
                PYIO.success(True)
                if "example.com" in email
                else PYIO.fail(ValueError("Invalid domain"))
            )

        def generate_token(has_permission: bool):
            return PYIO.success("secret-token-123")

        def record_audit_log(token: str):
            return PYIO.success(f"Audit: token {token} created")

        flow = (
            PYIO.success("Alice")
            .flat_map(validate_user)
            .flat_map(create_email)
            .flat_map(check_permissions)
            .flat_map(generate_token)
            .flat_map(record_audit_log)
        )

        self.assertEqual(flow.run(), "Audit: token secret-token-123 created")

    def test_long_flow_with_failure(self):
        def step1(x: int):
            return PYIO.success(x + 1)

        def step2(x: int):
            return PYIO.attempt(lambda: x / 0)

        def step3(x: int):
            return PYIO.success(f"Final value: {x}")

        flow = PYIO.success(0).flat_map(step1).flat_map(step2).flat_map(step3)

        self.assertEqual(flow.is_failure().run(), True)

    def test_for(self):
        # a single effect
        result = PYIO.chain_all(PYIO.success(1)).run()
        self.assertEqual(result, 1)

        result = PYIO.chain_all(PYIO.success(1), PYIO.success(2), PYIO.success(3)).run()
        self.assertEqual(result, 3)

        # stop at the first error
        error = ValueError("test error")
        result = PYIO.chain_all(
            PYIO.success(1), PYIO.fail(error), PYIO.success(3)
        ).run()
        self.assertEqual(result, error)

        # no-op
        result = PYIO.chain_all().run()
        self.assertEqual(result, None)

    def test_for_effects(self):
        def first(_: None) -> PYIO[None, int]:
            return PYIO.success(1)

        def double(x: int) -> PYIO[None, int]:
            return PYIO.success(x * 2)

        def to_string(x: int) -> PYIO[None, str]:
            return PYIO.success(f"Result: {x}")

        # Test successful chain
        result = PYIO.pipeline(first, double, to_string).run()
        self.assertEqual(result, "Result: 2")

        # Test with error
        def fail(x: int) -> PYIO[Exception, None]:
            return PYIO.fail(ValueError(f"Error at {x}"))

        result = PYIO.pipeline(
            first, double, fail, to_string  # Should not reach this
        ).run()
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Error at 2")

        # Test empty
        result = PYIO.pipeline().run()
        self.assertIsNone(result)

        # Test single effect
        result = PYIO.pipeline(lambda _: PYIO.success(42)).run()
        self.assertEqual(result, 42)

        # Test with dependencies
        def get_user(_: None):
            return PYIO.success({"id": 1, "name": "Alice"})

        def get_permissions(user: dict):
            return PYIO.success({"user_id": user["id"], "perms": ["read", "write"]})

        def get_data(perms: dict):
            return PYIO.success(f"Data for user {perms['user_id']}")

        result = PYIO.pipeline(get_user, get_permissions, get_data).run()

        self.assertEqual(result, "Data for user 1")
