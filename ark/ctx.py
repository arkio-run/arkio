import threading
from typing import Any
from typing import Dict
from uuid import uuid4


class Meta:
    TRACE_ID_KEY = "x-trace-id"

    def __init__(self) -> None:
        self._meta: Dict[str, Any] = {}

    def set(self, k: str, v: Any) -> None:
        self._meta[k] = v

    def get(self, k: str, default: Any = None) -> Any:
        return self._meta.get(k, default)

    def clear(self) -> None:
        self._meta.clear()

    def gen_trace_id(self) -> str:
        trace_id = str(uuid4()).replace("-", "").upper()
        self._meta[self.TRACE_ID_KEY] = trace_id
        return trace_id

    @property
    def trace_id(self) -> str:
        return self._meta.get(self.TRACE_ID_KEY) or self.gen_trace_id()

    @trace_id.setter
    def trace_id(self, val: str) -> None:
        self._meta[self.TRACE_ID_KEY] = val


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


g: Global = Global()
