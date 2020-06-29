import time, functools, dataclasses, logging
from typing import Tuple, Union, List, Callable, Dict

instance_field__num = Union[int, Tuple[str, int]]

@dataclasses.dataclass
class RepeatOnError(object):
    """decorator class allowing a function to be repeated a limited amount of times
    when an error is encountered during execution. If no error is encountered, no
    repeats are done.

    Also supports delaying the repeat execution after an error by some time, as
    specified either directly to this instance (as a numerical value), or through
    an some instance field in the wrapped objects method. See `attempt_count' and
    `interval_delay'.

    Parameters
    ----------
    func
        the callable that this class decorator is wrapping. should be an instance
        method which recieves an instance of the class as it's first argument.
    attempt_count
        how many consecutive times to try invoking `func`. can be a numerical value
        in which case that's how many times the function will be invoked, ALWAYS.
        alternatively, can be a tuple, in which case the first value is an attribute
        in the requester which specifies the `attempt_count` and the second is a
        fallback value used if the requester doesn't have that attribute.
    request_delay
        how long to wait after encountering an error before trying again. uses the
        same format as `attempt_count`.
    repeat_exception_types
        list of exception classes denoting which exceptions, if encountered, will not
        terminate the repeated attempts on `func`. if unspecified, any exceptions
        (excluding `KeyboardInterrupt`'s) will not stop repeat attempts.

    Notes
    -----
        the time span denoted by `request_delay` doesn't include however long it takes
        function to run. eg. if func takes 2 seconds to run and `request_delay` is 3,
        only 1 second will be waited.
    """
    func: Callable
    attempt_count: instance_field__num
    request_delay: instance_field__num
    repeat_exception_types: List[type]

    def __post_init__(self):
        functools.update_wrapper(self, self.func)

    def __call__(self, requester, *args, **kwargs):
        attempt_count = max(self._extract_attribute(requester, self.attempt_count), 1)
        request_delay = max(self._extract_attribute(requester, self.request_delay), 0)
        last_executed = {'time': None}  # remember when function was last delayed

        def recursively_invoke_func(attempt):
            try:
                return self.func(requester, *args, **kwargs)
            except KeyboardInterrupt: raise  # always raise
            except Exception as e:
                if self.repeat_exception_types and e.__class__ not in self.repeat_exception_types:
                    raise e  # unknown exception type has occured, let it take over control flow

                if attempt > 0:
                    time.sleep(self._delay_for(request_delay, last_executed))
                    return recursively_invoke_func(attempt-1)  # try again
                else:  # all attempts exhausted
                    logging.error('failed to make request after %03d attempts using %s with paramters: %s, %s' % (
                        attempt_count, requester, args, kwargs))

                    raise e

        return recursively_invoke_func(attempt_count-1)

    def _delay_for(self, delay_span, memory: Dict[str, int]):
        """Calculate and return the actual interval which should be
        waited for (in seconds).

        Returns
        -------
        Time to wait. Will be 0 if no wait is expected. """
        if 'time' not in memory.keys() or delay_span <= 0:
            return 0  # no delay, because no memory or no span
        else:
            now             = time.time()
            time_difference = (now - memory['time']) if memory['time'] is not None else 0
            memory['time']  = now

            return max(delay_span - time_difference, 0)

    def __get__(self, instance, owner):
        return functools.partial(self.__call__, instance)

    @classmethod
    def wrap(cls, *args, **kwargs):
        return lambda func: cls(func, *args, **kwargs)

    def _extract_attribute(self, instance, attribute):
        if isinstance(attribute, tuple):
            attribute, default = attribute

            if hasattr(instance, attribute):
                return getattr(instance, attribute)
            return default
        return attribute
