
from typing import Generic, TypeVar, Union, List, Callable

T = TypeVar("T")

# Alternative names: PassResult, HexagonResult, LayeredResult, DenestingResult, NestfulResult, RestlessResult, NestlessResult, ResultOr, ResOr, -ValOr-, SuccOr, -Outcome-, Upwards, -StepUp-, Stair, Rung, Straight, Around, Pack
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

    def with_errors(self, errors: List[Union[Exception, str]]) -> "Result[T]":
        if self._success:
            return Result(False, value=self.value, errors=errors)
        else:
            self._errors += errors
            return self

    def with_error(self, error: Union[Exception, str]) -> "Result[T]":
        return self.with_errors([error])

    def contains_error_type(self, error_type: type) -> bool:
        """Check if _errors contains an error of the given type.

        Args:
            error_type (type): The type of error to check for (e.g., ValueError).

        Returns:
            bool: True if an error of the specified type exists, False otherwise.
        """
        return any(isinstance(error, error_type) for error in self._errors)

    def __str__(self) -> str:
        if self._success:
            return f'[Success] "{self._value}"'
        else:
            return f'[Failure] "{self.concat_errors()}"'

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_errors(cls, errors: List[Union[str, Exception]]) -> "Result[T]":
        """Create a Result object for a failed operation. With multiple error information"""
        return cls(False, errors=errors)

    @classmethod
    def from_error(cls, error: Union[str, Exception]) -> "Result[T]":
        """Create a Result object for a failed operation."""
        return cls(False, errors=[error])

    @classmethod
    def from_value(cls, value: T) -> "Result[T]":
        """Create a Result object for a successful operation with value."""
        return cls(True, value)

    @classmethod
    def from_success_with_no_value(cls) -> "Result[T]":
        """Create a Result object for a successful operation without value."""
        return cls(True, None)

    U = TypeVar("U")

    @staticmethod
    def type_adjusted(source: "Result[T]", value_converter: Callable[[T | None], U]) -> "Result[U]":
        if source.is_success and source.has_value:
            try:
                return Result.from_value(value_converter(source.value))
            except Exception as e:
                return Result.from_error(e)
        else:
            return Result.from_errors(source.errors)


    @staticmethod
    def type_erroneous(source: "Result[T]") -> "Result[U]":
        if source.is_success:
            raise ValueError("This method should only be called on Results with errors, ensure proper checks upfront or consider using type_adjusted() and provide value_converter method")
        else:
            return Result.from_errors(source.errors)

    def generic_error_typed(self: "Result[T]") -> "Result[U]":
        return Result.type_erroneous(self)


    @staticmethod
    def any_erroneous_in_list(collection: List["Result[T]"]) -> bool:
        for collection_item in collection:
            if collection_item.has_errors:
                return True
        return False

    @staticmethod
    def from_erroneous_list(collection: List["Result[T]"]) -> "Result[T]":
        if not Result.any_erroneous_in_list(collection):
            raise ValueError("This method should only be called on a List with erroneous Results, ensure proper checks upfront")

        all_errors = []
        for collection_item in collection:
            if collection_item.has_errors:
                all_errors.extend(collection_item.errors)
        return Result.from_errors(all_errors)
