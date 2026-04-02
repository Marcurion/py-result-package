
from typing import Any, Generic, TypeVar, Union, List, Callable, TypeIs, Awaitable

T = TypeVar("T")
U = TypeVar("U")
A = TypeVar("A")
B = TypeVar("B")

class Resolute(Generic[T]):

    def __init__(self, success: bool, value: Union[T, None] = None, errors: List[Union[Exception, str]] | None = None) -> None:
        self._success: bool = success
        self._value: Union[T, None] = value
        self._errors: List[Union[Exception, str]] = errors or []
        self._type: type = type(value)

    @property
    def is_success(self) -> bool:
        """True if operation was successful, False if it failed. """
        return self._success

    @property
    def has_value(self) -> bool:
        """True if operation was successful, False if it failed or value is None."""
        if self._value is None: return False
        return self._success

    @property
    def has_errors(self) -> bool:
        """True if operation failed, False if successful (read-only)."""
        return not self._success

    @property
    def value(self) -> T | None:
        """The result of the operation if successful."""
        if not self._success:
            raise ValueError("Cannot access value on a failed Result")
        #assert isinstance(self._value, T)
        return self._value

    @property
    def _(self) -> T | None:
        """Alias for .value."""
        return self.value

    @property
    def errors(self) -> List[Union[Exception, str]]:
        """Error message detailing why the operation failed."""
        if self._success:
            raise ValueError("Cannot access error on a successful Result")
        #assert isinstance(self._errors, List[Union[str, Exception]])
        return self._errors

    def value_is_of_type(self, expected_type: type) -> bool:
        return issubclass(self._type, expected_type)

    def concat_errors(self, separator='\n') -> str:
        if self._success:
            raise ValueError("Cannot access error on a successful Result")
        #assert isinstance(self._errors, List[Union[str, Exception]])
        return separator.join(str(error) for error in self._errors)

    def with_errors(self, errors: List[Union[Exception, str]]) -> "Failure[T]":
        if self._success:
            return Failure(False, value=self.value, errors=errors)
        else:
            self._errors += errors
            return self  # type: ignore[return-value]

    def with_error(self, error: Union[Exception, str]) -> "Failure[T]":
        return self.with_errors([error])

    def contains_error_type(self, error_type: type) -> bool:
        """Check if _errors contains an error of the given type.

        Args:
            error_type (type): The type of error to check for (e.g., ValueError).

        Returns:
            bool: True if an error of the specified type exists, False otherwise.
        """
        return any(isinstance(error, error_type) for error in self._errors)

    # -------------------------------------------------------------------------
    # Functional programming methods
    # -------------------------------------------------------------------------

    def map(self, fn: Callable[[T], U]) -> "Success[U] | Failure[U]":
        """Transform the success value; pass failures through unchanged."""
        if not self._success:
            return self  # type: ignore[return-value]
        try:
            return Resolute.from_value(fn(self._value))  # type: ignore[arg-type]
        except Exception as e:
            return Resolute.from_error(e)

    async def async_map(self, fn: Callable[[T], Awaitable[U]]) -> "Success[U] | Failure[U]":
        """Async variant of map."""
        if not self._success:
            return self  # type: ignore[return-value]
        try:
            return Resolute.from_value(await fn(self._value))  # type: ignore[arg-type]
        except Exception as e:
            return Resolute.from_error(e)

    def map_err(self, fn: Callable[[List[Union[Exception, str]]], List[Union[Exception, str]]]) -> "Success[T] | Failure[T]":
        """Transform the error list; pass successes through unchanged."""
        if self._success:
            return self  # type: ignore[return-value]
        return Resolute.from_errors(fn(self._errors))

    def and_then(self, fn: Callable[[T], "Success[U] | Failure[U]"]) -> "Success[U] | Failure[U]":
        """Chain a fallible operation (flatmap); pass failures through unchanged."""
        if not self._success:
            return self  # type: ignore[return-value]
        return fn(self._value)  # type: ignore[arg-type]

    async def async_and_then(self, fn: Callable[[T], Awaitable["Success[U] | Failure[U]"]]) -> "Success[U] | Failure[U]":
        """Async variant of and_then."""
        if not self._success:
            return self  # type: ignore[return-value]
        return await fn(self._value)  # type: ignore[arg-type]

    def fold(self, on_failure: Callable[[List[Union[Exception, str]]], U], on_success: Callable[[T], U]) -> U:
        """Terminal operation: consume the result by providing handlers for both branches."""
        if self._success:
            return on_success(self._value)  # type: ignore[arg-type]
        return on_failure(self._errors)

    def unwrap_or(self, default: T) -> T:
        """Return the value on success, or a static default on failure."""
        if self._success:
            return self._value  # type: ignore[return-value]
        return default

    def unwrap_or_else(self, fn: Callable[[List[Union[Exception, str]]], T]) -> T:
        """Return the value on success, or compute a fallback from the errors (lazy)."""
        if self._success:
            return self._value  # type: ignore[return-value]
        return fn(self._errors)

    async def async_unwrap_or_else(self, fn: Callable[[List[Union[Exception, str]]], Awaitable[T]]) -> T:
        """Async variant of unwrap_or_else."""
        if self._success:
            return self._value  # type: ignore[return-value]
        return await fn(self._errors)

    def inspect(self, fn: Callable[[T], None]) -> "Success[T] | Failure[T]":
        """Call fn(value) for side effects on success; always return self."""
        if self._success:
            fn(self._value)  # type: ignore[arg-type]
        return self  # type: ignore[return-value]

    def inspect_err(self, fn: Callable[[List[Union[Exception, str]]], None]) -> "Success[T] | Failure[T]":
        """Call fn(errors) for side effects on failure; always return self."""
        if not self._success:
            fn(self._errors)
        return self  # type: ignore[return-value]

    def filter(self, predicate: Callable[[T], bool], error: Union[Exception, str]) -> "Success[T] | Failure[T]":
        """Conditionally fail a success if the predicate returns False."""
        if not self._success:
            return self  # type: ignore[return-value]
        if predicate(self._value):  # type: ignore[arg-type]
            return self  # type: ignore[return-value]
        return Resolute.from_error(error)

    async def async_filter(self, predicate: Callable[[T], Awaitable[bool]], error: Union[Exception, str]) -> "Success[T] | Failure[T]":
        """Async variant of filter."""
        if not self._success:
            return self  # type: ignore[return-value]
        if await predicate(self._value):  # type: ignore[arg-type]
            return self  # type: ignore[return-value]
        return Resolute.from_error(error)

    @classmethod
    def zip(cls, a: "Resolute[A]", b: "Resolute[B]") -> "Success[tuple] | Failure[tuple]":
        """Combine two results into a tuple; aggregate errors if either fails."""
        if a._success and b._success:
            return cls.from_value((a._value, b._value))
        all_errors: List[Union[Exception, str]] = []
        if not a._success:
            all_errors.extend(a._errors)
        if not b._success:
            all_errors.extend(b._errors)
        return cls.from_errors(all_errors)

    @classmethod
    def sequence(cls, results: List["Resolute[T]"]) -> "Success[List[T]] | Failure[List[T]]":
        """Collect a list of results into a result of a list; aggregate all errors on failure."""
        if not results:
            return cls.from_value([])
        all_errors: List[Union[Exception, str]] = []
        for r in results:
            if not r._success:
                all_errors.extend(r._errors)
        if all_errors:
            return cls.from_errors(all_errors)
        return cls.from_value([r._value for r in results])  # type: ignore[misc]

    @classmethod
    def from_call(cls, fn: Callable[[], T]) -> "Success[T] | Failure[T]":
        """Wrap a callable that may raise; returns Success or Failure."""
        try:
            return cls.from_value(fn())
        except Exception as e:
            return cls.from_error(e)

    @classmethod
    async def from_async_call(cls, fn: Callable[[], Awaitable[T]]) -> "Success[T] | Failure[T]":
        """Wrap an async callable that may raise; returns Success or Failure."""
        try:
            return cls.from_value(await fn())
        except Exception as e:
            return cls.from_error(e)

    # -------------------------------------------------------------------------
    # End functional programming methods
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        if self._success:
            return f'[Success] "{self._value}"'
        else:
            return f'[Failure] "{self.concat_errors()}"'

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_errors(cls, errors: List[Union[str, Exception]]) -> "Failure[T]":
        """Create a Result object for a failed operation. With multiple error information"""
        return Failure(False, errors=errors)

    @classmethod
    def from_error(cls, error: Union[str, Exception]) -> "Failure[T]":
        """Create a Result object for a failed operation."""
        return Failure(False, errors=[error])

    @classmethod
    def from_value(cls, value: T) -> "Success[T]":
        """Create a Result object for a successful operation with value."""
        return Success(True, value)

    @classmethod
    def from_success_with_no_value(cls) -> "Success[T]":
        """Create a Result object for a successful operation without value."""
        return Success(True, None)

    @staticmethod
    def type_adjusted(source: "Resolute[T]", value_converter: Callable[[T | None], U]) -> "Success[U] | Failure[U]":
        if source.is_success and source.has_value:
            try:
                return Resolute.from_value(value_converter(source.value))
            except Exception as e:
                return Resolute.from_error(e)
        else:
            return Resolute.from_errors(source.errors)


    @staticmethod
    def type_erroneous(source: "Resolute[T]") -> "Failure[Any]":
        if source.is_success:
            raise ValueError("This method should only be called on Results with errors, ensure proper checks upfront or consider using type_adjusted() and provide value_converter method")
        else:
            return Resolute.from_errors(source.errors)

    def generic_error_typed(self: "Resolute[T]") -> "Failure[Any]":
        return Resolute.type_erroneous(self)


    @staticmethod
    def any_erroneous_in_list(collection: List["Resolute[T]"]) -> bool:
        for collection_item in collection:
            if collection_item.has_errors:
                return True
        return False

    @staticmethod
    def from_erroneous_list(collection: List["Resolute[T]"]) -> "Resolute[T]":
        if not Resolute.any_erroneous_in_list(collection):
            raise ValueError("This method should only be called on a List with erroneous Results, ensure proper checks upfront")

        all_errors = []
        for collection_item in collection:
            if collection_item.has_errors:
                all_errors.extend(collection_item.errors)
        return Resolute.from_errors(all_errors)


def is_success(res: Resolute[T]) -> TypeIs["Success[T]"]:
    """Type guard: narrows Resolute[T] to Success[T] when True."""
    return res._success


def has_errors(res: Resolute[T]) -> TypeIs["Failure[T]"]:
    """Type guard: narrows Resolute[T] to Failure[T] when True."""
    return not res._success


class Success(Resolute[T]):
    @property
    def value(self) -> T:
        return self._value  # type: ignore[return-value]

    @property
    def _(self) -> T:
        return self._value  # type: ignore[return-value]


class Failure(Resolute[T]):
    pass


type Result[T] = Success[T] | Failure[T]
