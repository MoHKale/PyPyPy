"""RequestMixin includes simple request methods and a shared session instance
so any implementing classes can make requests in a consistent reliable format.

If you don't want session instances to be shared between request classes, 
instead of using the auto created request_mixin.request_mixin.RequestMixin
use request_mixin.request_mixin.create_request_mixin() to create a new un-
related request mixin class.
"""

from requests import Session
from bs4 import BeautifulSoup as BS4
from .decorators.sewd import SegmentExecutionWithDelay
from .decorators.repeat_upon_error import RepeatUponError

from wrap_logger.logger import Logger as WrapLogger

from requests.exceptions import (
    ChunkedEncodingError, ConnectTimeout,
    ConnectionError, HTTPError, ReadTimeout, 
    RequestException, Timeout, TooManyRedirects
)

request_exceptions = [
    ChunkedEncodingError, ConnectTimeout,
    ConnectionError, HTTPError, ReadTimeout, 
    RequestException, Timeout, TooManyRedirects
]

def create_request_mixin(**kwargs):
    """Method To Create Request Mixin Class With Shared Session Instance Used
    By Each Class Which Implements The Mixin. This Function Allows Assignment 
    Of Default Request Arguments via Specified Keyword Arguments.
    
    Parameters
    ----------
    check_status_code : bool
        Default Value For whether Request Status Codes Are Automatically Checked.
    update_referrer : str
        Default Referrer Value Assigned Upon Each Request, Set To None to Ignore.
    soup_parser : str
        Default Parser Used By BeautifulSoup. Defaults To html.parser
    request_method : str || Callable
        Default Request Method Used When No Request Method Is Explicitly Given.
        Defaults To the GET method of the session instance bound to the mixin.
    request_delay : int
        Default Interval Between Subsequent Requests. Defaults to 0. Implemented
        using request_mixin.decorators.SegmentExecutionWithDelay therefore delay 
        can be changed in the returned mixin by setting
        
        >>> RequestMixin.make_request.delay = input('New Delay Value :> ')
        
        or
        
        >>> create_request_mixin().make_request.delay = input('New Delay Value :> ')
    max_attempt_count : int
        Maximum number of times a request can be made when an error is encountered.
    """
    
    default_check_status_code = kwargs.pop('check_status_code', False)
    default_referrer          = kwargs.pop('update_referrer', None)
    default_soup_parser       = kwargs.pop('soup_parser', 'html.parser')
    default_request_method    = kwargs.pop('request_method', None)
    default_delay_between_requests = kwargs.pop('request_delay', 0)
    default_repeat_on_request_error = kwargs.pop('max_attempt_count', 5)
    logger = kwargs.pop('logger', WrapLogger(__name__))
    
    class RequestMixin(object):
        """Method To Perform A Request To A Given URL With The Given Arguments &
        Keyword Arguments. Note, Some Keyword Arguments Are Used Explicitly By The
        Method Itself & Will Not Be Passed In The Request To The Given.
        
        Parameters
        ----------
        check_status_code : bool
            Whether an error should be raised if the recieved reponse does not have a
            200 status code.
        update_referrer : str
            Updates referrer to this value when method is executed, note if a default
            referrer was specified in the initial call to create_request_mixin, the
            referrer will be reset to that default value in the next call to make request
            unless a explicit referrer is again passed to the method.
        request_method : str || Callable
            Explicit Request Method Which Should Be Used By To Make The Request, Defaults
            to self.session.get .
        """
        @logger.wrap__entry(new_name='Making Request', include_params=True)
        @RepeatUponError.repeat(default_repeat_on_request_error, request_exceptions)
        @SegmentExecutionWithDelay.delay(default_delay_between_requests)
        def make_request(self, url, *args, **kwargs):
            #region Kwarg Extraction
            check_status_code = kwargs.pop('check_status_code', default_check_status_code)
            update_referrer   = kwargs.pop('update_referrer', default_referrer)
            request_method    = kwargs.pop('request_method', 
                default_request_method if default_request_method else self.session.get
            )
            #endregion
            
            #region Pre-Request-Actions
            if isinstance(request_method, str): # try cast string to session callable
                try: request_method = getattr(self.session, request_method.lower())
                except ValueError:
                    raise ValueError(f'Unknown Request Method {request_method}')
            
            if update_referrer and self.session.headears.get('referrer', None) != update_referrer:
                self.session.headears['referrer'] = update_referrer # assign when different
            #endregion
            
            #region Make Request
            formatted_a_kw = logger.format_params(*args, **kwargs) # format params
            logger.debug(f'Making Request To Url "{url}" With {formatted_a_kw}')
            response = request_method(url, *args, **kwargs) # store request response
            logger.debug(f'Response Recieved With Status {response.status_code}')
            #endregion
            
            #region Post-Request-Actions
            if check_status_code: response.raise_for_status()
            #endregion
            
            return response # give back acceptable request response
            
        def make_soup_request(self, url, *args, **kwargs):
            """Makes A Request To A Given URL & Converts The Response Text To A 
            bs4.BeautifulSoup Instance.
            
            WARNING: request status codes should be considered to not automatically
            be checked so it is highly suggested that you explicitly pass the kwarg
            check_status_code with a truthy value to ensure it is checked.
            
            See Also: help(self.make_request)
            
            Parameters
            ----------
            soup_parser : str
                Explicit Parser To Be Used By The BeautifulSoup Instance
            
            """
            return BS4(
                self.make_request(url, *args, **kwargs).text, 
                kwargs.pop('soup_parser', default_soup_parser)
            )
            
        def make_json_request(self, url, *args, **kwargs):
            """Makes A Request To A Given URL & Interprets The Response As JSON

            See Also: help(self.make_request)"""
            return self.make_request(url, *args, **kwargs).json()
            
        session = Session() # create new session instance as class level reference
    
    return RequestMixin
