from collections import defaultdict
import logging, re


ev_log = logging.getLogger('events')


class Event:
    selector_regex = re.compile('([\/\w]+):([\w*]+)')

    def __init__(self, evt_str):
        matches = self.selector_regex.match(evt_str)

        self.path = matches.group(1)
        self.type = matches.group(2)

    def emit_on(self, event_emitter):
        event_emitter.emit(self.selector)

    def forward_to(self, event_emitter):
        event_emitter.emit(self.selector)
    
    @property
    def selector(self):
        return self.path + ':' + self.type

    def is_selected_by(self, sel_evt):
        path_match = self.path == sel_evt.path[0:len(self.path)]
        type_match = sel_evt.type == self.type or self.type == '*'

        return path_match and type_match
        

class EventEmitter(object):
    def __init__(self):
        self.callbacks = defaultdict(lambda: set())
        self.remotes   = set()

    def on(self, selector):
        ev_log.debug('\n{self}.on({selector})'.format( self=repr(self),
                                                       selector=selector ))

        def decorator(callback):
            ev_log.debug('-> add callback: {callback}'.format( selector=selector,
                                                               callback=repr(callback) ))
            self.callbacks[selector].add(callback)
            def wrapper():
                return callback()

            return wrapper
        return decorator

    def off(self, selector):
        def decorator(callback):
            if selector and callback:
                self.callbacks[selector].remove(callback)
            elif selector:
                self.callbacks[selector] = set()
            else:
                self.callbacks = defaultdict(lambda: set())

            def wrapper():
                return callback()
            return wrapper
        return decorator

    def _handle_selector(self, selector):
        my_evt = Event(selector)

        for evt_sel in self.callbacks:
            sel_evt = Event(evt_sel)

            if sel_evt.is_selected_by(my_evt):
                ev_log.debug("-> matched: {selector}".format(selector=sel_evt.selector))

                for callback in self.callbacks[evt_sel]:
                    ev_log.debug("-> caused: {callback}".format(callback=str(callback)))
                    callback(my_evt)

    def emit(self, selector):
        ev_log.debug('\n{self}.emit({selector})'.format( self=repr(self),
                                                         selector=selector ))
        self._handle_selector(selector)
