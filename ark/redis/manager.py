from redis import Redis
from ark.config import infra_config


class Manager:
    def __init__(self):
        self.mapping = {}
        for name, url in infra_config.redis.items():
            self.mapping[name] = Redis.from_url(url)

    def get(self, name):
        return self.mapping[name]


manager = Manager()
