"""
服务接口监控指标
"""
import logging

from .base import BasicMetric

logger = logging.getLogger(__name__)


class IfaceMetric(BasicMetric):
    _Metric = 'Summary'
    _domain = 'iface'

    @classmethod
    def timer(cls, name, tags=None, amt=1.0):
        logger.debug('[metric] {} {}, tags:{} cost:{:.03f}ms'.format(cls._domain, name, tags, amt*1000))
        super(IfaceMetric, cls).timer(name, tags=tags, amt=amt)
