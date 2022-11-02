
import logging
import threading
import prometheus_client


logger = logging.getLogger(__name__)


class BasicMetric:
    _metrics = {}
    _lock = threading.Lock()
    _path = '{domain}__{name}'

    _Metric = None  # eg. 'Summary'
    _domain = ''    # eg. 'iface'

    @classmethod
    def factory(cls):
        return getattr(prometheus_client, cls._Metric)

    @classmethod
    def get_or_create(cls, name, tags):
        key = cls.gen_key(name)
        return cls._metrics.get(key) or cls.create(name, tags)

    @classmethod
    def create(cls, name, tags):
        key = cls.gen_key(name)
        with cls._lock:
            if key not in cls._metrics:
                from ark.config import app_config
                namespace = app_config.metric.get('namespace', 'ark')
                subsystem = app_config.metric.get('subsystem', 'stat')
                cls._metrics[key] = cls.factory()(
                    key, '', namespace=namespace, subsystem=subsystem, labelnames=sorted(tags.keys()))
            return cls._metrics.get(key)

    @classmethod
    def gen_key(cls, name):
        return cls._path.format(domain=cls._domain, name=name)

    @classmethod
    def counter(cls, name, tags=None, amt=1):
        # 计数器
        try:
            tags = tags or {}
            cls.get_or_create(name, tags).labels(**tags).inc(amt)
        except Exception as exc:
            logger.error('[Metric] counter exc:{}'.format(repr(exc)), exc_info=True)

    @classmethod
    def timer(cls, name, tags=None, amt=1.0):
        # 计时器
        try:
            tags = tags or {}
            cls.get_or_create(name, tags).labels(**tags).observe(amt)
        except Exception as exc:
            logger.error('[Metric] timer exc:{}'.format(repr(exc)), exc_info=True)
