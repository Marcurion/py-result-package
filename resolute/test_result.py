from pickletools import read_uint2

import pytest
import traceback
from typing import List

from resolute import Resolute

def results_in_int() -> Resolute[int]:
    res : Resolute[int] = Resolute.from_value(1)
    return res

def results_in_float() -> Resolute[float]:
    int_result: Resolute[int] = results_in_int() # Mypy needed to hint at the issue of returning this directly
    if int_result.has_errors: return int_result.generic_error_typed()
    # Else continue with business logic
    return Resolute.type_adjusted(int_result, lambda value: float(str(value))) # Lamda needs to consider possibility of None value

def results_in_none() -> Resolute[None]:
    return Resolute.from_value(None)

def results_in_list() -> Resolute[List[int]]:
    listing = [1,2,3]
    return Resolute.from_value(listing)

def test_init():
    success_with_value : Resolute[str] = Resolute.from_value("Hello")  # type: ignore

    assert success_with_value.value == "Hello"
    assert success_with_value.has_value == True
    assert success_with_value.has_errors == False
    assert success_with_value.value_is_of_type(str) == True
    assert success_with_value.is_success == True

    failure : Resolute[str] = Resolute.from_error("My error message")  # type: ignore
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
    success_without_value = Resolute.from_success_with_no_value() # same as Result.from_value(None)
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

    failure_collection = [Resolute.from_error("Err1"), Resolute.from_error(ValueError("Incorrect Value")), Resolute.from_errors(["Err2", "Err3", ZeroDivisionError()])]
    assert Resolute.any_erroneous_in_list(failure_collection)
    failure_from_collection = Resolute.from_erroneous_list(failure_collection)
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
        converted_exception = Resolute.from_error(traceback.format_exc())
        assert len(converted_exception.concat_errors()) > 25 # Has exception details

    from resolute import Result, has_errors, is_success, Success
    res: Result[int] = Resolute.from_value(1)
    res2: Result = Resolute.from_error("Error")
    res3: Result[int] = Resolute.from_error("Error")
    assert res2.is_success == False
    assert res3.has_errors
    assert has_errors(res3)
    assert is_success(res)
    assert isinstance(res.value, int)
    assert type(res) == Success


test_init()
print("All tests passed")


# =============================================================================
# Functional programming method tests
# =============================================================================

import asyncio


# --- map ---

def test_map():
    assert Resolute.from_value(2).map(lambda x: x * 3).value == 6
    assert Resolute.from_value("3").map(int).value == 3
    assert Resolute.from_error("bad").map(lambda x: x * 3).has_errors
    assert Resolute.from_value("abc").map(int).has_errors  # fn raises ValueError


# --- async_map ---

def test_async_map():
    async def double(x: int) -> int:
        return x * 2

    async def run():
        assert (await Resolute.from_value(3).async_map(double)).value == 6
        assert (await Resolute.from_error("bad").async_map(double)).has_errors

    asyncio.run(run())


# --- map_err ---

def test_map_err():
    result = Resolute.from_error("low-level error").map_err(lambda es: [f"domain: {es[0]}"])
    assert result.errors == ["domain: low-level error"]
    assert Resolute.from_value(1).map_err(lambda es: ["x"]).value == 1


# --- and_then ---

def test_and_then():
    def parse_int(s: str) -> Resolute:
        try:
            return Resolute.from_value(int(s))
        except ValueError as e:
            return Resolute.from_error(e)

    assert Resolute.from_value("42").and_then(parse_int).value == 42
    assert Resolute.from_value("bad").and_then(parse_int).has_errors
    assert Resolute.from_error("upstream").and_then(parse_int).has_errors


# --- async_and_then ---

def test_async_and_then():
    async def fetch_user(user_id: int) -> Resolute:
        if user_id > 0:
            return Resolute.from_value(f"user:{user_id}")
        return Resolute.from_error("invalid id")

    async def run():
        r = await Resolute.from_value(1).async_and_then(fetch_user)
        assert r.value == "user:1"

        r = await Resolute.from_value(-1).async_and_then(fetch_user)
        assert r.has_errors

        r = await Resolute.from_error("upstream").async_and_then(fetch_user)
        assert r.has_errors

    asyncio.run(run())


