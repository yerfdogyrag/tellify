from tellify.tellify import EventHandler, ConfigBuilder


class Plug1(EventHandler):
    last_event: dict

    def __init__(self, *args, **kwargs):
        self.last_event = None
        super().__init__(self, *args, **kwargs)

    def event_handler(self, tellify, event: dict):
        assert tellify
        self.last_event = event

    def title(self):
        assert self
        return "plug1"

    def description(self):
        assert self
        return "plug1 longer description"

    def required_fields(self):
        assert self
        return set("Name Block".split())

    def match_fields(self):
        project = self.config["Project"]
        return {("Project", project)}

    def get_config_parameters(self):
        b = ConfigBuilder(self.title())
        b.add_string("Name", help="Person's name")
        b.add_string(
            "BlockList", help="List of blocks, comma separated.  Must be lowercase"
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
