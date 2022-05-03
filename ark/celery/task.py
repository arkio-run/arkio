import base64
import logging
import pickle

import grpc
from google.protobuf import json_format

from ..apps.shell import GrpcClient
from ..exc import BizExc
from ..exc import ExcCode
from ..exc import SysExc
from .app import app

client = GrpcClient()
logger = logging.getLogger(__name__)


@app.task(autoretry_for=(BaseException,), retry_kwargs={"max_retries": 3, "countdown": 10})
def async_api(method, request, context=None):
    try:
        request = pickle.loads(base64.b64decode(request))
        context = pickle.loads(base64.b64decode(context))
        # g.meta = Meta(context=context)
        json_request = json_format.MessageToDict(request, preserving_proto_field_name=True)
        logger.info("[async-api] method:{} request:{} context:{}".format(method, json_request, context))
        client.call(method, request, context, mute=False)
    except grpc.RpcError as err:
        code, msg = err.code().value[0], err.details()
        if code > ExcCode.RPC_ERR:
            logger.info("[async-api] method:{} exc:{}".format(method, repr(BizExc(code, msg))))
        else:
            logger.error("[async-api] method:{} exc:{}".format(method, repr(SysExc(code, msg))))
            raise
    except BaseException as exc:
        logger.error("[async-api] method:{} exc:{}".format(method, repr(exc)))
        raise


def send_task(method, request, context=None, countdown=None):
    try:
        json_request = json_format.MessageToDict(request, preserving_proto_field_name=True)
        logger.info("[send-task] method:{} request:{} context:{}".format(method, json_request, context))
        countdown = countdown or getattr(request, "countdown", 0)
        request = base64.b64encode(pickle.dumps(request)).decode()
        context = base64.b64encode(pickle.dumps(context)).decode()
        async_api.apply_async((method, request, context), countdown=countdown)
    except Exception as exc:
        logger.info("[send-task] method:{} exc:{}".format(method, repr(exc)))
    finally:
        pass
