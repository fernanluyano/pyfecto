"""
Example Pyfecto Application: Weather CLI

This example demonstrates how to create a command-line application using the Pyfecto
application structure. It simulates fetching weather data for a given city.
"""
import time
from dataclasses import dataclass

from pyfecto.app import PyfectoApp
from pyfecto.pyio import PYIO
from pyfecto.runtime import Runtime


# ===== Domain Models =====

@dataclass
class WeatherData:
    temperature: float
    condition: str
    humidity: float
    wind_speed: float

    def format(self) -> str:
        return (
            f"Temperature: {self.temperature}°C\n"
            f"Condition: {self.condition}\n"
            f"Humidity: {self.humidity}%\n"
            f"Wind Speed: {self.wind_speed} km/h"
        )


class WeatherAPIError(Exception):
    """Error raised when weather API calls fail"""
    pass


# ===== Services =====

class WeatherService:
    """Service for retrieving weather data"""

    def __init__(self):
        # Mock database of city weather data
        self._db = {
            "london": WeatherData(12.5, "Cloudy", 85.0, 10.2),
            "paris": WeatherData(15.3, "Partly Cloudy", 70.0, 8.5),
            "new york": WeatherData(18.2, "Sunny", 65.0, 12.3),
            "tokyo": WeatherData(20.1, "Rainy", 90.0, 5.8),
        }

    def get_weather(self, city: str) -> PYIO[WeatherAPIError, WeatherData]:
        """
        Fetch weather data for the given city.

        Args:
            city: Name of the city to fetch weather for

        Returns:
            PYIO effect containing WeatherData on success or WeatherAPIError on failure
        """
        # Normalize city name
        city_lower = city.lower()

        # Simulate network request
        return PYIO.log_span(
            name="weather-api",
            log_msg=f"Fetching weather data for {city}",
            operation=PYIO.attempt(lambda: self._fetch_weather(city_lower))
        )

    def _fetch_weather(self, city: str) -> WeatherData:
        """Simulated API call that might fail"""
        if city not in self._db:
            raise WeatherAPIError(f"Could not find weather data for {city}")
        # simulate waiting on an api/db call
        time.sleep(1)
        return self._db[city]


# ===== Application =====

class WeatherApp(PyfectoApp[Exception]):
    """
    Weather application that retrieves and displays weather information.
    """

    def __init__(
        self,
        city: str,
        verbose: bool = False
    ):
        """
        Initialize the weather application.

        Args:
            city: City to fetch weather for
            verbose: Whether to use verbose logging
        """
        # Configure the runtime with custom settings if verbose
        log_level = "DEBUG" if verbose else "INFO"
        custom_runtime = Runtime(log_level=log_level)
        super().__init__(runtime=custom_runtime)

        self.service = WeatherService()
        self.city = city

    def run(self) -> PYIO[Exception, None]:
        """
        Main application logic for retrieving and formatting weather data.

        Returns:
            PYIO effect containing formatted weather data string or exception
        """
        return (
            PYIO.log_info(f"Starting weather lookup for {self.city}")
            .then(self.service.get_weather(self.city))
            .map(lambda weather_data: weather_data.format())
            .flat_map(lambda formatted_result:
                PYIO.log_info("Weather data retrieved successfully")
                .then(PYIO.success(formatted_result))
            )
        )


def main():
    # Create and run the application
    city = "london"
    verbose = False
    app = WeatherApp(
        city=city,
        verbose=verbose
    )
    Runtime.run_app(app, exit_on_error=True)

if __name__ == "__main__":
    main()