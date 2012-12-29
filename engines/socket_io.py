from socketio.namespace import BaseNamespace
from socketIO_client import SocketIO, BaseNamespace as BaseNamespace_Client
import logging
from events.emitter import Event, EventEmitter
from socketio import socketio_manage


ev_log = logging.getLogger('events')


class EventNamespace(BaseNamespace):
    def __init__(self, event_emitter, *args, **kwargs):
        self.event_emitter = event_emitter
        super(EventNamespace, self).__init__(*args, **kwargs)

    def emit_subscribed_event(self, evt):
        self.emit('event', evt.selector)

    def on_subscribe(self, evt_selector):
        self.event_emitter.on(evt_selector)(self.emit_subscribed_event)

    def on_unsubscribe(self, evt_selector):
        self.event_emitter.off(evt_selector)()

    def on_close(self):
        self.event_emitter.off()


def namespace_factory(event_emitter):
    def make_ns(*args, **kwargs):
        return EventNamespace(event_emitter, *args, **kwargs)
    return make_ns


class RemoteNamespace(BaseNamespace_Client):
    def __init__(self, socket, *args, **kwargs):
        self.socket = socket
        super(RemoteNamespace, self).__init__(*args, **kwargs)

    def on_event(self, selector):
        evt = Event(selector)
        evt.emit_on(self.socket)


class SocketIOEventEmitter(EventEmitter):
    def __init__(self, namespace, *args, **kwargs):
        self.namespace = namespace
        super(SocketIOEventEmitter, self).__init__(*args, **kwargs)
    
    def handle_request(self, request):
        io_ns = namespace_factory(event_emitter=self)
        return socketio_manage(request.environ, {self.namespace: io_ns}, request)

    def remote(self, url, subscriptions):
        url, port = url.rsplit(':', 1)
        socket = SocketIO(url, int(port), RemoteNamespace)

        for selector in subscriptions:
            socket.emit('subscribe', selector)

        self.remotes.push(socket)
