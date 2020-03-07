from tellify.tellify import Tellify
# from pytest_redis import factories
from tellify.tests.plugins.plug1 import Plug1, Plug1_events, Plug1_alarms


def test_store_alert(redis, loop):
    async def ts1():
        tellify = Tellify(redis)
        tellify.add_user_event_handler_class(Plug1)

        # Set up configuration for this EventHandler
        ev_config1 = dict(Project="p1", User="u1", Block="b1,b2")
        testplug1 = Plug1()
        await testplug1.set_config(ev_config1, redis)
        await tellify.load_configs()

        # Send our event that should store an alarm
        ev0 = dict(Project="p1", User="u1", Block="b1", message="Did Not Pass", status="fail")
        tellify.send_event(ev0)
        p1_al_id, p1_al_config = Plug1_alarms[0]
        assert p1_al_id is not None
        assert p1_al_config == ev0

    loop.run_until_complete(ts1())
