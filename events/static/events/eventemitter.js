
define(['events/event'], function(Event) {
    function EventEmitter() {
        this.callbacks = {};
        this.remotes = [];
    }

    EventEmitter.prototype.emit = function(selector) {
        var my_evt = new Event(selector);

        for(evt_sel in this.callbacks) {
            var sel_evt = new Event(evt_sel);

            if( sel_evt.path == my_evt.path.slice(0, sel_evt.path.length) &&
                ( sel_evt.type == my_evt.type ||
                  sel_evt.type == '*' )) {
                
                this.callbacks[evt_sel].forEach(function(callback) {
                    callback(my_evt);
                });
            }
        }
    }

    EventEmitter.prototype.on = function(selector) {
        var self = this;

        return function(callback) {
            if(self.callbacks[selector] === undefined) {
                self.callbacks[selector] = [];
            }

            self.callbacks[selector].push(callback);
        };
    };

    EventEmitter.prototype.off = function(selector) {
        var self = this;

        return function() {
            self.callbacks[selector] = [];
        };
    };

    EventEmitter.prototype.remote = function(url, subscriptions) {
        var self = this;

        var socket = io.connect(url);

        socket.on('event', function(data) {
            var evt = new Event(data);
            evt.emit_on(self);
        });

        socket.on('connect', function() {
            subscriptions.forEach(function(sub_sel) {
                socket.emit('subscribe', sub_sel);
            });
        });

        this.remotes.push(socket);
    };

    return EventEmitter;
});
