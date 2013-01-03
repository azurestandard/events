
define(function() {
    function Event(evt_str) {
        var matches = (/([\/\w]+):([\w*]+)/).exec(evt_str);

        this.path = matches[1];
        this.type = matches[2];
    }

    Event.prototype.emit_on = function(event_emitter) {
        event_emitter.emit(this.selector(), this);
    }

    Event.prototype.forward_to = function(event_emitter) {
        event_emitter.emit(this.selector(), this);
    }

    Event.prototype.selector = function() {
        return this.path + ':' + this.type;
    };

    return Event;
});
