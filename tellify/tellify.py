import logging
import json
import uuid
from typing import Type
from aioredis.commands import Redis


class EventHandler:
    """
    Pure virtual class - user event handlers should inherit from this.
    """

    def __init__(self, config=None):
        self.config = config

    async def set_config(self, config, redis: Redis):
        """
        Saves configuration off to redis.
        @param config:
        @param redis:
        """
        self.config = config

        # If there's an ID, we're overwriting an existig one
        if "tellify_id" not in self.config:
            config["tellify_id"] = str(uuid.uuid1())
        ev_id = config["tellify_id"]
        ev_name = type(self).__name__
        config['tellify_EventHandlerClass'] = ev_name
        await redis.set(ev_id, json.dumps(self.config))
        await redis.sadd("event_handlers", ev_id)

    def required_fields(self) -> set:
        assert self
        return set()

    def match_fields(self) -> set:
        """
        @return: set of (field-name, field-value) tuples
        """
        assert self
        return set()


class ConfigBuilder:
    def __init__(self, title):
        self.title = title
        self.params = []

    def add_string(self, strname, description=None):
        param = dict(name=strname, description=description)
        self.params.append(param)

    def config_parameters(self):
        return self.params


class Tellify:
    def __init__(self, redis: Redis):
        """
        @param redis: Redis
        """
        self.redis = redis
        self._reset_configs()

        # Key=EventHandlerClass name, value=class
        self.event_handler_classes = dict()

    def _reset_configs(self):
        """
        These items should be reset whenever we reload our configs
        @return:
        """
        # Key=uuid, value=EventHandler object
        self.event_handlers = dict()
        # All possible parameters and fixed values across all EventHandlers
        self.all_params = set()
        # Which keys to convert to tuples in all_params
        self.all_match_keys = set()
        # key=event key, value=[list of EventHandlers to give this event to]
        self.ev_dispatch = dict()

    def add_user_event_handler_class(self, event_handler_class: Type[EventHandler]):
        """
        Register the specified event handler with the system.
        @type event_handler_class: EventHandler
        """
        ev_name = event_handler_class.__name__
        self.event_handler_classes[ev_name] = event_handler_class

    async def load_configs(self):
        """
        This loads (or reloads) all the EventConfigs from redis
        """
        # Clear everything out - see __init__ for docs
        redis = self.redis
        self._reset_configs()
        ev_config_ids = await redis.smembers("event_handlers")
        recs = await redis.mget(ev_config_ids)
        for ev_config_json in recs:
            ev_config = json.loads(ev_config_json)
            ev_class = ev_config['tellify_EventHandlerClass']
            ev_id = ev_config['tellify_id']

            print("Loading:", ev_class, ev_id)
            if ev_class not in self.event_handler_classes:
                logging.error(f"No plugin found for EventHandler '{ev_class}'.")
                continue

            # Instantiate a new instance of the user EventHandler
            ev_handler = self.event_handler_classes[ev_class]
            eh = ev_handler(ev_config)
            # Look at what parameters this EventHandler will be
            # looking for so we can optimize dispatch
            required = eh.required_fields()
            matches = eh.match_fields()
            self.all_params.update(required)
            self.all_params.update(matches)
            self.all_match_keys.update(required)
            self.all_match_keys.update([ii[0] for ii in matches])
            self.event_handlers[ev_id] = eh

    def send_event(self, event):
        """
        Send matching events to every eventhandler
        This works by converting parts of the event into a frozenset which
        we can compare against other frozensets that we've seen
        previously.  It pretty much means we can dispatch to all
        the event handlers without having to scan each one more
        than the first time.
        @type event: dict
        """

        ev_keys = set(event.keys())
        ev_key = ev_keys & self.all_params
        for k in ev_keys & self.all_match_keys:
            ev_key.add((k, event[k]))

        ev_fkey = frozenset(ev_key)
        # If we don't have a match here, we have to go through
        # all the EventHandlers and add them to the list.  We should
        # only have to do this once for each event pattern.
        if ev_fkey not in self.ev_dispatch:
            # We don't have a match, so need to go through all the
            # configs to look for ones that really do match.
            eh_list = []
            for eh in self.event_handlers.values():
                req = eh.required_fields()
                if not ev_fkey.issuperset(req):
                    continue
                for k, v in eh.match_fields():
                    if k not in event or event[k] != v:
                        break
                else:
                    # They all match - add this one
                    eh_list.append(eh)
            self.ev_dispatch[ev_fkey] = eh_list

        for eh in self.ev_dispatch[ev_fkey]:
            # TODO: Make this a dispatcher rather than a call
            eh.event_handler(self, event)
