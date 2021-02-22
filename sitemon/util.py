import time
from typing import Any, Callable, Tuple


async def timed(fn: Callable, *args, **kwargs) -> Tuple[float, Any]:
    '''Times the runtime of the given function call.'''

    time_started = time.monotonic()
    result = await fn(*args, **kwargs)
    time_finished = time.monotonic()

    return (time_finished - time_started), result
