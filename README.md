# Pyfecto - Pure IO Effects for Python

Pyfecto is a simple yet powerful library for handling effects and errors in Python, inspired by Scala's [ZIO](https://zio.dev/) library.
It provides a composable way to handle computations that might fail, ensuring type safety and maintainability.

Like ZIO, Pyfecto models effectful computations as values, enabling powerful composition and error handling patterns while maintaining referential transparency.
While ZIO offers a more comprehensive suite of features for concurrent and parallel programming in Scala, Pyfecto brings its core concepts of effect management to Python.

## Features

- Error handling without exceptions
- Lazy evaluation of effects
- Composable operations
- Clean separation of description and execution
- Fully type-hinted for modern Python development

## Installation

```bash
pip install pyfecto
```

## Quick Start

```python
from pyfecto.pyio import PYIO

# Create a simple effect
def divide(a: int, b: int):
    if b == 0:
        return PYIO.fail(ValueError("Division by zero"))
    return PYIO.success(a / b)


# Chain multiple effects
def compute_average(numbers: list[int]):
    return (
        PYIO.success(sum(numbers))
        .flat_map(lambda total: divide(total, len(numbers)))
    )


# Run the computation
result = compute_average([1, 2, 3, 4]).run()
# Returns: 2.5

result = compute_average([]).run()
# Returns: ValueError("Division by zero")
```

## Core Concepts

Pyfecto is built around a few key concepts:

1. **Effects**: An effect represents a computation that might fail. It carries both the potential error type `E` and success type `A`.

2. **Lazy Evaluation**: Effects are only executed when `.run()` is called, allowing for composition without immediate execution.

3. **Error Channel**: Instead of throwing exceptions, errors are carried in a type-safe way through the error channel.

## Key Operations

### Creating Effects

```python
from pyfecto.pyio import PYIO

# Success case
success_effect = PYIO.success(42)

# Error case
error_effect = PYIO.fail(ValueError("Something went wrong"))

# From potentially throwing function
def might_throw() -> int:
    raise ValueError("Oops")

safe_effect = PYIO.attempt(might_throw)
```

### Transforming Effects

```python
from pyfecto.pyio import PYIO

# Map success values
effect = PYIO.success(42).map(lambda x: x * 2)

# Chain effects
effect = (
    PYIO.success(42)
    .flat_map(lambda x: PYIO.success(x * 2))
)

# Handle errors
effect = (
    PYIO.fail(ValueError("Oops"))
    .recover(lambda err: PYIO.success(0))  # Default value on error
)
```

### Combining Effects

```python
from pyfecto.pyio import PYIO

# Sequence independent effects
combined = PYIO.chain_all(
    effect1,
    effect2,
    effect3
)

# Create dependent pipelines
pipeline = PYIO.pipeline(
    lambda _: effect1,
    lambda prev: effect2(prev),
    lambda prev: effect3(prev)
)

# Zip effects together
zipped = effect1.zip(effect2)  # Gets tuple of results
```

## Runtime Configuration

Pyfecto includes a runtime configuration system that allows you to customize logging and span tracking using [Loguru](https://github.com/Delgan/loguru) as the backend:


```python
from pyfecto.runtime import Runtime
import sys

# Define a custom sink function for logs
def alert_sink(message):
    if "error" in message.lower():
        print(f"🚨 ALERT: {message}")

# Configure the runtime
runtime = Runtime(
    log_level="DEBUG",  # Set minimum log level
    log_format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message} {extra}",  # Custom format
    sinks=[
        # Standard stderr sink
        {
            'sink': sys.stderr,
            'level': "INFO",
            'colorize': True,
        },
        # File sink with rotation
        {
            'sink': "app.log",
            'rotation': "10 MB",
            'retention': "1 week",
            'level': "DEBUG",
        },
        # Custom callable sink
        alert_sink
    ]
)

# The logger is now configured and ready to use
from pyfecto.runtime import LOGGER

# Regular logging
LOGGER.info("Application started")

# Logging with context
user_logger = LOGGER.bind(user_id="12345")
user_logger.info("User logged in")

# With PYIO for span timing
from pyfecto.pyio import PYIO

def database_query():
    # Simulate database operation
    return {"result": "success"}

effect = PYIO.log_span(
    name="db-query",
    log_msg="Database query execution",
    operation=PYIO.attempt(database_query)
)

# Run the effect - this will log timing information
result = effect.run()
```

## Real World Example

Here's a more complex example showing how to handle database operations:

```python
from dataclasses import dataclass
from typing import Optional
from pyfecto.pyio import PYIO

@dataclass
class User:
    id: int
    name: str

class DatabaseError(Exception):
    pass

def get_user(user_id: int):
    try:
        # Simulate DB lookup
        if user_id == 1:
            return PYIO.success(User(1, "Alice"))
        return PYIO.success(None)
    except Exception as e:
        return PYIO.fail(DatabaseError(str(e)))

def update_user(user: User, new_name: str):
    try:
        # Simulate DB update
        return PYIO.success(User(user.id, new_name))
    except Exception as e:
        return PYIO.fail(DatabaseError(str(e)))

# Usage
def rename_user(user_id: int, new_name: str):
    return (
        get_user(user_id)
        .flat_map(lambda maybe_user: 
            PYIO.success(None) if maybe_user is None
            else update_user(maybe_user, new_name)
        )
    )

# Run it
result = rename_user(1, "Alicia").run()
```

## Error Handling Patterns

Pyfecto provides several ways to handle errors:

1. **Recovery with default**:
```python
from pyfecto.pyio import PYIO

effect.recover(lambda err: PYIO.success(default_value))
```

2. **Transformation**:
```python
effect.match(
    lambda err: f"Failed: {err}",
    lambda value: f"Success: {value}"
)
```

3. **Branching logic**:
```python
effect.match_pyio(
    lambda value: handle_success(value),
    lambda err: handle_error(err)
)
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.


## Code of Conduct
All contributors are expected to maintain a professional and respectful environment. Technical discussions should focus on the merits of the ideas presented.
Be constructive in feedback, back technical opinions with examples or explanations, and remember that new contributors are learning. 
Repeated disruptive behavior will result in removal from the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.