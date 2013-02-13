-- aquameta.db event subscriber functions for PostgreSQL


drop table subscriptions;
create table subscriptions( id serial,
                                session_id  varchar(30)  not null,
                                path        varchar(255) not null,
                                "type"      varchar(255) not null,
                                unique(session_id, path, "type") ); 


drop function event_session_id();
create function event_session_id() returns varchar as $$
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


drop function event_split_selector(event_selector varchar);
create function event_split_selector(event_selector varchar) returns varchar[] as $$
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

        selector_parts := event_split_selector(event_selector);
        raise notice '%', selector_parts;

        insert into subscriptions( session_id,
                                       path,
                                       type ) values ( event_session_id(),
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

        selector_parts := event_split_selector(event_selector);

        delete from subscriptions where session_id = event_session_id()
                                        and path = selector_parts[1]
                                        and "type" = selector_parts[2];
    end;
$$
language plpgsql;


drop function unsubscribe();
create function unsubscribe() returns void as $$
    begin
        unlisten *;

        delete from subscriptions where session_id = event_session_id();
    end;
$$
language plpgsql;


drop function event_emit() cascade;
create function event_emit() returns trigger as $$
    declare
        causing_ev varchar; -- selector identifying the actual changing item, payload of our notify
        causingevent_path varchar;
        causingevent_type varchar;
        emitted_ev varchar; -- channel through which we will emit an event
        object_id integer;
        subscr record;

    begin
        raise notice 'emit()';

        if TG_OP = 'DELETE' then
            causingevent_type := 'delete';
            object_id := OLD.id;

        elsif TG_OP = 'INSERT' then
            causingevent_type := 'insert';
            object_id := NEW.id;

        elsif TG_OP = 'UPDATE' then
            causingevent_type := 'update';
            object_id := NEW.id;

        end if;

        causingevent_path := '/' || current_database() || '/' || TG_RELNAME || '/' || object_id;
        causing_ev := causingevent_path || ':' || causingevent_type;

        raise notice '%', causing_ev;

        for subscr in ( select distinct path, "type"
                        from subscriptions
                        where causingevent_path like path || '%'
                          and ( causingevent_type = "type"
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
    for each row execute procedure event_emit();
