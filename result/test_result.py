import pytest
import traceback
from typing import List

from result import Result

def results_in_int() -> Result[int]:
    res : Result[int] = Result.from_value(1)
    return res

def results_in_float() -> Result[float]:
    int_result: Result[int] = results_in_int() # Mypy needed to hint at the issue of returning this directly
    if int_result.has_errors: return int_result.generic_error_typed()
    # Else continue with business logic
    return Result.type_adjusted(int_result, lambda value: float(str(value)) ) # Lamda needs to consider possibility of None value

def results_in_none() -> Result[None]:
    return Result.from_value(None)

def results_in_list() -> Result[List[int]]:
    listing = [1,2,3]
    return Result.from_value(listing)

def test_init():
    success_with_value : Result[str] = Result.from_value("Hello")  # type: ignore

    assert success_with_value.value == "Hello"
    assert success_with_value.has_value == True
    assert success_with_value.has_errors == False
    assert success_with_value.value_is_of_type(str) == True
    assert success_with_value.is_success == True

    failure : Result[str] = Result.from_error("My error message")  # type: ignore
    assert failure.has_value == False
    assert failure.has_errors == True
    assert len(failure.errors) == 1
    assert failure.errors[0] == "My error message"

    failure.with_error("My 2nd error message")
    assert failure.has_value == False
    assert failure.has_errors == True
    assert len(failure.errors) == 2
    assert failure.errors[0] == "My error message"
    assert failure.errors[1] == "My 2nd error message"
    assert failure.concat_errors("&") == "My error message&My 2nd error message"
    assert isinstance(failure.errors[0], str)
    assert not isinstance(failure.errors[0], Exception)
    with pytest.raises(ValueError) as caught_exception:
        print(failure.value)
    assert str(caught_exception.value) == "Cannot access value on a failed Result"
    assert failure.contains_error_type(ValueError) == False

    failure.with_errors(["My 3rd error message", ValueError("4th")])
    assert failure.has_value == False
    assert failure.has_errors == True
    assert len(failure.errors) == 4
    assert isinstance(failure.errors[3], Exception)
    assert isinstance(failure.errors[3], ValueError)
    assert str(failure.errors[3]) == "4th"
    assert failure.contains_error_type(ValueError) == True
    assert failure.contains_error_type(Exception) == True
    assert failure.contains_error_type(ZeroDivisionError) == False
    assert failure.contains_error_type(str) == True
    assert failure.contains_error_type(int) == False

    class MyError(Exception):
        pass

    assert failure.contains_error_type(MyError) == False
    failure.with_error(MyError("5th"))
    assert failure.contains_error_type(MyError) == True

    #assert type(results_in_float()) == Result[int]
    assert results_in_float().value_is_of_type(float) == True
    assert results_in_float()._type == float
    assert results_in_none().value_is_of_type(type(None)) == True
    assert results_in_none()._type == type(None)

    # success_with_value.value = 2 # TODO: Setter for value
    success_without_value = Result.from_success_with_no_value() # same as Result.from_value(None)
    assert success_without_value.has_value == False
    assert success_without_value.has_errors == False
    assert success_without_value.value is None
    assert success_without_value.is_success == True

    assert results_in_list().is_success == True
    assert results_in_list().has_value == True
    assert len(results_in_list().value) == 3
    assert results_in_list().value[1] == 2
    #assert results_in_list().value_is_of_type(List[int]) == True # Generic types are flattened at runtime
    assert results_in_list().value_is_of_type(List) == True

    failure_collection = [Result.from_error("Err1"), Result.from_error(ValueError("Incorrect Value")), Result.from_errors(["Err2", "Err3", ZeroDivisionError()])]
    assert Result.any_erroneous_in_list(failure_collection)
    failure_from_collection = Result.from_erroneous_list(failure_collection)
    assert failure_from_collection.has_value == False
    assert failure_from_collection.is_success == False
    assert failure_from_collection.has_errors == True
    assert len(failure_from_collection.errors) == 5
    assert failure_from_collection.errors[0] == "Err1"
    assert failure_from_collection.contains_error_type(ValueError) == True
    assert failure_from_collection.contains_error_type(ZeroDivisionError) == True
    assert failure_from_collection.concat_errors().startswith("Err1")
    assert failure_from_collection.value_is_of_type(type(None)) == True
    assert len(failure_from_collection.with_error(Exception()).errors) == 6

    try:
        1 / 0
    except:
        #traceback.print_exc()
        converted_exception = Result.from_error(traceback.format_exc())
        assert len(converted_exception.concat_errors()) > 25 # Has exception details


