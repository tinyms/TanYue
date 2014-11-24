__author__ = 'i@tinyms.com'

import time
import functools
from types import CodeType


def timeit(func):
    @functools.wraps(func)
    def wrapper():
        start = time.clock()
        func.__a__ = '1'
        func()
        end = time.clock()
        print 'used:', end - start
    return wrapper


@timeit
def foo():
    print 'in foo()'
c = 2
apply(foo, [])
# foo()
# print(foo.__code__)
print(callable(c))
print(dir(foo.func_code))
print(foo.func_code.co_name)
print(foo.func_code.co_names)
# print type(foo.func_code) == CodeType