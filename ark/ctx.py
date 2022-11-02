import threading
import logging
from typing import Any
from typing import Dict
from uuid import uuid4

logger = logging.getLogger(__name__)


class Meta:
    TRACE_ID_KEY = "x-trace-id"

    def __init__(self, **kwargs) -> None:
        self._meta: Dict[str, Any] = kwargs

    def set(self, k: str, v: Any) -> None:
        self._meta[k] = v

    def get(self, k: str, default: Any = None) -> Any:
        return self._meta.get(k, default)

    def clear(self) -> None:
        self._meta.clear()

    def gen_trace_id(self) -> str:
        trace_id = str(uuid4()).replace("-", "").lower()
        self._meta[self.TRACE_ID_KEY] = trace_id
        return trace_id

    @property
    def trace_id(self) -> str:
        if self.TRACE_ID_KEY not in self._meta:
            self.decode_context(self.TRACE_ID_KEY)
        return self._meta.get(self.TRACE_ID_KEY) or self.gen_trace_id()

    @trace_id.setter
    def trace_id(self, val: str) -> None:
        self._meta[self.TRACE_ID_KEY] = val

    @property
    def context(self):
        return self._meta.get('context')

    def decode_context(self, target):
        """每次只解析一个"""
        if not self.context:
            return
        try:
            metadata = self.context.invocation_metadata()
            for datum in metadata:
                if datum.key != target:
                    continue
                if datum.key == self.TRACE_ID_KEY and datum.value:
                    self._meta[self.TRACE_ID_KEY] = datum.value
        except Exception as exc:
            logger.error('grpc context exc:{}'.format(repr(exc)), exc_info=True)


class Global(object):
    def __init__(self) -> None:
        self.ctx = threading.local()

    @property
    def meta(self) -> Meta:
        try:
            return self.ctx.meta
        except:  # noqa
            self.ctx.meta = Meta()
            return self.ctx.meta

    @meta.setter
    def meta(self, meta):
        self.ctx.meta = meta


g: Global = Global()
