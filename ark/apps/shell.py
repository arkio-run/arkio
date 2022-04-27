import logging

from . import grpc as app

logger = logging.getLogger(__name__)


class GrpcClient:
    @staticmethod
    def call(path, request, context=None, mute=True):
        # e.g.:
        # c.call('/helloworld.Greeter/SayHello', helloworld_pb2.HelloRequest(name='ark'))
        method = app.service.methods.get(path)
        if not method:
            msg = "path:{}, handler not found".format(path)
            if mute:
                logger.warning(msg)
                return
            else:
                raise Exception(msg)
        rsp = method(request, context)
        if context and context.err:
            raise context.err
        return rsp


def start():
    from . import grpc as app

    app.init()

    from IPython import start_ipython

    start_ipython(argv=[], user_ns=dict(c=GrpcClient()))
