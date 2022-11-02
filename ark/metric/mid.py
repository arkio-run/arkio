
import logging

from .base import BasicMetric


logger = logging.getLogger(__name__)


class DBMetric(BasicMetric):
    _Metric = 'Summary'
    _domain = 'db'

    @classmethod
    def timer(cls, name, tags=None, amt=1.0):
        logger.debug('[metric] {} {}, tags:{} amt:{}'.format(cls._domain, name, tags, amt))
        super(DBMetric, cls).timer(name, tags=tags, amt=amt)


class CeleryMetric(BasicMetric):
    _Metric = 'Summary'
    _domain = 'celery'

    @classmethod
    def timer(cls, name, tags=None, amt=1.0):
        logger.debug('[metric] {} {}, tags:{} amt:{}'.format(cls._domain, name, tags, amt))
        super().timer(name, tags=tags, amt=amt)
