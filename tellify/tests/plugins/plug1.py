from tellify.tellify import EventHandler, ConfigBuilder

global Plug1_events
# Key=plug name, value=[list of events matched]
Plug1_events = dict()

class Plug1(EventHandler):
    last_event: dict

    def event_handler(self, tellify, event: dict):
        # Check to make sure that everything matches what we expect
        # If there's a ',' in the config value, we match on any of them
        name = self.config['Project']
        for k, v in self.config.items():
            if k.startswith('tellify_'):
                continue
            if k not in event:
                return False
            ev_val = event[k]
            if ',' in v:
                if ev_val not in v.split(','):
                    return False
            else:
                if ev_val != v:
                    return False

        Plug1_events.setdefault(name, []).append(event)
        assert tellify
        return True

    def title(self):
        assert self
        return "plug1"

    def description(self):
        assert self
        return "plug1 longer description"

    def required_fields(self):
        assert self
        return set("User Block".split())

    def match_fields(self):
        project = self.config["Project"]
        return {("Project", project)}

    def get_config_parameters(self):
        b = ConfigBuilder(self.title())
        b.add_string("User", description="Person's username name")
        b.add_string(
            "BlockList", description="List of blocks, comma separated.  Must be lowercase"
        )
        return b.config_parameters()

    def validate_parameters(self, config):
        assert self
        errors = []  # (field, error message)
        if not config["Name"]:
            errors.append(("Name", "Name must be filled out"))
        block = config["Block"]
        if block != block.lower():
            errors.append(("Block", "Block must be lower case"))


        return errors
