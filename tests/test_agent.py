# pylint: disable=redefined-outer-name
# Avoid pylint errors when fixture are defined in same file as used

from datetime import datetime

import asyncpg
import pytest
from sitemon.main import app, reports_agent
from sitemon.records import MonitorReport
from sitemon.settings import settings

# https://faust.readthedocs.io/en/latest/userguide/testing.html


@pytest.fixture()
def test_app(event_loop):  # pylint: disable=unused-argument
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'  # make sure tables are clean for tests
    app.flow_control.resume()
    return app


@pytest.fixture()
@pytest.mark.asyncio()
async def test_db():
    db = await asyncpg.connect(dsn=settings.postgres_dsn)

    # Make sure site 0 (test) is present
    await db.execute(
        '''
        INSERT INTO sites(id, name, enabled, test_url)
        VALUES (0, 'test', FALSE, 'https://example.com')
        ON CONFLICT DO NOTHING;
        '''
    )

    yield db

    # Clean up test values from db
    await db.execute('''DELETE FROM site_reports WHERE site_id = 0;''')
    await db.close()


@pytest.mark.asyncio()
async def test_agent_db_write(test_app, test_db):  # pylint: disable=unused-argument
    async with reports_agent.test_context() as agent:
        now = datetime(2021, 2, 14, 10, 27, 00)

        # Send a report to the agent
        await agent.put(
            MonitorReport(
                site_id=0,
                timestamp=now,
                response_complete=True,
                response_time=1,
                response_code=200,
                response_valid=True,
            )
        )

        # Attempt to fetch the row back and compare values
        row = await test_db.fetchrow('SELECT * FROM site_reports WHERE site_id = 0 AND timestamp = $1;', now)

        assert row['reachable'] is True
        assert row['latency'] == 1
        assert row['status_code'] == 200
        assert row['content_valid'] is True
