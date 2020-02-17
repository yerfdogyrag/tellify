"""
Test basic event send handling.
"""

from tellify.tellify import Tellify
# from pytest_redis import factories
from tellify.tests.plugins.plug1 import Plug1, Plug1_events


def test_send1(redis, loop):
    """
    We're looking to make
    sure that the Test1EventHandler gets the events that
    it expects and it's not called when it shouldn't.
    """
    async def ts1():
        tellify = Tellify(redis)
        tellify.add_user_event_handler_class(Plug1)

        # Set up configuration for this EventHandler
        ev_config1 = dict(Project="p1", User="u1", Block="b1,b2")
        testplug1 = Plug1()
        await testplug1.set_config(ev_config1, redis)
        await tellify.load_configs()

        # Send our event and verify it made it through
        ev0 = dict(Project="p1", User="u1", Block="b1", message="Hi There")
        tellify.send_event(ev0)
        p1_ev = Plug1_events['p1']
        assert p1_ev[0] == ev0
        assert len(p1_ev) == 1

        # This one doesn't match project so it shouldn't make it through
        ev = dict(Project="p2", User="u1", Block="b1", message="Hi There")
        tellify.send_event(ev)
        assert len(p1_ev) == 1

        # This one doesn't match on the block
        ev = dict(Project="p2", User="u1", Block="b1", message="Hi There")
        tellify.send_event(ev)
        assert len(p1_ev) == 1

        # This one doesn't match on missing project
        ev = dict(User="u1", Block="b1", message="Hi There")
        tellify.send_event(ev)
        assert len(p1_ev) == 1

        # Set up new event configuration (new project and blocks)
        ev_config2 = dict(Project="p2", User="u1", Block="b3,b4")
        testplug2 = Plug1()
        await testplug2.set_config(ev_config2, redis)
        await tellify.load_configs()

        # This should match 2, not 1
        ev = dict(Project="p2", User="u1", Block="b3", message="Hi There")
        tellify.send_event(ev)
        p2_ev = Plug1_events['p2']
        assert len(p1_ev) == 1
        assert len(p2_ev) == 1
        assert p2_ev[0] == ev

    loop.run_until_complete(ts1())

