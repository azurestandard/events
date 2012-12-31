import logging
from gevent import sleep, spawn
from events.emitter import Event, EventEmitter


ev_log = logging.getLogger('events')


class RedisEventEmitter(EventEmitter):
    def __init__(self, connection, queue_key, *args, **kwargs):
        super(RedisEventEmitter, self).__init__(*args, **kwargs)
        self.connection = connection
        self.pubsub = connection.pubsub()
        self.pubsub.subscribe(queue_key)
        self.queue_key = queue_key
        self.pollster = spawn(self.wait_for_events)
    
    def wait_for_events(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                self._handle_selector(message['data'])

    def emit(self, selector):
        ev_log.debug('\n{self}.emit({selector})'.format( self=repr(self),
                                                         selector=selector ))

        self.connection.publish('events', 'selector')
