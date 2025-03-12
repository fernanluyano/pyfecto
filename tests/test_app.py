from dataclasses import dataclass
from unittest import TestCase, mock

from src.pyfecto.app import PyfectoApp
from src.pyfecto.pyio import PYIO
from src.pyfecto.runtime import Runtime


@dataclass
class Config:
    api_key: str
    endpoint: str


class MockService:
    def __init__(self, config: Config):
        self.config = config

    def fetch_data(self, query: str):
        if not self.config.api_key:
            return PYIO.fail(ValueError("Missing API key"))
        if query == "error":
            return PYIO.fail(ValueError("Invalid query"))
        return PYIO.success(f"Results for {query} from {self.config.endpoint}")


class MyTestApplication(PyfectoApp[Exception]):
    """Example application for testing the PyfectoApp structure."""

    def __init__(self, config: Config, query: str, runtime: Runtime = None):
        super().__init__(runtime)
        self.service = MockService(config)
        self.query = query

    def run(self) -> PYIO[None, None]:
        return (
            PYIO.log_info(f"Querying with: {self.query}")
            .then(self.service.fetch_data(self.query))
            .flat_map(
                lambda result: PYIO.log_info(f"Got result: {result}").then(
                    PYIO.success(result)
                )
            )
        )


class TestPyfectoApp(TestCase):

    def test_successful_app_execution(self):
        config = Config(api_key="test-key", endpoint="https://api.example.com")
        app = MyTestApplication(config, "test-query")
        Runtime.run_app(app, exit_on_error=False)

    def test_failed_app_execution(self):
        config = Config(api_key="test-key", endpoint="https://api.example.com")
        app = MyTestApplication(config, "error")
        self.assertRaises(ValueError, lambda: Runtime.run_app(app, exit_on_error=False))

    @mock.patch("sys.exit")
    def test_run_app_with_exit(self, mock_exit):
        config = Config(api_key="test-key", endpoint="https://api.example.com")

        # Test error with exit
        app = MyTestApplication(config, "error")
        Runtime.run_app(app, exit_on_error=True, error_code=42)
        mock_exit.assert_called_once_with(42)

    def test_custom_runtime(self):
        # Create a custom runtime with debug logging
        custom_runtime = Runtime(log_level="DEBUG")

        config = Config(api_key="test-key", endpoint="https://api.example.com")
        app = MyTestApplication(config, "test-query", runtime=custom_runtime)
        Runtime.run_app(app, exit_on_error=False)
