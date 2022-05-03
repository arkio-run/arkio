import logging
from concurrent import futures
from types import ModuleType
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import grpc._server
from google.protobuf.descriptor import FileDescriptor
from grpc_reflection.v1alpha import reflection

from ark.config import GrpcAppConfig
from ark.config import load_app_config
from ark.env import get_mode
from ark.env import MODE_GRPC
from ark.utils import load_module
from ark.utils import load_obj

service = None
logger = logging.getLogger(__name__)


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
