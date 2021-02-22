
import asyncio
import logging
import re

from datetime import datetime
from typing import Optional, List

import httpx

from .records import SiteInfo, MonitorReport
from .settings import settings
from .util import timed

log = logging.getLogger(__name__)



class SiteMonitor:
    '''Site Monitor.

    '''
    def __init__(self, sites: List[SiteInfo], reports_agent, scan_interval=60, max_concurrent_checks=100):
        self._pool = None
        self._sites = sites
        self._reports_agent = reports_agent

        if max_concurrent_checks < 1:
            raise ValueError('Concurrency must be at least 1')

        self._concurrent_checks = asyncio.Semaphore(max_concurrent_checks)


    async def scan_site(self, site: SiteInfo):
        '''Gather the metrics for a Site.

        :param SiteInfo site: The site to scan.

        This method scans the site by performing a get request
        to the site `test_url`. The success of the request, as
        well as the response time, and status code are recorded.
        The content of the response is matched against a regular
        expression if provided, and the result of is also included
        in the report. The report is then published to the relevant
        kafka stream.

        The content of the response is assumed valid if no regex
        was provided.

        Any number of site scans can be performed can be requested,
        but they will be bounded by the `_concurrent_checks` semaphore.
        '''
        async with self._concurrent_checks:
            log.info(f'Starting check for site {site.id}: {site.test_url}')
            async with httpx.AsyncClient() as http:
                timestamp = datetime.now()
                try:
                    # Perform the request, measuring the time taken
                    rtt, response = await timed(http.get, site.test_url)
                    log.info(f'Check for site {site.id} completed in {rtt}s ({response.status_code})')
                    
                    # Check the contents against provided regex
                    if site.regex:
                        valid_content = site.regex.search(response.text) is not None
                    else:
                        # Assume content valid if no regex was provided
                        valid_content = True

                    report = MonitorReport(
                        site_id = site.id,
                        timestamp = timestamp,
                        response_complete = True,
                        response_time = rtt,
                        response_code = response.status_code,
                        response_valid = valid_content,
                    )

                except httpx.HTTPError as e:
                    log.warn(f'Error connecting to site {site.id}: {e}')
                    report = MonitorReport(
                        site_id = site.id,
                        timestamp = timestamp,
                        response_complete = False,
                        response_time = None,
                        response_code = None,
                        response_valid = None,
                    )

                # Publish the report
                await self._reports_agent.cast(report)


    async def scan_sites(self):
        '''Run the site scans.
        
        All the scans are created as separate tasks and are
        waited upon before returning.
        '''
        checkers = [
            asyncio.create_task(self.scan_site(site))
            for site in self._sites
        ]

        # Wait for all checks to be completed
        await asyncio.wait(checkers)


    async def run(self):
        '''Run the scan loop infinitely.'''
        while True:
            await self.scan_sites()
            await asyncio.sleep(settings.scan_interval)