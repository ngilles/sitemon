
import re
import time

from datetime import datetime
from typing import Any, Optional, AsyncIterable

import asyncpg
import faust
import httpx

from faust.types.streams import StreamT

from .records import SiteInfo, MonitorReport
from .settings import settings
from .util import timed


app = faust.App('sitemon', broker=settings.kafka_broker)
reports_topic = app.topic('monitor_reports')


@app.agent(reports_topic)
async def reports_agent(reports: StreamT[MonitorReport]) -> None:
    pool = await asyncpg.create_pool(dsn=settings.postgres_dsn)

    async for report in reports:
        async with pool.acquire() as db:
            async with db.transaction():
                print(f'Processing report: {report}')
                print(await db.execute('''
                    INSERT INTO site_status (site_id, reachable, status_code, content_valid, latency, last_update) 
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (site_id) DO 
                        UPDATE SET
                        reachable = EXCLUDED.reachable,
                        status_code = EXCLUDED.status_code,
                        content_valid = EXCLUDED.content_valid,
                        latency = EXCLUDED.latency,
                        last_update = EXCLUDED.last_update
                    ''',
                    report.site_id,
                    report.response_complete,
                    report.response_code,
                    report.response_valid,
                    report.response_time,
                    report.timestamp,
                ))

                print(await db.execute('''INSERT INTO site_reports(site_id, timestamp, reachable, status_code, content_valid, latency)
                                    VALUES ($1, $2, $3, $4, $5, $6)''',
                                    report.site_id,
                                    report.timestamp,

                                    report.response_complete,
                                    report.response_code,
                                    report.response_valid,
                                    report.response_time,
                ))





@app.command()
async def test_data() -> None:
    print(await reports_agent.cast(MonitorReport(
        site_id=1,
        timestamp=datetime.now(),
        response_complete=True,
        response_time=0.1,
        response_code=200,
        response_valid=True,
    )))


def validate_regex_pattern(rp: str) -> Optional[re.Pattern]:
    if rp is None:
        return None

    try:
        return re.compile(rp)
    except re.error:
        print(f'Could not validate pattern ...')
        return None




async def scan_site(site_info):
    async with httpx.AsyncClient() as http:
        rtt, response = await timed(http.get, site_info.test_url)
        print(site_info, rtt, response)
        
        report = MonitorReport(
            site_id = 1,
            timestamp = datetime.now(),
            response_complete = True,
            response_time = rtt,
            response_code = response.status_code,
            response_valid = True,
        )

        await reports_agent.cast(report)

class SiteMonitor:
    def __init__(self):
        self._pool = None
        self.sites = []

    async def connect_db(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=settings.postgres_dsn)

    async def load_sites(self):
        async with self._pool.acquire() as db:
            sites = await db.fetch('''SELECT * FROM sites''')
            print(sites)

            site_infos = [SiteInfo(id=site['id'], name=site['name'], test_url=site['test_url'], regex=validate_regex_pattern(site['regex'])) for site in sites]
            print(site_infos)

            return site_infos

    async def scan_site():
        # scan the site
        pass

@app.command()
async def scan_sites():
    sm = SiteMonitor()
    await sm.connect_db()
    site_infos = await sm.load_sites()
    for site in site_infos:
        await scan_site(site)


@app.command()
async def monitor_sites():
    sm = SiteMonitor()
    await sm.start_monitoring()


if __name__ == '__main__':
    app.main()
