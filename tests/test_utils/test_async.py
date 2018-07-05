from pydent.utils.async_requests import make_async
import time
import random

def test_async_basic():
    """Expect array to be return in correct order"""
    @make_async(3)
    def myfxn(arr):
        t = round(random.random(), 2)
        time.sleep(t)
        return arr

    result = myfxn(range(100))

    assert result == list(range(100))


def test_async_with_args():

    @make_async(2)
    def myfxn(arr, arg0):
        time.sleep(0.5)
        return [arg0] * len(arr)

    result = myfxn(range(10), 5)

    assert result == [5]*10


def test_async_with_kwargs():

    @make_async(2)
    def myfxn(arr, arg0, kwarg0=1):
        time.sleep(0.5)
        return [arg0*kwarg0] * len(arr)

    result = myfxn(range(10), 5)
    result2 = myfxn(range(10), 5, kwarg0=2)

    assert result == [5]*10
    assert result2 == [10]*10