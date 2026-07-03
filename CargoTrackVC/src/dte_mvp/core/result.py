"""Result pattern for explicit error handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Represents the result of an operation that may fail.

    Follows the Railway Oriented Programming pattern.
    """

    value: T | None = None
    error: E | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None

    @property
    def is_failure(self) -> bool:
        return self.error is not None

    @classmethod
    def success(cls, value: T) -> Result[T, E]:
        return cls(value=value, error=None)

    @classmethod
    def failure(cls, error: E) -> Result[T, E]:
        return cls(value=None, error=error)

    def unwrap(self) -> T:
        if self.error is not None:
            raise self.error
        if self.value is None:
            raise ValueError("Result has no value")
        return self.value

    def map(self, fn: callable) -> Result:
        if self.is_failure:
            return self
        return Result.success(fn(self.value))

    def bind(self, fn: callable) -> Result:
        if self.is_failure:
            return self
        return fn(self.value)