# --- fold ---

def test_fold():
    msg = Resolute.from_value(5).fold(lambda es: "err", lambda v: f"ok:{v}")
    assert msg == "ok:5"

    msg = Resolute.from_error("oops").fold(lambda es: f"failed:{es[0]}", lambda v: "ok")
    assert msg == "failed:oops"


# --- unwrap_or ---

def test_unwrap_or():
    assert Resolute.from_value(10).unwrap_or(0) == 10
    assert Resolute.from_error("fail").unwrap_or(0) == 0


# --- unwrap_or_else ---

def test_unwrap_or_else():
    assert Resolute.from_value(10).unwrap_or_else(lambda es: -1) == 10
    assert Resolute.from_error("oops").unwrap_or_else(lambda es: len(es)) == 1


# --- async_unwrap_or_else ---

def test_async_unwrap_or_else():
    async def fetch_default(errors: list) -> int:
        return -1

    async def run():
        assert (await Resolute.from_value(10).async_unwrap_or_else(fetch_default)) == 10
        assert (await Resolute.from_error("oops").async_unwrap_or_else(fetch_default)) == -1

    asyncio.run(run())


# --- inspect / inspect_err ---

def test_inspect():
    log = []
    result = Resolute.from_value(7).inspect(lambda v: log.append(v))
    assert log == [7]
    assert result.value == 7

    log = []
    result = Resolute.from_error("e").inspect_err(lambda es: log.extend(es))
    assert log == ["e"]
    assert result.has_errors

    log = []
    Resolute.from_error("e").inspect(lambda v: log.append(v))
    assert log == []

    log = []
    Resolute.from_value(1).inspect_err(lambda es: log.extend(es))
    assert log == []


# --- filter ---

def test_filter():
    assert Resolute.from_value(5).filter(lambda x: x > 0, "must be positive").value == 5
    assert Resolute.from_value(-1).filter(lambda x: x > 0, "must be positive").has_errors
    assert Resolute.from_error("upstream").filter(lambda x: x > 0, "irrelevant").has_errors


# --- async_filter ---

def test_async_filter():
    async def is_available(name: str) -> bool:
        return name != "taken"

    async def run():
        r = await Resolute.from_value("free").async_filter(is_available, "name taken")
        assert r.value == "free"

        r = await Resolute.from_value("taken").async_filter(is_available, "name taken")
        assert r.has_errors

        r = await Resolute.from_error("upstream").async_filter(is_available, "irrelevant")
        assert r.has_errors

    asyncio.run(run())


# --- zip ---

def test_zip():
    r = Resolute.zip(Resolute.from_value(1), Resolute.from_value("a"))
    assert r.value == (1, "a")

    r = Resolute.zip(Resolute.from_error("x"), Resolute.from_value(2))
    assert r.has_errors

    r = Resolute.zip(Resolute.from_error("x"), Resolute.from_error("y"))
    assert len(r.errors) == 2


# --- sequence ---

def test_sequence():
    r = Resolute.sequence([Resolute.from_value(1), Resolute.from_value(2)])
    assert r.value == [1, 2]

    r = Resolute.sequence([Resolute.from_value(1), Resolute.from_error("bad")])
    assert r.has_errors

    r = Resolute.sequence([Resolute.from_error("a"), Resolute.from_error("b")])
    assert len(r.errors) == 2

    r = Resolute.sequence([])
    assert r.value == []


# --- from_call ---

def test_from_call():
    assert Resolute.from_call(lambda: int("42")).value == 42
    assert Resolute.from_call(lambda: int("bad")).has_errors
    assert Resolute.from_call(lambda: int("bad")).contains_error_type(ValueError)


# --- from_async_call ---

def test_from_async_call():
    async def boom():
        raise ValueError("network error")

    async def run():
        r = await Resolute.from_async_call(boom)
        assert r.has_errors
        assert r.contains_error_type(ValueError)

    asyncio.run(run())