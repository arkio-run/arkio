task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Shanghai"
enable_utc = True
worker_hijack_root_logger = False
broker_transport_options = {
    "visibility_timeout": 86400 * 7,
    # retry
    "max_retries": 3,
    "interval_start": 0,
    "interval_max": 1,
    "interval_step": 0.5,
    # redis timeout
    "socket_timeout": 3,
    "socket_connect_timeout": 3,
    "retry_on_timeout": 3,
    # amqp timeout
    "connect_timeout": 3,
    "read_timeout": 3,
    "write_timeout": 3,
}
