import logging
from events.emitter import EventEmitter
from gevent import sleep, spawn

ev_log = logging.getLogger('events')


class PGEventEmitter(EventEmitter):
    def __init__(self, connection, *args, **kwargs):
        super(PGEventEmitter, self).__init__(*args, **kwargs)

        self.connection = connection
        self.pollster = spawn(self.poll_for_events)
    
    def poll_for_events(self):
        while True:
            self.connection.poll()

            while self.connection.notifies:
                notify = self.connection.notifies.pop()
                self.emit(notify.payload)

            sleep(0.1)

    def on(self, selector):
        parent_decorator = super(PGEventEmitter, self).on(selector)
        ev_log.debug('\n{self}.on({selector})'.format( self=repr(self),
                                                       selector=selector ))

        def decorator(callback):
            if selector not in self.callbacks:
                sql = "select subscribe('"+ selector +"')"
                c = self.connection.cursor()
                c.execute(sql);
                self.connection.commit()

            parent_wrapper = parent_decorator(callback)
            ev_log.debug('\n{self}.on({selector})({callback})'.format( self=repr(self),
                                                                       selector=selector,
                                                                       callback=repr(callback) ))
            def wrapper():
                return callback()

            return wrapper
        return decorator

    # TODO later remove subscriptions for selectors with no callbacks
    def off(self, selector=None, callback=None):
        super(PGEventEmitter, self).off(selector, callback)
