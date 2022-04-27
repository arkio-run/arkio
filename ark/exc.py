import functools
from typing import Any
from typing import Callable

import grpc


class ExcCode:
    # 系统异常<=999
    RPC_ERR = 999

    # 表示正常
    SUCCESS = 2000

    # 系统异常: [10001~10999]
    UNKNOWN = 10001

    # 业务异常: [20001~20999]
    LOCK_ERR = 20001

    # 服务降级
    DEGRADED = 50000


ExcDesc = {
    ExcCode.SUCCESS: "",
    ExcCode.UNKNOWN: "未知错误",
    ExcCode.LOCK_ERR: "并发锁冲突",
    ExcCode.DEGRADED: "研发小哥哥被外星人抓走了",
}


class ArkException(Exception):
    def __init__(self, code: int, msg: str = "", exc_info: bool = False) -> None:
        super().__init__()
        self.code = code
        self.msg = msg
        self.exc_info = exc_info

    def __repr__(self) -> str:
        return "{}(code={}, msg='{}')".format(self.__class__.__name__, self.code, self.msg)


class SysExc(ArkException):
    pass


class BizExc(ArkException):
    pass


def raise_sys_exc(code: int, msg: str = "", exc_info: bool = True, **kwargs: Any) -> None:
    msg = msg or ExcDesc.get(code, "")
    if kwargs:
        msg = msg.format(**kwargs)
    raise SysExc(code, msg, exc_info)


def raise_biz_exc(code: int, msg: str = "", exc_info: bool = False, **kwargs: Any) -> None:
    msg = msg or ExcDesc.get(code, "")
    if kwargs:
        msg = msg.format(**kwargs)
    raise BizExc(code, msg, exc_info)


def transform_exc(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as err:
            code, msg = err.code().value[0], err.details()
            if code <= ExcCode.RPC_ERR:
                raise_sys_exc(code, msg)
            else:
                raise_biz_exc(code, msg)

    return inner
