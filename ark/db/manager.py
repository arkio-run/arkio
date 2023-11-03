import logging
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from ark.metric.mid import DBMetric
from .event import event_register

POOL_SIZE = 8
POOL_RECYCLE = 600
POOL_TIMEOUT = 3
READ_TIMEOUT = 10
WRITE_TIMEOUT = 10
MAX_OVERFLOW = 0

ECHO = False
ECHO_POOL = False
AUTOCOMMIT = False

logger = logging.getLogger(__name__)

metric = DBMetric()


def create_session(appid, db, cfg):
    autocommit = cfg.get('autocommit', AUTOCOMMIT)
    connect_args = {
        'autocommit': autocommit,
        'read_timeout': READ_TIMEOUT,
        'write_timeout': WRITE_TIMEOUT,
    }
    connect_args.update(**cfg.get('connect_args', {}))

    engine_args = {
        'pool_size': POOL_SIZE,
        'pool_recycle': POOL_RECYCLE,
        'pool_timeout': POOL_TIMEOUT,
        'max_overflow': MAX_OVERFLOW,
        'echo': ECHO,
        'echo_pool': ECHO_POOL,
    }
    logger.info('db:{} connect_args:{} engine_args:{}'.format(db, connect_args, engine_args))
    engine_args.update(**cfg.get('engine_args', {}))
    engine = create_engine(cfg['url'], connect_args=connect_args, **engine_args)
    session_factory = sessionmaker(engine, expire_on_commit=False, autocommit=autocommit)
    event_register(engine, appid=appid, db=db, metric=metric)
    return scoped_session(session_factory)


class Manager:
    def __init__(self):
        self.mapping = {}
        self.initialized = False
        self.lock = threading.Lock()

    def initialize(self):
        with self.lock:
            from ark.config import basic_config
            app_id = basic_config.app_id
            from ark.config import infra_config
            for name, cfg, in infra_config.database.items():
                cfg = cfg if isinstance(cfg, dict) else {'url': cfg}
                self.mapping[name] = create_session(app_id, name, cfg)
            self.initialized = True

    def get(self, name):
        if not self.initialized:
            self.initialize()
        return self.mapping[name]

    def close(self):
        for Session in self.mapping.values():
            try:
                Session.close()
            except Exception as exc:
                logger.error('Session close exc:{}'.format(repr(exc)), exc_info=True)

    def remove(self):
        for Session in self.mapping.values():
            try:
                Session.remove()
            except Exception as exc:
                logger.error('Session remove exc:{}'.format(repr(exc)), exc_info=True)


manager = Manager()
