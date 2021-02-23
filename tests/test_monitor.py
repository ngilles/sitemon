import re

import pytest
from sitemon.monitor import SiteMonitor
from sitemon.records import MonitorReport, SiteInfo


class MockReportAgent:
    def __init__(self):
        self.report: MonitorReport = None

    async def cast(self, report):
        self.report = report


@pytest.mark.parametrize(
    "site_info, complete, status_code, content_valid",
    [
        (SiteInfo(id=0, name="test", test_url="https://example.com"), True, 200, True),  # nominal
        (SiteInfo(id=0, name="test", test_url="https://jcpasty.fr/ntsh"), True, 404, True),  # 404, different status code
        (SiteInfo(id=0, name="test", test_url="https://example-fake.com"), False, None, None),  # unreachable
        (SiteInfo(id=0, name="test", test_url="https://microsoft.com",
                  regex=re.compile("Google")), True, 200, False),  # regex no match
        (SiteInfo(id=0, name="test", test_url="https://google.com",
                  regex=re.compile("Google")), True, 200, True),  # regex match
    ]
)
@pytest.mark.asyncio
async def test_scanner(site_info, complete, status_code, content_valid):
    '''Test the site scanner.'''

    agent = MockReportAgent()
    sm = SiteMonitor([], agent)
    await sm.scan_site(site_info)

    assert agent.report.response_complete == complete
    assert agent.report.response_code == status_code
    assert agent.report.response_valid == content_valid
