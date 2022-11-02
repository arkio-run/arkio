import logging
import os
import socket
import traceback
from logging import LogRecord
from logging.handlers import TimedRotatingFileHandler

from gunicorn.glogging import Logger

from .ctx import g
from .env import get_mode


class TraceFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:

        try:
            record.traceId = g.meta.trace_id  # type: ignore
        except BaseException as exc:
            record.traceId = "unknown"  # type: ignore
            print("TraceFilter, exc:{}".format(repr(exc)))

        return True


def set_log() -> None:
    from .config import load_basic_config

    mode = get_mode()
    cfg = load_basic_config()
    level = getattr(logging, cfg.log_lv)

    extra = ""
    if mode == "consumer":
        extra = "[%(processName)s,%(process)d] "
    if level == logging.DEBUG:
        extra += "[%(threadName)s-%(thread)d] "

    fmt = "[%(asctime)s] [%(levelname)s] {extra}[%(name)s:%(lineno)d] " "[traceid:%(traceId)s] %(message)s".format(
        extra=extra
    )

    # 终端日志
    logging.basicConfig(level=level, format=fmt)
    logging.root.handlers[0].addFilter(TraceFilter())

    # 文件日志
    os.makedirs(os.path.join(cfg.log_dir, cfg.app_id), exist_ok=True)
    suffix = ""
    if os.getenv("LOG_NAME_SUFFIX"):
        suffix = "-" + os.getenv("LOG_NAME_SUFFIX")
    elif os.getenv("LOG_NAME_USING_HOST"):
        suffix = "-" + socket.gethostname()
    elif os.getenv("LOG_NAME_USING_HOST_SUFFIX"):
        suffix = "-" + socket.gethostname().split('-')[-1]
    filename = "{}/{}/{}{}.log".format(cfg.log_dir, cfg.app_id, mode, suffix)
    rotating_handler = TimedRotatingFileHandler(filename=filename, when=cfg.log_when, backupCount=cfg.log_backup)
    rotating_handler.setLevel(level)
    rotating_handler.setFormatter(logging.Formatter(fmt))
    rotating_handler.addFilter(TraceFilter())

    # 重置-终端&文件日志
    stderr = logging.root.handlers[0]
    logging.root.handlers.clear()
    logging.root.addHandler(stderr)
    logging.root.addHandler(rotating_handler)

    # 重置-Gunicorn日志
    error_logger = logging.getLogger("gunicorn.error")
    access_logger = logging.getLogger("gunicorn.access")
    error_logger.handlers.clear()
    access_logger.handlers.clear()
    error_logger.handlers.extend(logging.root.handlers)
    access_logger.handlers.extend(logging.root.handlers)


class GLogger(Logger):
    def access(self, resp, req, environ, request_time):
        safe_atoms = self.atoms_wrapper_class(self.atoms(resp, req, environ, request_time))
        try:
            safe_atoms["M"] = "{:.02f}".format(safe_atoms["D"] / 1000.0)
            self.access_log.info(self.cfg.access_log_format, safe_atoms)
        except Exception:  # noqa
            self.error(traceback.format_exc())

    def _set_handler(self, *args, **kwargs):
        return
