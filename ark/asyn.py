import functools
import logging

from google.protobuf.empty_pb2 import Empty

from ark.apps import grpc as app
from ark.celery.task import send_task
from ark.env import get_mode
from ark.env import MODE_GRPC
from ark.mock import mocked_context

logger = logging.getLogger(__name__)


def task(countdown=None, **kwargs):
    def deco(func):
        @functools.wraps(func)
        def inner(self, request, context):
            if get_mode() == MODE_GRPC:
                context = mocked_context(context)
                method = "/{}/{}".format(app.service.endpoints[self.__class__.__name__], func.__name__)
                send_task(method, request, context=context, countdown=countdown)
                return Empty()
            else:
                return func(self, request, context)

        return inner

    return deco
