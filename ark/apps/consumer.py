import functools
import logging
import os
import signal
from multiprocessing import Process
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from ..config import BasicAppConfig
from ..config import InfraConfig
from ..mq.consumer import AmqpConsumer
from ..mq.consumer import KafkaConsumer
from ark import config
from ark.utils import load_obj

logger = logging.getLogger(__name__)


class ConsumerMix:
    def __init__(
        self,
        broker: Optional[str] = None,
        type: Optional[str] = None,
        queues: Optional[List[Dict[str, Any]]] = None,
        topic: Optional[Dict[str, str]] = None,
        concurrency: int = 1,
    ) -> None:
        self.type = type or "amqp"
        self.broker = broker or ""
        self.queues = queues or []
        self.topic = topic or {}
        self.concurrency = concurrency
        self.runners = {
            "amqp": self.run_amqp,
            "kafka": self.run_kafka,
        }
        self.consumer: Optional[Union[AmqpConsumer, KafkaConsumer]] = None

    def start(self) -> List[Process]:

        processes = []
        for _ in range(self.concurrency):
            process = Process(target=self.run, daemon=True)
            processes.append(process)
            process.start()
        return processes

    def setup(self) -> None:
        from ark.log import set_log

        set_log()

        if not config.app_config:
            logger.info("consumer, load app config")
            config.load_app_config()
        if config.infra_config:
            # 一定要在子进程启动初始化，否则Apollo不能热更新
            raise Exception("consumer, infra config not empty.")
        config.load_infra_config()

    def run(self) -> None:
        logger.info("consumer running.")
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        self.setup()
        self.runners[self.type]()

    def stop(self, signum: int, frame: Any) -> None:
        logger.info("consumer stopping.")
        assert self.consumer
        self.consumer.stop()

    def run_amqp(self) -> None:
        from ark.mq.consumer import AmqpConsumer

        infra = config.infra_config
        assert isinstance(infra, InfraConfig)

        broker = infra.amqp.get(self.broker, "")
        self.consumer = AmqpConsumer(broker=broker)
        for cfg in self.queues:
            queue = self.consumer.declare_queue(
                name=cfg["name"],
                durable=cfg.get("durable", True),
                exclusive=cfg.get("exclusive", False),
                auto_delete=cfg.get("auto_delete", False),
            )
            if "binding" in cfg:
                self.consumer.bind_queue(queue, cfg["binding"])
            if "unbound" in cfg:
                self.consumer.unbind_queue(queue, cfg["unbound"])
            handler = load_obj(cfg["handler"])
            prefetch_count = cfg.get("prefetch_count")
            self.consumer.add_handler(queue, handler, prefetch_count=prefetch_count)
        self.consumer.run()

    def run_kafka(self) -> None:
        from ark.mq.consumer import KafkaConsumer

        infra = config.infra_config
        assert isinstance(infra, InfraConfig)

        topic = self.topic["name"]
        group = self.topic["group"]
        broker = infra.kafka.get(self.broker, "")
        handler = load_obj(self.topic["handler"])
        self.consumer = KafkaConsumer(broker, topic, group, handler)
        self.consumer.run()


def stop(processes: List[Process], signum: int, frame: Any) -> None:
    logger.info("consumer, got signal {}".format(signum))
    for proc in processes:
        logger.warning("sending {} to {}".format(signum, proc.pid))
        if not proc.pid:
            continue
        os.kill(proc.pid, signum)


def start() -> None:
    logger.info("main consumer start.")
    processes: List[Process] = []
    signal.signal(signal.SIGINT, functools.partial(stop, processes))
    signal.signal(signal.SIGTERM, functools.partial(stop, processes))
    app = config.app_config
    assert isinstance(app, BasicAppConfig)
    for cfg in app.consumers:
        type = cfg.get("type", "amqp")
        if type == "amqp":
            consumer = ConsumerMix(
                type=type,
                broker=cfg["broker"],
                queues=cfg.get("queues"),
                concurrency=cfg.get("concurrency", 1),
            )
            processes.extend(consumer.start())
        else:
            topics = cfg.get("topics", [])
            for topic in topics:
                consumer = ConsumerMix(
                    type=type,
                    broker=cfg["broker"],
                    topic=topic,
                    concurrency=topic.get("concurrency", 1),
                )
                processes.extend(consumer.start())
    try:
        for process in processes:
            process.join()
    except BaseException as exc:
        logger.error("main consumer exc:{}.".format(repr(exc)), exc_info=True)
    finally:
        logger.info("main consumer stopped.")
        exit(0)
