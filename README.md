# Request Mixin

## Overview
RequestMixin includes simple request methods and a shared session instance so any implementing classes can make requests in a consistent reliable format. The end goal of this module is to provide a simple means of providing request methods along multiple classes with attributes such as cookies and request headers shared across them.

## Usage

### Using The Module Level Global RequestMixin Instance

```python
from request_mixin import RequestMixin

class A(RequestMixin, object):
    pass

A().make_request('https://www.google.co.uk')
```

### Using The create_request_mixin Method

```python
from request_mixin import create_request_mixin

class B(create_request_mixin(), object):
    pass
    
B().make_request('https://www.google.co.uk')
```

### Customising Default Request Behaviour Using create_request_mixin

```python
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
```
