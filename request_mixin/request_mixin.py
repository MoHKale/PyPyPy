"""RequestMixin includes simple request methods and a shared session instance
so any implementing classes can make requests in a consistent reliable format.

If you don't want session instances to be shared between request classes, 
instead of using the auto created request_mixin.request_mixin.RequestMixin
use request_mixin.request_mixin.create_request_mixin() to create a new un-
related request mixin class.
"""

import json

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
    update_referer : str
        Default referer Value Assigned Upon Each Request, Set To None to Ignore.
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
        
    Example
    -------
    
    Using The create_request_mixin Method
    
        from request_mixin import create_request_mixin
        
        class B(create_request_mixin(), object):
            pass
            
        B().make_request('https://www.google.co.uk')
        
    Customising Default Request Behaviour Using create_request_mixin
    
        from request_mixin import create_request_mixin
        
        class C(
            create_request_mixin(
                request_method='POST',
                check_status_code=True,
                max_attempt_count=10,
                request_delay=3
            ), 
            object
        ):
            pass
            
        C().make_request('https://www.google.co.uk')
    """
    
    default_check_status_code       = kwargs.pop('check_status_code', False)
    default_referer                = kwargs.pop('update_referer', None)
    default_soup_parser             = kwargs.pop('soup_parser', 'html.parser')
    default_request_method          = kwargs.pop('request_method', None)
    default_delay_between_requests  = kwargs.pop('request_delay', 0)
    default_repeat_on_request_error = kwargs.pop('max_attempt_count', 5)
    logger                          = kwargs.pop('logger', WrapLogger(__name__))
    
    if len(kwargs) != 0:
        name = 'create_request_mixin' # name of current method. Include in error msg
        kwargs = json.dumps(list(kwargs.keys())).replace('[', '{').replace(']', '}')
        raise ValueError(f'{name} Recieved Some Unexpected Keyword Arguments {kwargs}')
    
    class RequestMixin(object):
        """Mixin class containing a single requests.Session instance shared alongside
        any implementing classes.
        
        Example
        -------
        
        Using The Module Level Global RequestMixin Instance
        
            from request_mixin import RequestMixin
        
            class A(RequestMixin, object):
                pass
        
            A().make_request('https://www.google.co.uk')
            
        """
        @logger.wrap__entry(new_name='Making Request', include_params=True, include_result=False)
        @RepeatUponError.repeat(default_repeat_on_request_error, request_exceptions)
        @SegmentExecutionWithDelay.delay(default_delay_between_requests)
        def make_request(self, url, *args, **kwargs):
            """Method To Perform A Request To A Given URL With The Given Arguments &
            Keyword Arguments. Note, Some Keyword Arguments Are Used Explicitly By The
            Method Itself & Will Not Be Passed In The Request To The Given.
            
            Parameters
            ----------
            check_status_code : bool
                Whether an error should be raised if the recieved reponse does not have a
                200 status code.
            update_referer : str
                Updates referer to this value when method is executed, note if a default
                referer was specified in the initial call to create_request_mixin, the
                referer will be reset to that default value in the next call to make request
                unless a explicit referer is again passed to the method.
            request_method : str || Callable
                Explicit Request Method Which Should Be Used By To Make The Request, Defaults
                to self.session.get .
            """
            
            #region Kwarg Extraction
            check_status_code = kwargs.pop('check_status_code', default_check_status_code)
            update_referer   = kwargs.pop('update_referer', default_referer)
            request_method    = kwargs.pop('request_method', 
                default_request_method if default_request_method else self.session.get
            )
            #endregion
            
            #region Pre-Request-Actions
            if isinstance(request_method, str): # try cast string to session callable
                try: request_method = getattr(self.session, request_method.lower())
                except ValueError:
                    raise ValueError(f'Unknown Request Method {request_method}')
            
            current_referer = self.session.headers.get('referer', None) # extract
            change_referer  = update_referer and current_referer != update_referer
            if change_referer: self.session.headers['referer'] = update_referer
            #endregion
            
            #region Make Request
            formatted_a_kw = logger.format_params(*args, **kwargs) # format params
            logger.debug(f'Making Request To Url "{url}" With {formatted_a_kw} Using {request_method.__name__.upper()}')
            response = request_method(url, *args, **kwargs) # store request response
            logger.debug(f'Response Recieved With Status {response.status_code}')
            #endregion
            
            #region Post-Request-Actions
            if change_referer: self.session.headers['referer'] = current_referer
            if check_status_code: response.raise_for_status() # only accept code 200
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
