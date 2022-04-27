from typing import Any

from ..config import infra_config
from ..config import InfraConfig
from .producer import AmqpProducer
from .producer import KafkaProducer


class AmqpSender(AmqpProducer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert isinstance(infra_config, InfraConfig)
        kwargs["broker"] = infra_config.amqp.get(kwargs["broker"])
        super().__init__(*args, **kwargs)


class KafkaSender(KafkaProducer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert isinstance(infra_config, InfraConfig)
        kwargs["broker"] = infra_config.kafka.get(kwargs.get("broker", "default"))
        super().__init__(*args, **kwargs)
