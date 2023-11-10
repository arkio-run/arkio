import functools
import logging
import os
import sys
import threading
import time

from ark.utils import load_obj
from flask import request, Flask
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.http.message import Request
from gunicorn.workers.gthread import ThreadWorker as _ThreadWorker

from ark import db
from ark.config import app_config, WsgiAppConfig
from ark.ctx import g, Meta
from ark.exc import BizExc, SysExc
from ark.exc import ExcCode
from ark.metric.iface import IfaceMetric

logger = logging.getLogger(__name__)


class WSGIApp(WSGIApplication):
    def __init__(self, *args, **kwargs):
        self.app_uri = None
        super().__init__(*args, **kwargs)

    def init(self, parser, opts, args):
        self.app_uri = app_config.app_uri
        args = [self.app_uri]
        super().init(parser, opts, args)


class ThreadWorker(_ThreadWorker):
    def init_process(self):
        g.ctx = threading.local()
        from ark.metric import timer  # noqa
        timer.start()
        super().init_process()

    def handle_request(self, req, conn):
        try:
            assert isinstance(req, Request)
            g.meta = Meta()
            trace_id = {k: v for k, v in req.headers}.get(Meta.TRACE_ID_KEY.upper())
            if trace_id:
                g.meta.trace_id = trace_id
            super().handle_request(req, conn)
        finally:
            g.meta.clear()
            db.manager.remove()


def api_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        req = {}
        path = request.path
        method = request.method
        if method.upper() == 'GET':
            req = dict(request.args)
        elif method.upper() == 'POST':
            req = request.get_json()
        logger.info("[{}] {} req:{}".format(method, path, req))

        request_id = g.meta.trace_id
        t0 = time.time()
        ret, rsp = 'success', {}
        try:
            rsp = func(*args, **kwargs)
            rsp = {'code': ExcCode.SUCCESS, 'msg': '', 'data': rsp, 'request_id': request_id}
            logger.info("[{}] {} rsp:{}".format(method, path, rsp))
            return rsp
        except (BizExc, SysExc) as exc:
            ret = 'biz_exc' if isinstance(exc, BizExc) else 'sys_exc'
            rsp = {'code': exc.code, 'msg': exc.msg, 'data': {}, 'request_id': request_id}
            logger.warning('[{}] {} code:{} msg:{}'.format(method, path, exc.code, exc.msg))
            return rsp
        except BaseException as exc:
            ret = 'sys_exc'
            logger.error('[{}] {} exc:{}'.format(method, path, repr(exc)), exc_info=True)
            rsp = {'code': ExcCode.UNKNOWN, 'msg': repr(exc)[:100], 'data': {}, 'request_id': request_id}
            return rsp
        finally:
            try:
                iface = '{} [{}]'.format(path, method)
                tags = {'iface': iface, 'method': method, 'path': path, 'ret': ret, 'code': rsp.get('code', 0)}
                IfaceMetric.timer('wsgi', tags=tags, amt=time.time() - t0)
            except BaseException as exc:
                logger.error('[{}] {} exc:{}'.format(method, path, repr(exc)), exc_info=True)

    return wrapper


app = None


def init() -> Flask:
    global app
    if not app:
        cfg = app_config
        assert isinstance(cfg, WsgiAppConfig)
        app = load_obj(cfg.app_uri)
    return app


def start():
    port = app_config.port + int(os.getenv("INST_NO", 0))
    args = [
        "--bind={}".format("0.0.0.0:{}".format(port)),
        "--threads=100",
        "--worker-class=ark.apps.wsgi.ThreadWorker",
        "--access-logformat=%(s)s %(m)s %({raw_uri}e)s (%(h)s) %(M)sms",
        "--logger-class=ark.log.GLogger",
    ]
    sys.argv += args
    WSGIApp().run()
