from engines.socket_io  import SocketIOEventEmitter, handle_socketio_request
from engines.redis      import RedisEventEmitter

from http import Request

from redis import Redis


#pg_ev = PGEventEmitter(connection.connection)
#pg_ev.on('/aquameta_db/customers:*')(lambda evt: evt.forward_to(io_ev))


def app(environ, start_response):
    request = Request(environ)

    io_ev = SocketIOEventEmitter('/events')
    rs_ev = RedisEventEmitter(Redis(), 'events')
    rs_ev.on('/:*')(lambda evt: evt.forward_to(io_ev))

    handle_socketio_request(request, [io_ev])
