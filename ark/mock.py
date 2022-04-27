import logging

import grpc


logger = logging.getLogger(__name__)


class RpcError(grpc.RpcError):
    def __init__(self, code, details):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class Context:
    def __init__(self, metadata=None):
        self.err = None
        self.metadata = metadata or []

    def abort(self, code, details):
        if code == grpc.StatusCode.OK:
            return
        self.err = RpcError(code, details)

    def invocation_metadata(self):
        return self.metadata

    def __str__(self):
        return "({})".format(",".join(tuple(str(datum) for datum in self.metadata)))


class Metadatum:
    def __init__(self, datum):
        self.key = datum.key
        self.value = datum.value

    def __str__(self):
        return "{}(key='{}', value='{}')".format(self.__class__.__name__, self.key, self.value)


def mocked_context(context):
    metadata = [Metadatum(datum) for datum in context.invocation_metadata()]
    return Context(metadata=metadata)
