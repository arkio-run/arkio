import logging
import sys

from celery.bin import celery

from ark.apps import grpc

logger = logging.getLogger(__name__)


def start():
    from ark.config import load_basic_config

    cfg = load_basic_config()
    level = getattr(logging, cfg.log_lv)

    if sys.argv[-1] != "-h":
        sys.argv = (
            sys.argv[:1]
            + ["-A", "ark.celery.task"]
            + sys.argv[1:]
            + ["-n", "1234"]
            + ["-l", logging.getLevelName(level)]
        )
        # sys.argv.extend(["-P", "gevent"])
        sys.argv.extend(["-P", "threads"])
        grpc.init()
        celery.main()
    else:
        sys.argv[-1] = "--help"
        celery.main()
