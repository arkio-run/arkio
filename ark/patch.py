def patch_all():
    return
    from gevent.monkey import patch_all

    patch_all()

    from grpc.experimental.gevent import init_gevent

    init_gevent()
