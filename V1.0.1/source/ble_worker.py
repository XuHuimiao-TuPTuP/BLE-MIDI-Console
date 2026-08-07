"""Async Bleak backend running in a dedicated thread."""
from __future__ import annotations

import asyncio
import threading
from typing import Callable

from bleak import BleakClient, BleakScanner

MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHARACTERISTIC_UUID = "7772e5db-3868-4112-a1a9-f2669d106bf3"


class BleWorker:
    def __init__(self, emit: Callable[[str, object], None]) -> None:
        self.emit = emit
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, name="BLE-Worker", daemon=True)
        self.client: BleakClient | None = None
        self.midi_char: str | None = None
        self.thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coroutine) -> None:
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        future.add_done_callback(self._done)

    def _done(self, future) -> None:
        try:
            future.result()
        except Exception as exc:  # surfaced safely on UI thread
            self.emit("error", f"{type(exc).__name__}: {exc}")

    def scan(self, seconds: float = 7.0) -> None:
        self.submit(self._scan(seconds))

    async def _scan(self, seconds: float) -> None:
        self.emit("scan_state", True)
        devices: dict[str, dict] = {}

        def detected(device, adv) -> None:
            address = device.address
            service_uuids = list(adv.service_uuids or [])
            manufacturer = {int(k): bytes(v).hex(" ").upper() for k, v in (adv.manufacturer_data or {}).items()}
            service_data = {str(k): bytes(v).hex(" ").upper() for k, v in (adv.service_data or {}).items()}
            devices[address] = {
                "name": device.name or adv.local_name or "(未命名)", "address": address,
                "rssi": adv.rssi, "service_uuids": service_uuids,
                "manufacturer_data": manufacturer, "service_data": service_data,
                "tx_power": adv.tx_power, "connectable": getattr(adv, "connectable", None),
                "is_midi": MIDI_SERVICE_UUID in [u.lower() for u in service_uuids],
            }
            self.emit("device", devices[address])

        scanner = BleakScanner(detection_callback=detected)
        try:
            await scanner.start()
            await asyncio.sleep(seconds)
        finally:
            await scanner.stop()
            self.emit("scan_state", False)

    def connect(self, address: str) -> None:
        self.submit(self._connect(address))

    async def _connect(self, address: str) -> None:
        if self.client and self.client.is_connected:
            await self._disconnect()
        self.client = BleakClient(address, disconnected_callback=lambda _: self.emit("disconnected", address))
        await self.client.connect()
        self.midi_char = None
        detail = []
        for service in self.client.services:
            chars = []
            for char in service.characteristics:
                item = {"uuid": char.uuid, "handle": char.handle, "properties": list(char.properties), "descriptors": [d.uuid for d in char.descriptors]}
                chars.append(item)
                if char.uuid.lower() == MIDI_CHARACTERISTIC_UUID:
                    self.midi_char = char.uuid
            detail.append({"uuid": service.uuid, "description": service.description, "characteristics": chars})
        if self.midi_char:
            await self.client.start_notify(self.midi_char, self._notification)
        self.emit("connected", {"address": address, "services": detail, "midi_char": self.midi_char})

    def _notification(self, _sender, data: bytearray) -> None:
        self.emit("rx", bytes(data))

    def disconnect(self) -> None:
        self.submit(self._disconnect())

    async def _disconnect(self) -> None:
        if self.client:
            if self.client.is_connected:
                await self.client.disconnect()
            self.client = None
            self.midi_char = None

    def send(self, packet: bytes) -> None:
        self.submit(self._send(packet))

    async def _send(self, packet: bytes) -> None:
        if not self.client or not self.client.is_connected or not self.midi_char:
            raise RuntimeError("尚未连接到支持标准 BLE MIDI 特征的设备")
        char = self.client.services.get_characteristic(self.midi_char)
        response = "write-without-response" not in char.properties
        await self.client.write_gatt_char(self.midi_char, packet, response=response)
        self.emit("tx", packet)

    def close(self) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop).result(timeout=3)
        except Exception:
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
