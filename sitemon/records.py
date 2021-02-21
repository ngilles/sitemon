
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
    
    #site_url: str
    timestamp: datetime
    response_complete: bool
    response_time: float
    response_code: int
    response_valid: Optional[bool]