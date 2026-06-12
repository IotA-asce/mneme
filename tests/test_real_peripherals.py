from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from android_brain_memory import (
    MnemeRuntime,
    PeripheralDiscoveryService,
    PeripheralKind,
    RealPeripheralBackend,
    RuntimeClock,
)


MIGRATIONS = Path(__file__).resolve().parents[1] / "storage" / "migrations"


class StubCommands:
    def __init__(self, outputs: dict[tuple[str, ...], str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str], timeout_ms: int) -> str:
        key = tuple(command)
        self.calls.append(key)
        if key not in self.outputs:
            raise FileNotFoundError(key[0])
        return self.outputs[key]


def test_real_peripheral_backend_parses_macos_system_profiler_json():
    payload = {
        "SPCameraDataType": [
            {"_name": "FaceTime HD Camera", "unique_id": "cam-1"},
        ],
        "SPAudioDataType": [
            {
                "_name": "Built-in Microphone",
                "coreaudio_device_input": "Yes",
            },
            {
                "_name": "MacBook Pro Speakers",
                "coreaudio_device_output": "Yes",
            },
        ],
    }
    runner = StubCommands({
        ("system_profiler", "-json", "SPCameraDataType", "SPAudioDataType"): json.dumps(payload)
    })
    backend = RealPeripheralBackend(platform_name="Darwin", command_runner=runner)

    devices = backend.scan()

    assert [device.kind for device in devices] == [
        PeripheralKind.CAMERA,
        PeripheralKind.MICROPHONE,
        PeripheralKind.SPEAKER,
    ]
    assert {device.label for device in devices} == {
        "FaceTime HD Camera",
        "Built-in Microphone",
        "MacBook Pro Speakers",
    }
    assert all(device.metadata["backend"] == "real" for device in devices)


def test_real_peripheral_backend_parses_linux_inventory_tools():
    runner = StubCommands({
        ("v4l2-ctl", "--list-devices"): "USB Camera:\n\t/dev/video0\n\n",
        ("arecord", "-l"): "card 0: Audio [USB Audio], device 0: USB Microphone [USB Microphone]\n",
        ("aplay", "-l"): "card 0: Audio [USB Audio], device 0: USB Speaker [USB Speaker]\n",
        ("pactl", "list", "short", "sources"): "0\talsa_input.usb-mic\tmodule\tformat\n",
        ("pactl", "list", "short", "sinks"): "1\talsa_output.usb-speaker\tmodule\tformat\n",
    })
    backend = RealPeripheralBackend(platform_name="Linux", command_runner=runner)

    devices = backend.scan()

    assert any(device.kind == PeripheralKind.CAMERA and device.label == "USB Camera" for device in devices)
    assert any(device.kind == PeripheralKind.MICROPHONE for device in devices)
    assert any(device.kind == PeripheralKind.SPEAKER for device in devices)


def test_real_peripheral_backend_parses_windows_pnp_json():
    payload = [
        {"Name": "Integrated Camera", "DeviceID": "cam-1", "PNPClass": "Camera", "Status": "OK"},
        {"Name": "Microphone Array", "DeviceID": "mic-1", "PNPClass": "AudioEndpoint", "Status": "OK"},
        {"Name": "Speakers", "DeviceID": "speaker-1", "PNPClass": "AudioEndpoint", "Status": "OK"},
    ]
    runner = StubCommands({
        (
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.PNPClass -in @('Camera','Image','AudioEndpoint','Media') } | "
            "Select-Object Name,DeviceID,PNPClass,Status | ConvertTo-Json -Depth 3",
        ): json.dumps(payload)
    })
    backend = RealPeripheralBackend(platform_name="Windows", command_runner=runner)

    devices = backend.scan()

    assert [device.kind for device in devices] == [
        PeripheralKind.CAMERA,
        PeripheralKind.MICROPHONE,
        PeripheralKind.SPEAKER,
    ]


def test_real_backend_failures_return_empty_inventory():
    backend = RealPeripheralBackend(
        platform_name="Linux",
        command_runner=StubCommands({}),
    )

    assert backend.scan() == []


def test_runtime_can_start_with_real_discovery_backend(tmp_path):
    backend = RealPeripheralBackend(
        platform_name="Darwin",
        command_runner=StubCommands({
            ("system_profiler", "-json", "SPCameraDataType", "SPAudioDataType"): json.dumps({
                "SPCameraDataType": [{"_name": "Camera"}],
                "SPAudioDataType": [],
            })
        }),
    )
    runtime = MnemeRuntime(
        db_path=tmp_path / "memory.sqlite3",
        migrations_dir=MIGRATIONS,
        clock=RuntimeClock(1_000),
        discovery_service=PeripheralDiscoveryService(backend=backend),
    )
    try:
        snapshot = runtime.start()

        assert snapshot.available(PeripheralKind.CAMERA)[0].label == "Camera"
        assert runtime.snapshot()["devices"]["available_counts"]["camera"] == 1
    finally:
        runtime.close()


def test_discovery_service_keeps_fake_backend_compatible():
    service = PeripheralDiscoveryService(
        backend=RealPeripheralBackend(
            platform_name="UnknownOS",
            command_runner=StubCommands({}),
        ),
        clock=RuntimeClock(1_000),
    )

    snapshot = service.scan_now(publish=False)

    assert snapshot.to_dict()["available_counts"] == {"camera": 0, "microphone": 0, "speaker": 0}
