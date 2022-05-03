import os
import sys

from gunicorn.app.wsgiapp import WSGIApplication

from ark.config import app_config


class WSGIApp(WSGIApplication):
    def __init__(self, *args, **kwargs):
        self.app_uri = None
        super().__init__(*args, **kwargs)

    def init(self, parser, opts, args):
        self.app_uri = app_config.app_uri
        args = [self.app_uri]
        super().init(parser, opts, args)


def start():
    port = app_config.port + int(os.getenv("INST_NO", 0))
    args = [
        "--bind={}".format("0.0.0.0:{}".format(port)),
        "--worker-class=gevent",
        "--access-logformat=%(s)s %(m)s %({raw_uri}e)s (%(h)s) %(M)sms",
        "--logger-class=ark.log.GLogger",
    ]
    sys.argv += args
    WSGIApp().run()
