#!/usr/bin/env python3

"""
Module exercise
"""
import redis
from typing import Union, Optional, Callable
import uuid
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    count how many times methods
    of the Cache class are called
    """
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """decorator wrapper"""
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    store the history of inputs and
    outputs for a particular function.
    """
    key_inputs = method.__qualname__ + ":inputs"
    key_outputs = method.__qualname__ + ":outputs"

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """decorator wrapper"""
        self._redis.rpush(key_inputs, str(args))
        output = method(self, *args, **kwargs)
        self._redis.rpush(key_outputs, str(output))
        return output
    return wrapper


def replay(method: Callable) -> None:
    """
    display the history of calls of a particular function
    """
    key = method.__qualname__
    key_inputs = key + ":inputs"
    key_outputs = key + ":outputs"

    redis = method.__self__._redis

    count = redis.get(key).decode("utf-8")
    print("{} was called {} times:".format(key, count))

    inputList = redis.lrange(key_inputs, 0, -1)
    outputList = redis.lrange(key_outputs, 0, -1)

    all_data = list(zip(inputList, outputList))
    for i, j in all_data:
        attr, data = i.decode("utf-8"), j.decode("utf-8")
        print("{}(*{}) -> {}".format(key, attr, data))


class Cache:
    """
    A redis Cache class
    """
    def __init__(self):
        """
        Stores an instnace of redis client
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Takes a data argument and
        returns a string
        """
        key: uuid.UUID = str(uuid.uuid1())

        self._redis.set(key, data)

        return key

    def get(self,
            key: str,
            fn: Optional[Callable] = None
            ) -> Union[str, bytes, int, float]:
        """
        Read from redis and
        recover original type
        """
        data = self._redis.get(key)

        return fn(data) if fn else data

    def get_str(self, data: bytes) -> str:
        """
        convert bytes to string
        """
        return data.decode('utf-8')

    def get_int(self, data: bytes) -> int:
        """
        convert string to integer
        """
        return int(data)
