import os
import sys
from typing import Optional

_app_type = None
_app_mode = None
_env = os.getenv("RUNTIME_ENV")

ENV_UT = "UT"  # unittest
ENV_DEV = "DEV"
ENV_BETA = "BETA"
ENV_PRE = "PRE"
ENV_PRO = "PRO"


MODE_GRPC = "grpc"

TYPE_WSGI = "wsgi"
TYPE_GRPC = "grpc"


def env() -> Optional[str]:
    return _env


def is_in_dev() -> bool:
    return _env == ENV_DEV


def is_in_beta() -> bool:
    return _env == ENV_BETA


def is_in_ut() -> bool:
    return _env == ENV_UT


def is_in_pre() -> bool:
    return _env == ENV_PRE


def is_in_pro() -> bool:
    return _env == ENV_PRO


def is_wsgi() -> bool:
    return _app_type == TYPE_WSGI


def is_grpc() -> bool:
    return _app_type == TYPE_GRPC


def set_wsgi() -> None:
    global _app_type
    _app_type = TYPE_WSGI


def set_grpc() -> None:
    global _app_type
    _app_type = TYPE_GRPC


def get_mode() -> str:
    global _app_mode
    if not _app_mode:
        targets = ["serve", "--wsgi", "run", "shell", "worker", "consumer"]
        kws = [k for k in sys.argv if k in targets] or ["unknown"]
        _app_mode = "-".join(kws).replace("--", "").replace("serve-wsgi", "wsgi").replace("serve", "grpc")
    return _app_mode


def is_mode_grpc():
    return get_mode() == MODE_GRPC
