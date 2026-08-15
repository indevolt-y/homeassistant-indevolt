"""Real Home Assistant concurrency and shutdown-boundary contracts."""

from __future__ import annotations

import asyncio
from collections import Counter

import pytest

from custom_components.indevolt.const import DOMAIN
from custom_components.indevolt.opendata.additional_points import (
    DEFAULT_ADDITIONAL_READ_GROUPS,
)
from custom_components.indevolt.opendata.polling import DEFAULT_POLLING_BASELINE

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    device_for_serial,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
    state_for_unique_id,
)

DEFAULT_BATCH_COUNT = (len(DEFAULT_POLLING_BASELINE) + 7) // 8 + sum(
    (len(group) + 7) // 8 for group in DEFAULT_ADDITIONAL_READ_GROUPS
)


@pytest.mark.asyncio
async def test_two_explicit_refreshes_are_serialized_and_both_complete(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.110": backend})
    entry = make_entry(
        host="192.0.2.110",
        serial="SERIAL-REFRESH-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data
        backend.fetches.clear()

        first_fetch_started = asyncio.Event()
        release_first_fetch = asyncio.Event()
        active_fetches = 0
        maximum_active_fetches = 0

        async def pause_first_fetch(_keys: list[int]) -> None:
            nonlocal active_fetches, maximum_active_fetches
            active_fetches += 1
            maximum_active_fetches = max(maximum_active_fetches, active_fetches)
            try:
                if len(backend.fetches) == 1:
                    first_fetch_started.set()
                    await release_first_fetch.wait()
            finally:
                active_fetches -= 1

        backend.before_fetch = pause_first_fetch
        first_refresh = asyncio.create_task(coordinator.async_refresh())
        await asyncio.wait_for(first_fetch_started.wait(), timeout=2)
        second_refresh = asyncio.create_task(coordinator.async_refresh())
        await asyncio.sleep(0)

        assert backend.fetches == [
            [field.point for field in DEFAULT_POLLING_BASELINE[:8]]
        ]
        assert second_refresh.done() is False
        assert maximum_active_fetches == 1

        release_first_fetch.set()
        await asyncio.gather(first_refresh, second_refresh)

        assert len(backend.fetches) == DEFAULT_BATCH_COUNT * 2
        assert maximum_active_fetches == 1
        assert coordinator.last_update_success is True


@pytest.mark.asyncio
async def test_queued_refresh_recovers_after_an_earlier_batch_fails(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.111": backend})
    entry = make_entry(
        host="192.0.2.111",
        serial="QUEUED-RECOVERY-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data
        backend.fetches.clear()
        backend.data["142"] = 4096

        first_refresh_started = asyncio.Event()
        release_first_refresh = asyncio.Event()
        recovery_refresh_started = asyncio.Event()
        release_recovery_refresh = asyncio.Event()
        failure_raised = False

        async def control_batches(_keys: list[int]) -> None:
            nonlocal failure_raised
            call_number = len(backend.fetches)
            if call_number == 1:
                first_refresh_started.set()
                await release_first_refresh.wait()
            elif call_number == 3 and not failure_raised:
                failure_raised = True
                raise RuntimeError("third batch failed")
            elif call_number == 4:
                recovery_refresh_started.set()
                await release_recovery_refresh.wait()

        backend.before_fetch = control_batches
        failed_refresh = asyncio.create_task(coordinator.async_refresh())
        await asyncio.wait_for(first_refresh_started.wait(), timeout=2)
        recovery_refresh = asyncio.create_task(coordinator.async_refresh())
        release_first_refresh.set()
        await asyncio.wait_for(recovery_refresh_started.wait(), timeout=2)

        assert failed_refresh.done() is True
        assert coordinator.last_update_success is False
        assert (
            state_for_unique_id(hass, entry, "QUEUED-RECOVERY-SN_142").state
            == "unavailable"
        )

        release_recovery_refresh.set()
        await asyncio.gather(failed_refresh, recovery_refresh)
        await hass.async_block_till_done()

        assert failure_raised is True
        assert len(backend.fetches) == 3 + DEFAULT_BATCH_COUNT
        assert coordinator.last_update_success is True
        assert (
            state_for_unique_id(hass, entry, "QUEUED-RECOVERY-SN_142").state == "4096"
        )


@pytest.mark.asyncio
async def test_refresh_completes_while_number_write_waits_then_write_refreshes_again(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.112": backend})
    entry = make_entry(
        host="192.0.2.112",
        serial="WRITE-REFRESH-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data
        power_entity = entry_entities(hass, entry)["WRITE-REFRESH-SN_power_setting"]
        backend.fetches.clear()

        write_started = asyncio.Event()
        release_write = asyncio.Event()

        async def pause_write(
            _point: int,
            _value: list[int | float | None],
        ) -> None:
            write_started.set()
            await release_write.wait()

        backend.before_write = pause_write
        write_task = asyncio.create_task(
            hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": power_entity.entity_id, "value": 1200},
                blocking=True,
            )
        )
        await asyncio.wait_for(write_started.wait(), timeout=2)

        backend.data["142"] = 5000
        try:
            await asyncio.wait_for(coordinator.async_refresh(), timeout=2)
            assert write_task.done() is False
            assert len(backend.fetches) == DEFAULT_BATCH_COUNT
            assert (
                state_for_unique_id(hass, entry, "WRITE-REFRESH-SN_142").state == "5000"
            )
        finally:
            release_write.set()

        await write_task

        assert backend.writes == [(47016, [1200.0])]
        assert len(backend.fetches) == DEFAULT_BATCH_COUNT * 2
        assert coordinator.last_update_success is True


@pytest.mark.asyncio
async def test_simultaneous_number_services_do_not_drop_either_request(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.113": backend})
    entry = make_entry(
        host="192.0.2.113",
        serial="NUMBER-RACE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        backend.fetches.clear()

        await asyncio.gather(
            hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": entities["NUMBER-RACE-SN_backup_soc"].entity_id,
                    "value": 80,
                },
                blocking=True,
            ),
            hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": entities["NUMBER-RACE-SN_power_setting"].entity_id,
                    "value": 2200,
                },
                blocking=True,
            ),
        )

        assert Counter((point, tuple(value)) for point, value in backend.writes) == (
            Counter({(1142, (80.0,)): 1, (47016, (2200.0,)): 1})
        )
        assert len(backend.fetches) == DEFAULT_BATCH_COUNT * 2


@pytest.mark.asyncio
async def test_concurrent_actions_for_two_entries_remain_independent(
    monkeypatch,
    tmp_path,
) -> None:
    first = FakeDevice(dict(DEFAULT_DATA))
    second = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(
        monkeypatch,
        {"192.0.2.114": first, "192.0.2.115": second},
    )
    first_entry = make_entry(
        host="192.0.2.114",
        serial="ACTION-FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.115",
        serial="ACTION-SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)
        first_device = device_for_serial(hass, "ACTION-FIRST-SN")
        second_device = device_for_serial(hass, "ACTION-SECOND-SN")
        assert first_device is not None
        assert second_device is not None
        first.fetches.clear()
        second.fetches.clear()

        started_devices: set[str] = set()
        both_writes_started = asyncio.Event()
        release_writes = asyncio.Event()

        def make_write_hook(device_name: str):
            async def pause_first_write(
                _point: int,
                _value: list[int | float | None],
            ) -> None:
                started_devices.add(device_name)
                if len(started_devices) == 2:
                    both_writes_started.set()
                await release_writes.wait()

            return pause_first_write

        first.before_write = make_write_hook("first")
        second.before_write = make_write_hook("second")

        first_action = asyncio.create_task(
            hass.services.async_call(
                DOMAIN,
                "set_solidflex_powerflex_work_mode",
                {
                    "device_id": [first_device.id],
                    "mode": "Real-Time Control",
                    "state": "Charging",
                    "power": 1200,
                    "soc": 60,
                },
                blocking=True,
            )
        )
        second_action = asyncio.create_task(
            hass.services.async_call(
                DOMAIN,
                "set_solidflex_powerflex_work_mode",
                {
                    "device_id": [second_device.id],
                    "mode": "Real-Time Control",
                    "state": "Discharging",
                    "power": 2300,
                    "soc": 70,
                },
                blocking=True,
            )
        )
        await asyncio.wait_for(both_writes_started.wait(), timeout=2)

        assert first_action.done() is False
        assert second_action.done() is False
        assert started_devices == {"first", "second"}

        release_writes.set()
        await asyncio.gather(first_action, second_action)
        await hass.async_block_till_done()

        assert first.writes == [(47005, [4]), (47015, [1, 1200, 60])]
        assert second.writes == [(47005, [4]), (47015, [2, 2300, 70])]
        assert len(first.fetches) == DEFAULT_BATCH_COUNT
        assert len(second.fetches) == DEFAULT_BATCH_COUNT


@pytest.mark.asyncio
async def test_cancelled_number_service_does_not_poison_the_next_write(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.116": backend})
    entry = make_entry(
        host="192.0.2.116",
        serial="CANCEL-WRITE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        power_entity = entry_entities(hass, entry)["CANCEL-WRITE-SN_power_setting"]
        backend.fetches.clear()
        write_started = asyncio.Event()
        never_release = asyncio.Event()

        async def pause_write(
            _point: int,
            _value: list[int | float | None],
        ) -> None:
            write_started.set()
            await never_release.wait()

        backend.before_write = pause_write
        cancelled_call = asyncio.create_task(
            hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": power_entity.entity_id, "value": 1200},
                blocking=True,
            )
        )
        await asyncio.wait_for(write_started.wait(), timeout=2)
        cancelled_call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await cancelled_call

        backend.before_write = None
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": power_entity.entity_id, "value": 1300},
            blocking=True,
        )

        assert backend.writes == [(47016, [1200.0]), (47016, [1300.0])]
        assert len(backend.fetches) == DEFAULT_BATCH_COUNT
        assert entry.runtime_data.last_update_success is True


@pytest.mark.asyncio
async def test_shutdown_during_refresh_finishes_inflight_work_and_blocks_new_fetches(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.117": backend})
    entry = make_entry(
        host="192.0.2.117",
        serial="SHUTDOWN-REFRESH-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data
        backend.fetches.clear()
        backend.data["142"] = 6000
        fetch_started = asyncio.Event()
        release_fetch = asyncio.Event()

        async def pause_first_fetch(_keys: list[int]) -> None:
            if len(backend.fetches) == 1:
                fetch_started.set()
                await release_fetch.wait()

        backend.before_fetch = pause_first_fetch
        inflight_refresh = asyncio.create_task(coordinator.async_refresh())
        await asyncio.wait_for(fetch_started.wait(), timeout=2)

        await coordinator.async_shutdown()
        assert inflight_refresh.done() is False

        release_fetch.set()
        await inflight_refresh
        await hass.async_block_till_done()

        assert len(backend.fetches) == DEFAULT_BATCH_COUNT
        assert (
            state_for_unique_id(hass, entry, "SHUTDOWN-REFRESH-SN_142").state == "6000"
        )

        await coordinator.async_refresh()
        assert len(backend.fetches) == DEFAULT_BATCH_COUNT
