Resolute is a new way of thinking Python functions. For your mind, it is like error handling on autopilot.

The package is loosely inspired by .NETs ErrorOr package, with a stronger focus on returning early in your code, reducing nesting, improving readability and understandability of your code base and avoiding exception handling. Resolute supports layered architecture with a clear separation of concerns and improves pinpointing of errors at a glance.

Imagine reading the following error history in your hexagon architecture project:

>“List all users API request failed“
>
>“Application could not retrieve all users“
>
>“User repository failed to fetch users“
>
>“MySQL DB adapter could not establish a connection on {192.168.0.127:500}“
>
>“NetworkError: TLS handshake refused, certificate mismatch, terminating connection… {Exception Details}“

You will be able to immediately tell which operation failed, which path through your code-base was attempted and see technical failure details at the lowest level. 

You can construct your error histroy from generic strings or use typed error messages specifically for your domain, or pass in the exception classes we all already know.



```python
return Resolute.from_error("My attempt failed")
# or
return Resolute.from_error(ZeroDivisionError())
# or
class MyError(Exception):
        pass
return Resolute.from_error(MyError("What happened"))
# or
import traceback
try:
  1 / 0
except:
  return Resolute.from_error(traceback.format_exc())
``` 

Your application logic relies on the success of calls to (deeper) parts of the code-base? It can not complete the task once a necessary call fails? No further questions asked - streamline your business logic and return what you got: An error!



```python
def business_logic() -> Resolute[float]:
...
  current_res: Resolute[int] = Infrastructure.retrieve_count()
  if current_res.has_errors: return current_res.generic_error_typed().with_error("I can't complete what I was about to do")
  # if not continue business as normal
...
```
Did we mention Resolute was created with Python's type system in mind? Detect potential value type mismatches with your linter of choice. Fast-forward erroneous results or provide a converter function for results with values.



```python
def results_in_int() -> Resolute[int]:
  return Resolute.from_value(3)
def results_in_float() -> Resolute[float]:
  int_res: Resolute[int] = results_in_int()
  if int_res.has_errors:
    return int_res.generic_error_typed()           # : Resolute[float]
    # or
    return Resolute.type_erroneous(int_res)         # : Resolute[float]
  # Else success
  # Lambda converter needs to consider possibility of None value
  return Resolute.type_adjusted(int_res, lambda value: float(str(value))*2.5 )
def also_ress_in_float() -> Resolute[float]:
  float_res: Resolute[float] = results_in_float()
  if float_res.has_errors: return float_res       # No conversion necessary
  return Resolute.from_value(float_res.value * 2.5)
def void_like_res() -> Resolute[None]:
  float_res: Resolute[float] = results_in_float()
  if float_res.is_success: return Resolute.from_success_with_no_value()
``` 

More complex example from a layered architecture:


```python
...
# Presentation layer
earliest_book_availability_res: Resolute[datetime] = reservation_service.calculate_book_availability(book_uuid)
if earliest_book_availability_res.has_errors: modal_manager.ShowError(earliest_book_availability_res.concat_errors())
...
...
# Application layer
def calculate_book_availability(book_uuid: str) -> Resolute[datetime]:
  # Get dependencies
  results: List[Resolute] = await asyncio.gather(
        async_check_if_book_is_in_store(book_uuid),
        async_get_return_date_of_last_borrower(book_uuid),
        async_get_waiting_list_for_book(book_uuid)
    ) 
  # Cumulative Error Handling
  if Resolute.any_erroneous_in_list(results):
    return Resolute.from_erroneous_list(results) # Optional: .with_error("Availability calculation failed")
  # Typing
  in_store_res: Resolute[bool]
  last_borrower_returned_res: Resolute[datetime]
  waiting_list_res: Resolute[List[User]]
  # Unpacking
  in_store_res, last_borrower_returned_res, waiting_list_res = results
  # Continue with business logic
...
...
# Infrastructure layer (using SQLAlchemy)
def retrieve_waiting_list_for_book_from_db(book_uuid: str) -> Resolute[List[User]]:
...
  try:
    book = session.query(Book).filter(Book.uuid == book_uuid).first()
  except:
    return Resolute.from_error(traceback.format_exc()) # Optional: .with_error("Book retrieval by UUID failed")
  # Success
  return Resolute.from_value(book.waiting_list)
... 
  ```