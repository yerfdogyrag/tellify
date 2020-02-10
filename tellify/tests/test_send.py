"""
Test basic event send handling.
"""

from tellify.tellify import Tellify
# from pytest_redis import factories
from tellify.tests.plugins.plug1 import Plug1


def test_send1(redis, loop):
    """
    We're looking to make
    sure that the Test1EventHandler gets the events that
    it expects and it's not called when it shouldn't.
    """
    async def ts1():
        tellify = Tellify(redis)
        tellify.add_user_event_handler(Plug1)

        # Set up configuration for this EventHandler
        ev_config = dict(Project="p1", User="u1", BlockList="b1,b2")
        testplug1 = Plug1()
        await testplug1.set_config(ev_config, redis)

        await tellify.load_configs()
        ev = dict(Project="p1", User="u1", Block="b1", message="Hi There")
        tellify.send_event(ev)
        assert testplug1.last_event == ev

    loop.run_until_complete(ts1())

