import sys
import pytest
import asyncio
from mockaioredis import MockRedis

@pytest.fixture
def redis():
    return MockRedis(strict=True, decode_responses=True)

# stolen from aioredis code
@pytest.yield_fixture
def loop():
    """Creates new event loop."""
    aloop = asyncio.new_event_loop()
    if sys.version_info < (3, 8):
        asyncio.set_event_loop(aloop)

    try:
        yield aloop
    finally:
        if not aloop.is_closed():
            aloop.call_soon(aloop.stop)
            aloop.run_forever()
            aloop.close()