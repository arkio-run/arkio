import os
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
    logger.info("metric running pid:{} ppid:{}".format(os.getpid(), os.getppid()))
    pid = 0 if os.getpid() == os.getppid() else os.getpid()
    grouping_key = {"host": host, "service": basic_config.app_id, "pid": pid}
    pushgateway = (infra_config.pushgateway if infra_config else {}).get("default", "")
    logger.info('pushgateway:{} grouping_key:{}'.format(pushgateway, grouping_key))

    while pushgateway:
        try:
            time.sleep(10)
            logger.debug("metric push to {}".format(pushgateway))
            push_to_gateway(pushgateway, job='pushgateway', registry=REGISTRY, grouping_key=grouping_key)
        except Exception as exc:
            logger.info("metric timer exc:{}".format(repr(exc)))


def start():
    logger.info("metric timer start")
    global thread
    if thread:
        return
    thread = Thread(target=running, daemon=True)
    thread.start()
