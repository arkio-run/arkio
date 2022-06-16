
def patch_all():
    from ark.apps.grpc.patch import patch_status_code
    patch_status_code()

    return
    from gevent.monkey import patch_all
    patch_all()

    from grpc.experimental.gevent import init_gevent
    init_gevent()
