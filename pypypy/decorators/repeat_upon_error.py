from functools import wraps, update_wrapper
import time

class StoredExceptionArray(Exception):
    """Stores an Ordered Collection of Raised Exceptions"""
    pass

class RepeatUponError(object):
    """Class Decorator To Allow Repeat Function Execution
    
    Parameters
    ----------
    func
        Function bound to decorator
    attempt_count : int
        Maximum number of times to attempt function when repeatable error encountered.
    repeat_exception_types : Exception[]
        List of exceptions which will be caught & ignored by function. If None or non-
        truthy value all exceptions will be caught and ignored.
    
    Note: Call as a decorator using the 'repeat' class method."""
    def __init__(self, func, attempt_count: int, repeat_exception_types=None):
        update_wrapper(self, func)
        
        if attempt_count <= 0: # Validate Attempt Count Argument
            raise ValueError(f'Attempt Count Must Be > 0, Not {attempt_count}')
        
        self.func = func # store arguments
        self.attempt_count = attempt_count
        
        self.repeat_exception_types = repeat_exception_types
        
    def __call__(self, *args, **kwargs):
        error_container = [] # will store raised exceptions
        
        for X in range(0, self.attempt_count):
            try:
                return self.func(*args, **kwargs)
            except (Exception, KeyboardInterrupt) as e:
                error_container.append(e) # store current error in container
                
                skip = self.repeat_exception_types or e.__class__ in self.repeat_exception_types
                # skip when no repeat types given or exception contained in repeat types
                
                if not(skip) or X == self.attempt_count - 1:
                    # raise regardless of skip when last attempt
                    raise StoredExceptionArray(error_container)
    
    @classmethod
    def repeat(cls, count: int, repeat_exception_types=None):
        def decorator(func):
            return cls(func, count, repeat_exception_types)
        return decorator
            