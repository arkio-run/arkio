"""
业务监控指标
"""

import logging

from .base import BasicMetric


logger = logging.getLogger(__name__)


class BizMetric(BasicMetric):
    _Metric = 'Counter'
    _domain = 'biz'

    @classmethod
    def counter(cls, name, tags=None, amt=1):
        logger.debug('[metric] {} {}, result:{} amt:{}'.format(cls._domain, name, tags, amt))
        super(BizMetric, cls).counter(name, tags=tags, amt=amt)


class BizTimerMetric(BasicMetric):
    _Metric = 'Summary'
    _domain = 'biz'

    @classmethod
    def timer(cls, name, tags=None, amt=1):
        logger.debug('[metric] {} {}, result:{} amt:{}'.format(cls._domain, name, tags, amt))
        super(BizTimerMetric, cls).timer(name, tags=tags, amt=amt)
