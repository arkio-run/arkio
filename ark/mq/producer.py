import logging
from typing import Any
from typing import Callable
from typing import Dict

import ujson
from confluent_kafka import KafkaError
from confluent_kafka import Message
from confluent_kafka import Producer
from kombu import Connection
from kombu import Exchange
from kombu import producers
from kombu.entity import PERSISTENT_DELIVERY_MODE as PERSISTENT

logger = logging.getLogger(__name__)


def wrap(func: Callable[..., Any]) -> Callable[..., Any]:
    def inner(self: Any, *args: Any, **kwargs: Any) -> Any:
        target = self.topic if self.type == "kafka" else kwargs.get("routing_key", "unknown")
        try:
            return func(self, *args, **kwargs)
        except BaseException as exc:
            logger.error("type:{} target:{} error:{}".format(self.type, target, repr(exc)), exc_info=True)
            raise

    return inner


class AmqpProducer:
    def __init__(
        self,
        broker: str = "",
        exchange: str = "",
        type: str = "direct",
        serializer: str = "json",
        durable: bool = True,
        delivery_mode: int = PERSISTENT,
    ) -> None:
        self.serializer = serializer
        self.connection = Connection(broker)
        self.retry_policy = {
            "max_retries": 2,
            "interval_start": 1,
            "interval_step": 5,
            "interval_max": 10,
        }
        self.type = "amqp"
        self.exchange = Exchange(name=exchange, type=type, delivery_mode=delivery_mode, durable=durable)

    @wrap
    def send(self, message: Dict[str, object], routing_key: str = "") -> None:
        logger.info("message:{}".format(message))
        pool = producers[self.connection]
        producer = pool.acquire(block=False, timeout=None)
        try:
            producer.publish(
                message,
                routing_key=routing_key,
                exchange=self.exchange,
                declare=[self.exchange],
                serializer=self.serializer,
                retry_policy=self.retry_policy,
            )
        except BaseException:
            pool.connections.replace(producer.connection)
            producer.__connection__ = None
            pool.replace(producer)
            raise
        else:
            pool.release(producer)


class KafkaProducer:
    def __init__(self, broker: str, topic: str) -> None:
        conf = {"bootstrap.servers": broker}
        self.topic = topic
        self.producer = Producer(**conf)
        self.type = "kafka"

    def on_delivery(self, err: KafkaError, msg: Message) -> None:
        if err:
            logger.info("kafka message failed delivery:{}".format(err))
        else:
            logger.info("kafka message delivered to:{}".format((msg.topic(), msg.partition(), msg.offset())))

    @wrap
    def send(self, message: Dict[str, object]) -> None:
        # ref: https://github.com/confluentinc/confluent-kafka-python/issues/137
        self.producer.produce(self.topic, ujson.dumps(message), on_delivery=self.on_delivery)
        self.producer.poll(0)
        # self.producer.flush(3)
