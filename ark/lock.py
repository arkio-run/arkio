import time
import logging
from ark.exc import raise_biz_exc
from ark.exc import ExcCode

logger = logging.getLogger(__name__)


class Lock:
    # ref: redis.lock.Lock
    def __init__(self, red, sleep=0.1, timeout=60):
        self.red = red
        self.sleep = sleep
        self.timeout = timeout

    def acquire(self, key, timeout=None, blocking=False, blocking_timeout=None):
        timeout = timeout or self.timeout
        blocking_timeout = blocking_timeout or timeout
        stop_trying_at = time.time() + blocking_timeout
        while 1:
            if self.red.set(key, '1', ex=timeout, nx=True):
                return True
            if not blocking:
                return False
            next_try_at = time.time() + self.sleep
            if next_try_at > stop_trying_at:
                return False
            time.sleep(self.sleep)

    def release(self, key):
        self.red.delete(key)

    def on_arguments(self, pos=None, namespace=None, timeout=None, blocking=False, blocking_timeout=None,
                     code=ExcCode.LOCK_ERR, raise_fn=raise_biz_exc):
        def decorator(func):
            _pos = [pos] if type(pos) == int else pos or []
            _namespace = namespace or '{}:{}'.format(func.__module__, func.__name__)

            def inner(*args, **kwargs):
                key = _namespace + "|" + " ".join([str(args[idx]) for idx in _pos])
                logger.debug('lock key:{}'.format(key))
                if not self.acquire(key, timeout=timeout, blocking=blocking, blocking_timeout=blocking_timeout):
                    raise_fn(code)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.release(key)
            return inner
        return decorator
