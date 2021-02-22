import logging
import re
import ssl
from datetime import datetime
from typing import List, Optional

import asyncpg
import faust
from faust.types.streams import StreamT

from .monitor import SiteMonitor
from .records import MonitorReport, SiteInfo
from .settings import settings

log = logging.getLogger(__name__)

extra_kwargs = {}

# SSL Support for Kafka connection
if settings.kafka_auth_ca:
    if not settings.kafka_access_key or not settings.kafka_access_crt:
        print('All of CA, access key and access certificate need to be specified for SSL support')
        raise Exception('Incomplete SSL configuration')

    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=str(settings.kafka_auth_ca))
    ssl_context.load_cert_chain(str(settings.kafka_access_crt), keyfile=str(settings.kafka_access_key))
    extra_kwargs['broker_credentials'] = ssl_context

app = faust.App('sitemon', broker=settings.kafka_broker, **extra_kwargs)
reports_topic = app.topic('monitor_reports')


@app.agent(reports_topic)
async def reports_agent(reports: StreamT[MonitorReport]) -> None:
    '''The Agent responsible storing the site monitoring reports.

    The agent consume the elements coming in from the Kafka reports
    stream and stores them in the postgres database. The reports are
    store in the log, as well as a current status table. This is
    performed within a transaction. Order (per site) is guaranteed
    by the Kafka stream.

    A connection pool is used to manage the connections to the
    database and will handle some connection failures. In case
    of errors during the insertion in the db, the data point may be
    lost. The agent will be restarted automatically (by Faust).
    '''
    pool = await asyncpg.create_pool(dsn=settings.postgres_dsn)

    async for report in reports:
        async with pool.acquire() as db:
            async with db.transaction():
                log.info('Processing report: %s', report)
                await db.execute(
                    '''
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
                )

                await db.execute(
                    '''INSERT INTO site_reports(site_id, timestamp, reachable, status_code, content_valid, latency)
                                    VALUES ($1, $2, $3, $4, $5, $6)''',
                    report.site_id,
                    report.timestamp,
                    report.response_complete,
                    report.response_code,
                    report.response_valid,
                    report.response_time,
                )


def validate_regex_pattern(rp: str) -> Optional[re.Pattern]:
    '''Compile a regex pattern, returning None if invalid.'''
    if rp is None:
        return None

    try:
        return re.compile(rp)
    except re.error:
        return None


def parse_site_info(site) -> SiteInfo:
    '''Create a SiteInfo record from a database record/dict.

    :param record site:
        The db record for the site, containing:
        **id**: The numerical id
        **name**: The human readable name of the site
        **test_url**: The URL to use as for the testing
        **regex**: An optional regex string use to test site content
    '''

    if site['regex'] is not None:
        pattern = validate_regex_pattern(site['regex'])
        if pattern is None:
            log.warning('Regex pattern for site %d is invalid, ignoring...', site['id'])
    else:
        pattern = None

    return SiteInfo(id=site['id'], name=site['name'], test_url=site['test_url'], regex=pattern)


async def load_sites_from_db(db) -> List[SiteInfo]:
    '''Loads site configurations from the database.

    :param connnection db: The asyncpg database connection to use.
    '''
    try:
        sites = await db.fetch('''SELECT id, name, test_url, regex FROM sites WHERE enabled = true;''')

        return [parse_site_info(site) for site in sites]

    except Exception as e:
        log.error('Could not load sites from database...')
        raise e


@app.command()
async def test_data() -> None:
    print(
        await reports_agent.cast(
            MonitorReport(
                site_id=1,
                timestamp=datetime.now(),
                response_complete=True,
                response_time=0.1,
                response_code=200,
                response_valid=True,
            )
        )
    )


@app.command()
async def monitor_sites():
    '''Runs the site monitor, gathering the website metrics.'''

    # Connect to DB to retrieve site infos
    db = await asyncpg.connect(dsn=settings.postgres_dsn)
    sites = await load_sites_from_db(db)
    await db.close()

    # Start and run the Site Monitor
    site_monitor = SiteMonitor(sites, reports_agent, scan_interval=settings.scan_interval)
    await site_monitor.run()  # Runs forever


# Allow the script to be called directly and handle the Faustiness
if __name__ == '__main__':
    app.main()
