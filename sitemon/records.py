from datetime import datetime
from re import Pattern
from typing import Optional

import faust


class SiteInfo(faust.Record, coerce=True):
    id: int
    name: str
    test_url: str
    regex: Pattern


class MonitorReport(faust.Record, coerce=True):
    site_id: int
    timestamp: datetime
    response_complete: bool
    response_time: Optional[float]
    response_code: Optional[int]
    response_valid: Optional[bool]
