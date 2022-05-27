import functools
import logging
import time
from concurrent import futures
from types import ModuleType
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import grpc._server
from google.protobuf import json_format

from ark.ctx import g, Meta
from google.protobuf.descriptor import FileDescriptor
from grpc_reflection.v1alpha import reflection

from ark.config import GrpcAppConfig
from ark.config import load_app_config
from ark.env import get_mode
from ark.env import MODE_GRPC
from ark.exc import BizExc, SysExc
from ark.utils import load_module
from ark.utils import load_obj
from .patch import custom_code

service = None
logger = logging.getLogger('ark.apps.grpc')


class Servicer:
    ignore_methods = []
    _wrapped_methods = {}

    def __getattribute__(self, name):
        if name[0] == '_':
            return object.__getattribute__(self, name)

        if name in self._wrapped_methods:
            return self._wrapped_methods[name]

        attr = object.__getattribute__(self, name)
        if not hasattr(attr, '__call__'):
            return attr

        @functools.wraps(attr)
        def inner(request, context):
            """统计接口状况，QPS、耗时等"""
            g.meta = Meta(context=context)
            t0 = time.time()
            try:
                json_req = json_format.MessageToDict(request, preserving_proto_field_name=True)
                logger.info('iface:{} req:{}'.format(name, json_req))
                rsp = attr(request, context)
            except (BizExc, SysExc) as exc:
                ret = 'biz_exc' if isinstance(exc, BizExc) else 'sys_exc'
                logger.warning('iface:{} exc:{}'.format(name, repr(exc)))
                context.abort(custom_code(exc.code), exc.msg) if context else None
            except BaseException as exc:
                ret = 'sys_exc'
                logger.error('iface:{} error:{}'.format(name, repr(exc)), exc_info=True)
                context.abort(grpc.StatusCode.UNKNOWN, 'unknown error') if context else None
            else:
                if name not in self.ignore_methods:
                    cost = (time.time()-t0) * 1000
                    json_rsp = json_format.MessageToDict(rsp, preserving_proto_field_name=True)
                    logger.info('iface:{} cost:{:.02f}ms rsp:{}'.format(name, cost, json_rsp))
                return rsp
            finally:
                try:
                    g.meta.clear()
                except BaseException as exc:
                    logger.error('Servicer method:{} exc:{}'.format(name, repr(exc)), exc_info=True)
        self._wrapped_methods[name] = inner
        return inner


class Service:
    def __init__(self, protos: List[Tuple[FileDescriptor, ModuleType]] = None) -> None:
        self.protos = protos or []
        self.server: Optional[grpc._server._Server] = None  # noqa
        self.module: Optional[ModuleType] = None
        self.endpoints: Dict[str, str] = {}  # {"Greeter": "/helloworld.Greeter"}
        self.methods: Dict[str, Callable[..., Any]] = {}  # {"/helloworld.Greeter/SayHello": func}

    def init(self) -> None:
        mode = get_mode()
        logger.info("service init :{}".format(mode))
        if mode == MODE_GRPC:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))

        for descriptor, pb2_grpc in self.protos:
            for k, s in descriptor.services_by_name.items():
                servicer = getattr(self.module, s.name)()
                if mode == MODE_GRPC:
                    getattr(pb2_grpc, "add_{}Servicer_to_server".format(s.name))(servicer, self.server)

                self.endpoints[servicer.__class__.__name__] = s.full_name
                func_names = getattr(pb2_grpc, "{}Servicer".format(s.name)).__dict__.keys()
                for func_name in func_names:
                    if not func_name.startswith("_"):
                        method = getattr(servicer, func_name)
                        if not method:
                            continue
                        self.methods["/{}/{}".format(s.full_name, func_name)] = method

        if mode == MODE_GRPC:
            service_names = [reflection.SERVICE_NAME] + list(self.endpoints.values())
            reflection.enable_server_reflection(service_names, self.server)

    def start(self) -> None:
        logger.info("service start")
        assert self.server
        self.server.add_insecure_port("[::]:50051")
        self.server.start()
        self.server.wait_for_termination()

    def stop(self) -> None:
        logger.info("service stop")
        assert self.server
        self.server.stop(5)


def init() -> Service:
    global service
    if not service:
        cfg = load_app_config()
        assert isinstance(cfg, GrpcAppConfig)
        service = load_obj(cfg.app_uri)
        module = load_module(cfg.app_uri.split(":")[0])
        assert isinstance(service, Service)
        service.module = module
        service.init()
    return service


def start() -> None:
    s = init()
    s.start()
