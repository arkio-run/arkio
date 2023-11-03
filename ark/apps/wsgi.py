import os
import sys
import threading

from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.http.message import Request
from gunicorn.workers.gthread import ThreadWorker as _ThreadWorker

from ark.config import app_config
from ark.ctx import g, Meta
from ark import db

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
