from typing import Any
from typing import Dict
from typing import Union

import yaml

from . import env
from .env import TYPE_GRPC
from .env import TYPE_WSGI


class BasicAppConfig:
    def __init__(self) -> None:
        self.config = {}  # type: ignore

    def load(self) -> "BasicAppConfig":
        self.config = yaml.load(open("app.yaml"), Loader=yaml.FullLoader)
        return self

    @property
    def app_id(self) -> str:
        return str(self.config.get("appid", ""))

    @property
    def log_lv(self) -> str:
        return self.config.get("log_lv", "INFO").upper()  # type: ignore

    @property
    def log_dir(self) -> str:
        return str(self.config.get("log_dir", "/tmp"))

    @property
    def consumers(self) -> Any:
        return self.config.get("consumers", {})


class AsgiAppConfig(BasicAppConfig):
    @property
    def app_uri(self) -> str:
        return self.config.get("services", {}).get(TYPE_WSGI, {}).get("app")  # type: ignore

    @property
    def port(self) -> int:
        return self.config.get("services", {}).get(TYPE_WSGI, {}).get("port", 8000)  # type: ignore


class GrpcAppConfig(BasicAppConfig):
    @property
    def app_uri(self) -> str:
        return self.config.get("services", {}).get(TYPE_GRPC, {}).get("app")  # type: ignore


class InfraConfig:
    def __init__(self) -> None:
        self.config = {}  # type: ignore
        self.client = None

    def load(self) -> "InfraConfig":
        if not app_config:
            load_app_config()
        if env.is_in_ut():
            stream = open("infra_unittest.yaml")
        else:
            stream = open("infra.yaml")
        self.config = yaml.load(stream, Loader=yaml.FullLoader)
        return self

    @property
    def database(self) -> Dict[str, Dict[str, str]]:
        return self.config.get("infra", {}).get("database", {})  # type: ignore

    @property
    def redis(self) -> Dict[str, str]:
        return self.config.get("infra", {}).get("redis", {})  # type: ignore

    @property
    def amqp(self) -> Dict[str, str]:
        return self.config.get("infra", {}).get("amqp", {})  # type: ignore

    @property
    def kafka(self) -> Dict[str, str]:
        return self.config.get("infra", {}).get("kafka", {})  # type: ignore

    @property
    def celery_broker(self) -> str:
        return self.config.get("infra", {}).get("celery", {}).get("broker", "")  # type: ignore


app_config = None
infra_config = None
basic_config = None


def load_basic_config() -> BasicAppConfig:
    global basic_config
    if basic_config is None:
        basic_config = BasicAppConfig().load()
    return basic_config


def load_app_config() -> Union[AsgiAppConfig, GrpcAppConfig, BasicAppConfig]:
    global app_config
    if app_config is None:
        if env.is_wsgi():
            app_config = AsgiAppConfig().load()
        elif env.is_grpc():
            app_config = GrpcAppConfig().load()
        else:
            app_config = BasicAppConfig().load()
    return app_config


def load_infra_config() -> InfraConfig:
    global infra_config
    if infra_config is None:
        infra_config = InfraConfig().load()
    return infra_config


def set_conf():
    load_app_config()
    load_infra_config()
