import functools
import logging

from .manager import manager

logger = logging.getLogger(__name__)


def db_session_close(func):
    @functools.wraps(func)
    def deco(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            manager.close()

    return deco


def db_session_remove(func):
    @functools.wraps(func)
    def deco(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            manager.remove()

    return deco
