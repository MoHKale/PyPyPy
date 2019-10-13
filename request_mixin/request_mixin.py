"""RequestMixin includes simple request methods and a shared session instance
so any implementing classes can make requests in a consistent reliable format.

If you don't want session instances to be shared between request classes,
instead of using the auto created request_mixin.request_mixin.RequestMixin
use request_mixin.request_mixin.create_request_mixin() to create a new un-
related request mixin class.
"""

import json, logging, requests

from bs4 import BeautifulSoup as BS4
from .decorators import RepeatOnError
from typing import Union, Callable

from requests.exceptions import (
    ChunkedEncodingError, ConnectTimeout,
    ConnectionError, HTTPError, ReadTimeout,
    RequestException, Timeout, TooManyRedirects
)

REQUEST_EXCEPTIONS = [
    ChunkedEncodingError, ConnectTimeout,
    ConnectionError, HTTPError, ReadTimeout,
    RequestException, Timeout, TooManyRedirects
]

def create_request_mixin(**kwargs):
    """Method to create request mixin class with shared session instance used
    by each class which implements the mixin. this function allows assignment
    of default request arguments via specified keyword arguments.

    Parameters
    ----------
    check_status_code : bool
        Default value for whether request status codes are automatically checked.
    update_referer : str
        Default referer value assigned upon each request, set to none to ignore.
    soup_parser : str
        Default parser used by `BeautifulSoup`. defaults to html.parser
    request_method : str || Callable
        Default request method used when no request method is explicitly given.
        defaults to the get method of the session instance bound to the mixin.
    request_delay : int
        Default interval between subsequent requests. defaults to 0. implemented
        using request_mixin.decorators.segmentexecutionwithdelay therefore delay
        can be changed in the returned mixin by setting

        >>> RequestMixin.make_request.delay = input('New Delay Value :> ')

        or

        >>> create_request_mixin().make_request.delay = input('New Delay Value :> ')
    max_attempt_count : int
        Maximum number of times a request can be made when an error is encountered.
    persist_session : bool
        Variable indicating whether a single request.session instance should be used
        for all implementing classes of the mixin or whether each implementing class
        should create it's own session instance. by defaulth this is true.

    Notes
    -----
        you can dynamically change the default request count or the request interval
        by setting the instance attributes `_attempt_count` and `_request_delay`
        respectively.

    Example
    -------

    Using The create_request_mixin Method

        from request_mixin import create_request_mixin

        class B(create_request_mixin(), object):
            pass

        B().make_request('https://www.google.co.uk')

    Customising Default Request Behaviour Using create_request_mixin

        from request_mixin import create_request_mixin

        RequestMixin = create_request_mixin(
            request_method    = 'POST',
            check_status_code = True,
            max_attempt_count = 10,
            request_delay     = 3)

        class C(RequestMixin, object):
            pass

        C().make_request('https://www.google.co.uk')
    """

    default_check_status_code = kwargs.pop('check_status_code', False)
    default_referer           = kwargs.pop('update_referer',    None)
    default_soup_parser       = kwargs.pop('soup_parser',       'html.parser')
    default_request_method    = kwargs.pop('request_method',    'get')
    default_attempt_delay     = kwargs.pop('request_delay',     0)
    default_attempt_count     = kwargs.pop('max_attempt_count', 5)
    persist_session           = kwargs.pop('persist_session',   True)

    if len(kwargs) != 0:
        name = 'create_request_mixin'  # name of current method. Include in error msg
        kwargs = json.dumps(list(kwargs.keys())).replace('[', '{').replace(']', '}')
        raise ValueError('%s recieved some unexpected keyword arguments %s' % (name, kwargs))

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

        def __init__(self):
            if not(persist_session): self.session = requests.Session()

        if persist_session: session = requests.Session()  # as class variable

        @RepeatOnError.wrap(
            ('_attempt_count', default_attempt_count),
            ('_request_delay', default_attempt_delay),
            repeat_exception_types=REQUEST_EXCEPTIONS)
        def make_request(self, url, *args,
                         check_status_code: bool                 = default_check_status_code,
                         update_referer:    str                  = default_referer,
                         request_method:    Union[Callable, str] = None,
                         **kwargs):
            """Method to perform a request to a given url with the given arguments &
            keyword arguments. note, some keyword arguments are used explicitly by the
            method itself & will not be passed in the request to the given.

            Parameters
            ----------
            check_status_code
                Whether an error should be raised if the recieved reponse does not have a
                OK status code.
            update_referer
                Updates referer to this value when method is executed, note if a default
                referer was specified in the initial call to create_request_mixin, the
                referer will be reset to that default value in the next call to make request
                unless a explicit referer is again passed to the method.
            request_method
                Explicit request method which should be used by to make the request, defaults
                to `self.session.get`.
            """

            request_method = request_method or default_request_method

            if isinstance(request_method, str):  # try cast string to session callable
                try: request_method = getattr(self.session, request_method.lower())
                except ValueError:
                    raise ValueError(f'unknown request method {request_method}')

            current_referer = self.session.headers.get('referer', None)  # extract
            change_referer  = update_referer and current_referer != update_referer
            if change_referer: self.session.headers['referer'] = update_referer

            logging.debug(f'making request to url "%s" using %s with args: %s %s' % (
                url, request_method.__name__.upper(), args, kwargs))
            response = request_method(url, *args, **kwargs)  # store request response
            logging.debug(f'response recieved with status: {response.status_code}')

            if change_referer:    self.session.headers['referer'] = current_referer
            if check_status_code: response.raise_for_status()  # only accept code 200

            return response  # give back acceptable request response

        def make_soup_request(self, url, *args, soup_parser=default_soup_parser, **kwargs):
            """Makes a request to a given url & converts the response text to a
            `bs4.BeautifulSoup` instance.

            WARNING: request status codes should be considered to not automatically
            be checked so it is highly suggested that you explicitly pass the kwarg
            check_status_code with a truthy value to ensure it is checked.

            See also: help(self.make_request)

            Parameters
            ----------
            soup_parser
                explicit parser to be used by the `BeautifulSoup` instance
            """
            return BS4(self.make_request(url, *args, **kwargs).text, soup_parser)

        def make_json_request(self, url, *args, **kwargs):
            """Makes a request to a given url & interprets the response as JSON

            See also: help(self.make_request)"""
            return self.make_request(url, *args, **kwargs).json()

    return RequestMixin
