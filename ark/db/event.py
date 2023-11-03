import functools
import logging
import time

from sqlalchemy import event

from ..ctx import g

logger = logging.getLogger(__name__)


def parse(sql):
    method, table = 'unknown', 'unknown'
    try:
        if sql.startswith('/*'):
            sql = sql.split('*/ ', 1)[1]
        sql = sql.strip().upper()
        method = sql.split(' ', 1)[0]
        if method in ('SELECT', 'DELETE'):
            table = sql.split('FROM', 1)[1].strip().split(' ', 1)[0]
        elif method == 'INSERT':
            table = sql.split('INTO', 1)[1].strip().split(' ', 1)[0]
        elif method == 'UPDATE':
            table = sql.strip().split(' ', 2)[1]
    except Exception as exc:
        logger.error('parse sql exc:{}'.format(repr(exc)))

    return method, table.lower()


def before_execute(conn, cursor, statement, parameters, context, executemany, appid='', db='', metric=None):
    g.ctx.execute_start_time = time.time()
    comment = '/*appid:{},traceid:{}*/ '.format(appid, g.meta.trace_id)
    return comment + statement, parameters


def after_execute(conn, cursor, statement, parameters, context, executemany, appid='', db='', metric=None):
    cost = time.time() - g.ctx.execute_start_time
    method, table = parse(statement)
    sql = cursor.mogrify(statement, parameters)
    logger.info('db:{} table:{} method:{} cost:{:.02f}ms sql:{}'.format(db, table, method, cost * 1000, sql))
    if not metric:
        return
    metric.timer('execute', tags={'db': db, 'table': table, 'method': method}, amt=cost)


def event_register(engine, appid='', db='', metric=None):
    event.listen(engine, 'before_cursor_execute', functools.partial(before_execute, appid=appid, db=db, metric=metric), retval=True)
    event.listen(engine, 'after_cursor_execute', functools.partial(after_execute, appid=appid, db=db, metric=metric))
