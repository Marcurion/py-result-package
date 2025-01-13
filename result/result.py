
from typing import Generic, TypeVar, Union

T = TypeVar("T")


class Result(Generic[T]):
    """Represents the outcome of an operation.

    Attributes
    ----------
    success : bool
        A flag that is set to True if the operation was successful, False if
        the operation failed.
    """

    #    @overload
    #    def __init__(self, success: bool, value: T) -> None: ...

    #    @overload
    #    def __init__(self, success: bool, error: str) -> None: ...

    def __init__(self, success: bool, value_or_error: Union[T, str]):
        self._success: bool = success
        self._value_or_error: Union[T, str] = value_or_error

    @property
    def success(self) -> bool:
        """True if operation was successful, False if it failed."""
        return self._success

    @property
    def failure(self) -> bool:
        """True if operation failed, False if successful (read-only)."""
        return not self._success

    @property
    def value(self) -> T:
        """The result of the operation if successful."""
        if not self._success:
            raise ValueError("Cannot access value on a failed Result")
        assert not isinstance(self._value_or_error, str)
        return self._value_or_error

    @property
    def error(self) -> str:
        """Error message detailing why the operation failed."""
        if self._success:
            raise ValueError("Cannot access error on a successful Result")
        assert isinstance(self._value_or_error, str)
        return self._value_or_error

    def __str__(self) -> str:
        if self._success:
            return f"[Success]"
        else:
            return f'[Failure] "{self._value_or_error}"'

    def __repr__(self) -> str:
        if self._success:
            return f"<Result success={self._success}>"
        else:
            return f'<Result success={self._success}, message="{self._value_or_error}">'

    @classmethod
    def fail(cls, error: str) -> "Result[T]":
        """Create a Result object for a failed operation."""
        return cls(False, error)

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create a Result object for a successful operation."""
        return cls(True, value)


