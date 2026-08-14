"""Cleanup hooks for tests that start a real Home Assistant runtime."""

from __future__ import annotations

import gc


def pytest_sessionfinish() -> None:
    """Keep remaining stopped-HA cycles out of interpreter finalization.

    The runtime helper has already unloaded every live entry and stopped HA. CPython
    3.14 can still crash while finalizing the remaining Sensor/Number descriptor
    cycles after pytest has reported success. Freezing only at session finish avoids
    that interpreter teardown fault without affecting test execution or assertions.
    """
    gc.collect()
    gc.freeze()
