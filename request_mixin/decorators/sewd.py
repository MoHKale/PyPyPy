"""SegmentExecutionWithDelay Delays Sequential Execution of a Given Function"""

from functools import wraps, update_wrapper, partial
import time
    
class SegmentExecutionWithDelay(object):
    """Class Decorator To Allow A Minimum Wait Period Between Consecutive
    Function Calls. Lazy Evaluation, Delay Is Only Run When Desired Interval
    Hasn't Already Been Evaluated During Execution of Other Commands.
    
    Note: Call as a decorator using the 'delay' class method."""
    def __init__(self, func, delay):
        update_wrapper(self, func) # update instance attributes
        self.func, self.delay = func, delay # store attributes
        self._last_executed = None # Initialise with None
        
    def __str__(self):
        return '{0}<Name:{1}, Delay:{2}>()'.format(
            self.__class__.__name__, self.func.__name__, self.delay
        )
    
    def __call__(self, *args, **kwargs):
        #region: Delay Section Executor
        if not(self.ready): 
            time_elapsed = (time.time() - self._last_executed)
            delay_span = self.delay - time_elapsed # wait amount
            
            if delay_span > 0: time.sleep(delay_span) # only +ve
        #endregion
        
        return_value = self.func(*args, **kwargs)
        self._last_executed = time.time() # update
        return return_value # executed function
        
    def __get__(self, instance, owner):
        return partial(self.__call__, instance)
        
    @property
    def ready(self):
        return not(self._last_executed) or time.time() - self._last_executed >= self.delay
    
    @classmethod
    def delay(cls, delay,):
        def decorator(func):
            return cls(func, delay)
        return decorator