Aquameta Events
===============

A set of bindings to various event systems which applies a uniform interface to each.  Two core abstractions are Events and EventEmitters.  Events are emitted and subscribed to by EventEmitters.  EventEmitters can either stand-alone or be connected to various external event systems.

Events are identified by selectors, which are arbitrary URL-like strings such as:

    /customer/3/cart:checkout
    /orders/5:delete
    /orders:*
    
If `/orders/3:change` is emitted on an EventEmitter, handlers bound to `/orders:*` will fire on that EventEmitter.

Examples
--------

### Redis PubSub → SocketIO Client (werkzeug wsgi app)

#### Event Forwarding

    from events.engines.socket_io import SocketIOEventEmitter, handle_socketio_request
    from events.engines.redis import RedisEventEmitter
    from http import Request
    from redis import Redis
                                        
    def app(environ, start_response):                                                                                                                                                              
        request = Request(environ)
                  
        io_ev = SocketIOEventEmitter('/events')
        rs_ev = RedisEventEmitter(Redis(), 'events')
        rs_ev.on('/:*')(lambda evt: evt.forward_to(io_ev))
        
        handle_socketio_request(request, [io_ev])
        
#### Example use via Redis elsewhere

    from events.engines.redis import RedisEventEmitter
    from redis import Redis
    
    rs_ev = RedisEventEmitter(Redis(), 'events')
    rs_ev.emit('/customers/3:change')

