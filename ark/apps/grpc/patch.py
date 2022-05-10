import enum
import collections
import grpc._common as cc


class GRPCCodeOutWrapper(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store.get(key, key.value[0])

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return self.store.get(key, key)


class GRPCCodeInWrapper(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        class sc(enum.Enum):
            DESC = (key, "custom code: " + str(key))
        return self.store.get(key, sc.DESC)

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return self.store.get(key, key)


def patch_status_code():
    cc.STATUS_CODE_TO_CYGRPC_STATUS_CODE = GRPCCodeOutWrapper(cc.STATUS_CODE_TO_CYGRPC_STATUS_CODE)
    cc.CYGRPC_STATUS_CODE_TO_STATUS_CODE = GRPCCodeInWrapper(cc.CYGRPC_STATUS_CODE_TO_STATUS_CODE)


def custom_code(code, dummy="custom code"):
    class sc(enum.Enum):
        DESC = (code, dummy)
    return sc.DESC
