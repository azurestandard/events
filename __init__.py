from engines.postgresql import PGEventEmitter
from engines.socket_io  import SocketIOEventEmitter

from db import connection
from http import Request


pg_ev = PGEventEmitter(connection.connection)


def app(environ, start_response):
    request = Request(environ)
    io_ev = SocketIOEventEmitter('/events')
    pg_ev.on('/aquameta_db/customers:*')(lambda evt: evt.forward_to(io_ev))
    io_ev.handle_request(request)
