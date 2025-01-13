Simple implementation of the Result pattern similar to ErrorOr in C#. Using type safety and generics in Python.

Use like this:

@staticmethod
def use_method() -> Result[int]:
    res: Result[int] = return_int_or_error()

    if res.failure: 
        print("Oh no")
        return res
    else: 
        print("Oh yes")
        return Result.ok(res.value + 1)
