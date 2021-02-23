from datetime import datetime
from re import Pattern
from typing import Optional

import faust


class SiteInfo(faust.Record, coerce=True):  # pylint: disable=W0223
    id: int
    name: str
    test_url: str
    regex: Optional[Pattern]


class MonitorReport(faust.Record, coerce=True):  # pylint: disable=W0223
    site_id: int
    timestamp: datetime
    response_complete: bool
    response_time: Optional[float]
    response_code: Optional[int]
    response_valid: Optional[bool]
