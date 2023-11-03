import logging

from flask.testing import FlaskClient

from .. import env
logger = logging.getLogger(__name__)


class GrpcClient:
    def __init__(self, app):
        self.app = app

    def call(self, path, request, context=None, mute=True):
        # e.g.:
        # c.call('/helloworld.Greeter/SayHello', helloworld_pb2.HelloRequest(name='ark'))
        method = self.app.service.methods.get(path)
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

class WsgiClient:
    def __init__(self, app):
        self.app = app

    def get(self, uri, params=None, headers=None):
        # e.g.: c.get('/user', {'id': 1018287200}, headers={"X-Auth-Token": "1"})
        params=params or {}
        headers=headers or {}
        with self.app.test_client() as c:
            return c.get(uri, query_string=params, headers=headers).get_json()


    def post(self, uri, params=None, headers=None):
        # e.g.: c.post('/user', {'name': 'arkio'}, headers={"X-Auth-Token": "1"})
        params=params or {}
        headers=headers or {}
        with self.app.test_client() as c:
            assert isinstance(c, FlaskClient)
            return c.post(uri, json=params, headers=headers).get_json()


def start():
    if env.is_grpc():
        from . import grpc #noqa
        client = GrpcClient(grpc.init())
    elif env.is_wsgi():
        from . import wsgi  #noqa
        client = WsgiClient(wsgi.init())
    else:
        print("env invalid")
        return

    from IPython import start_ipython  #noqa
    start_ipython(argv=[], user_ns=dict(c=client))
