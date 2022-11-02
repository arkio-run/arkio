import time
import socket
import logging
from threading import Thread

from prometheus_client import push_to_gateway, REGISTRY

thread = None
logger = logging.getLogger(__name__)

host = socket.gethostname()


def running():
    logger.info("metric timer running")
    from ark.config import basic_config, BasicAppConfig
    from ark.config import infra_config, InfraConfig
    if not all((basic_config, infra_config)):
        logger.info("metric timer skip")
        return
    assert isinstance(basic_config, BasicAppConfig)
    assert isinstance(infra_config, InfraConfig)
    default_labels_dic = {"host": host, "service": basic_config.app_id}
    pushgateway = (infra_config.pushgateway if infra_config else {}).get("default", "")
    logger.info('host:{} service:{} pushgateway:{}'.format(host, basic_config.app_id, pushgateway))

    while pushgateway:
        try:
            time.sleep(10)
            logger.debug("metric push to {}".format(pushgateway))
            push_to_gateway(pushgateway, job='pushgateway', registry=REGISTRY, grouping_key=default_labels_dic)
        except Exception as exc:
            logger.info("metric timer exc:{}".format(repr(exc)))


def start():
    logger.info("metric timer start")
    global thread
    if thread:
        return
    thread = Thread(target=running, daemon=True)
    thread.start()
