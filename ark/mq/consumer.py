import functools
import logging
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Union

import ujson
from confluent_kafka import Consumer
from confluent_kafka.cimpl import KafkaException
from confluent_kafka.cimpl import TopicPartition
from kombu import Connection
from kombu import Exchange
from kombu import messaging
from kombu import Queue
from kombu.mixins import ConsumerMixin
from kombu.transport.pyamqp import Channel

from ark.exc import BizExc
from ark.exc import SysExc

logger = logging.getLogger(__name__)


def wrap(type: str, target: str, func: Any) -> Any:
    hdl = "{}:{}".format(func.__module__, func.__name__)

    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BizExc as exc:
            logger.warning("target:{} handler:{} exc:{}".format(target, hdl, repr(exc)))
        except (SysExc, BaseException) as exc:
            # consumer retry
            logger.error("target:{} handler:{} error:{}".format(target, hdl, repr(exc)), exc_info=True)
            raise

    return inner


class AmqpConsumer(ConsumerMixin):
    def __init__(self, broker: str = ""):
        self.handlers: List[Dict[str, Any]] = []
        self.consumers: List[messaging.Consumer] = []
        self.connection = Connection(broker)
        self.running = 1

    def get_consumers(self, Consumer: Callable[..., messaging.Consumer], channel: Channel) -> List[messaging.Consumer]:
        for hdl in self.handlers:
            queue = hdl["queue"]
            callback = hdl["callback"]
            kwargs = hdl["kwargs"]
            accept = ["pickle", "json"]
            prefetch_count = kwargs.get("prefetch_count")
            consumer = Consumer(queues=[queue], prefetch_count=prefetch_count, accept=accept, callbacks=[callback])
            self.consumers.append(consumer)
        return self.consumers

    def add_handler(self, queue: Queue, handler: Callable[..., Any], **kwargs: Any) -> None:
        self.handlers.append(
            {
                "queue": queue,
                "kwargs": kwargs,
                "callback": wrap("amqp", queue.name, handler),
            }
        )

    def declare_queue(
        self, name: str, durable: bool = True, exclusive: bool = False, auto_delete: bool = False
    ) -> Queue:
        channel = self.connection.channel()
        queue = Queue(name=name, durable=durable, exclusive=exclusive, auto_delete=auto_delete, channel=channel)
        queue.declare()
        return queue

    def unbind_queue(self, queue: Queue, rules: List[Dict[str, Union[str, bool]]]) -> None:
        for rule in rules:
            queue.unbind_from(
                exchange=Exchange(name=rule.get("exchange", "")),
                routing_key=rule.get("routing_key", ""),
                nowait=rule.get("nowait", False),
            )

    def bind_queue(self, queue: Queue, rules: List[Dict[str, Union[str, bool]]]) -> None:
        for rule in rules:
            queue.bind_to(
                exchange=rule.get("exchange", ""),
                routing_key=rule.get("routing_key", ""),
                nowait=rule.get("nowait", False),
            )

    def stop(self) -> None:
        self.running = 0
        self.should_stop = True


class KafkaConsumer:
    def __init__(self, broker: str, topic: str, group: str, handler: Callable[..., Any]) -> None:
        conf = {
            "bootstrap.servers": broker,
            "group.id": group,
            "session.timeout.ms": 6000,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }

        self.consumer = Consumer(conf)
        self.topics = [topic]
        self.handler = wrap("kafka", topic, handler)
        self.running = 1
        self.latest: Dict[str, TopicPartition] = {}  # '{topic}-{partition}'

    def on_assign(self, consumer: Consumer, partitions: List[TopicPartition]) -> None:
        logger.info("kafka assign:{}".format(partitions))

    def run(self) -> None:
        self.consumer.subscribe(self.topics, on_assign=self.on_assign)
        while self.running:
            partition = None
            try:
                msg = self.consumer.poll(timeout=1.0)
                if not msg:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())
                # key = '{topic}-{partition}'.format(topic=msg.topic(), partition=msg.partition())
                # if key not in self.latest:
                #     partition = TopicPartition(msg.topic(), msg.partition())
                #     watermark_offsets = self.consumer.get_watermark_offsets(partition)
                #     max_offset = watermark_offsets[1]
                #     partition = TopicPartition(msg.topic(), msg.partition(), int(max_offset))
                #     self.consumer.seek(partition)
                #     logger.info('{} reset offset:{}'.format(key, max_offset))
                #     self.latest[key] = 1
                #     continue
                partition = TopicPartition(msg.topic(), msg.partition(), msg.offset())
                try:
                    self.handler(ujson.loads(msg.value()), msg)
                except BaseException as exc:
                    logger.error("kafka handler partition:{} exc:{}".format(partition, repr(exc)), exc_info=True)
                    self.consumer.seek(partition)
                    time.sleep(1)
                else:
                    self.consumer.commit(asynchronous=False)
                    partition = None
            except BaseException as exc:
                logger.error("kafka consumer partition:{} exc:{}".format(partition, repr(exc)), exc_info=True)
                time.sleep(1)
        try:
            self.consumer.close()
            logger.info("kafka consumer close.")
        except BaseException as exc:
            logger.error("kafka consumer close, exc:{}".format(repr(exc)), exc_info=True)
        logger.info("{} kafka consumer stopped".format(self.topics))

    def stop(self) -> None:
        self.running = 0
