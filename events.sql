-- aquameta.db event subscriber functions for PostgreSQL


drop table _ev_subscriptions;
create table _ev_subscriptions( id serial,
                                session_id  varchar(30)  not null,
                                path        varchar(255) not null,
                                "type"      varchar(255) not null,
                                unique(session_id, path, "type") ); 


drop function _ev_session_id();
create function _ev_session_id() returns varchar as $$
    declare
        bknd_start varchar;
        bknd_pid varchar;
        sess_id varchar;

    begin
        select procpid::varchar, backend_start
        from pg_stat_activity
        into bknd_pid, bknd_start
        where datname = current_database()
          and usename = session_user
          and client_addr = inet_client_addr()
          and client_port = inet_client_port();

        sess_id := (bknd_pid || regexp_replace(bknd_start, '[-:. ]', '', 'g'));

        return sess_id;
    end;
$$
language plpgsql;


drop function _ev_split_selector(event_selector varchar);
create function _ev_split_selector(event_selector varchar) returns varchar[] as $$
    begin
        return regexp_matches(event_selector, '([/\w]+):([*\w]+)');
    end;
$$
language plpgsql immutable;


drop function subscribe(event_selector varchar);
create function subscribe(event_selector varchar) returns void as $$
    declare
        selector_parts text[];

    begin
        execute 'listen ' || quote_ident(event_selector);

        selector_parts := _ev_split_selector(event_selector);
        raise notice '%', selector_parts;

        insert into _ev_subscriptions( session_id,
                                       path,
                                       type ) values ( _ev_session_id(),
                                                       selector_parts[1],
                                                       selector_parts[2] );
    end;
$$
language plpgsql;


drop function unsubscribe(event_selector varchar);
create function unsubscribe(event_selector varchar) returns void as $$
    declare
        selector_parts text[];
    
    begin
        execute 'unlisten ' || quote_ident(event_selector);

        selector_parts := _ev_split_selector(event_selector);

        delete from _ev_subscriptions where session_id = _ev_session_id()
                                        and path = selector_parts[1]
                                        and "type" = selector_parts[2];
    end;
$$
language plpgsql;


drop function unsubscribe();
create function unsubscribe() returns void as $$
    begin
        unlisten *;

        delete from _ev_subscriptions where session_id = _ev_session_id();
    end;
$$
language plpgsql;


drop function _ev_emit() cascade;
create function _ev_emit() returns trigger as $$
    declare
        causing_ev varchar; -- selector identifying the actual changing item, payload of our notify
        causing_ev_path varchar;
        causing_ev_type varchar;
        emitted_ev varchar; -- channel through which we will emit an event
        object_id integer;
        subscr record;

    begin
        raise notice 'emit()';

        if TG_OP = 'DELETE' then
            causing_ev_type := 'delete';
            object_id := OLD.id;

        elsif TG_OP = 'INSERT' then
            causing_ev_type := 'insert';
            object_id := NEW.id;

        elsif TG_OP = 'UPDATE' then
            causing_ev_type := 'update';
            object_id := NEW.id;

        end if;

        causing_ev_path := '/' || current_database() || '/' || TG_RELNAME || '/' || object_id;
        causing_ev := causing_ev_path || ':' || causing_ev_type;

        raise notice '%', causing_ev;

        for subscr in ( select distinct path, "type"
                        from _ev_subscriptions
                        where causing_ev_path like path || '%'
                          and ( causing_ev_type = "type"
                                or "type" = '*' ) ) loop

            emitted_ev := subscr.path || ':' || subscr."type";
            raise notice '%', emitted_ev;

            raise notice 'pg_notify(%, %)', emitted_ev, causing_ev;

            perform pg_notify(emitted_ev, causing_ev);

        end loop;

        return null;
    end;
$$
language plpgsql;


drop trigger emit_customers_trigger on customers;
create trigger emit_customers_trigger
    after insert or update or delete on customers
    for each row execute procedure _ev_emit();
