import time
from datetime import date
from datetime import datetime
from importlib import import_module
from typing import Any


def date2str(dt: date) -> str:
    assert isinstance(dt, date)
    return dt.strftime("%Y-%m-%d")


def datetime2str(dt: datetime) -> str:
    assert isinstance(dt, datetime)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def str2date(dt_str: str) -> date:
    return datetime.strptime(dt_str, "%Y-%m-%d").date()


def str2datetime(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def dt2ts(dt: datetime) -> int:
    return int(time.mktime(dt.timetuple()))


def load_module(module: str) -> Any:
    return import_module(module)


def load_obj(path: str) -> Any:
    module, name = path.split(":")
    obj = getattr(load_module(module), name)
    return obj
