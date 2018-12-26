import time, functools

def segment_execution_with_delay(delay_attribute: str):
    """Delays Sequential Execution of a Given Function by a Given Attribute

    Functions by calculating interval between function calls to whatever
    this decorates and then waiting for the difference between that period
    and the delay which must be waited between calls.

    The time taken for the function to run/evaluate will not be included
    in the wait period required between function calls.

    Parameters
    ----------
    delay_attribute : str
        Name of attribute in current class which is considered to be the 
        delay this function should use. When the delay attribute is not
        found in the self instance passed to this function, then an error
        is raised.
    """
    def try_get_delay(self):
        # Attempts to extract delay from class instance or throws an error when thats not possible
        if not(hasattr(self, delay_attribute)): # when class doesn't have the required attribute
            raise ValueError(f"Class {self} Doesn't Possess The Delay Attribute '{delay_attribute}'")
        
        return getattr(self, delay_attribute)

    def delay_for(delay, last_executed):
        """Calculate and return the actual interval which should be 
        waited for (in seconds).

        Parameters
        ----------
        delay : int
            Delay this decorator is expected to maintain.
        last_executed : Union['time', None]
            Last Point Time when this function was run.

        Returns
        -------
        Time to wait. Will be -1 if no wait is expected.

        """
        time_difference = None

        if not(last_executed): return -1 # no delay
        else: 
            time_difference = time.time() - last_executed
            
            if time_difference >= delay:
                return -1 # also no delay
            
            return delay - time_difference # delay span

    def decorator(func):
        last_executed = {'value':None} # stores time value reference

        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            delay_value = try_get_delay(self) # extract actual delay value
            delay_span  = delay_for(delay_value, last_executed['value'])
            if delay_span > 0: time.sleep(delay_span) # only delay when +ve
            
            return_value = func(self, *args, **kwargs)
            last_executed['value'] = time.time()
            return return_value # executed function
        
        return wrapped
    return decorator
