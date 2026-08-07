"""MIDI stream parsing and human-readable annotations."""
from __future__ import annotations

from dataclasses import dataclass


CHANNEL_LENGTHS = {
    0x80: 3, 0x90: 3, 0xA0: 3, 0xB0: 3,
    0xC0: 2, 0xD0: 2, 0xE0: 3,
}
SYSTEM_LENGTHS = {
    0xF1: 2, 0xF2: 3, 0xF3: 2, 0xF6: 1,
    0xF8: 1, 0xFA: 1, 0xFB: 1, 0xFC: 1, 0xFE: 1, 0xFF: 1,
}
CC_NAMES = {
    0: "Bank Select MSB", 1: "Modulation", 2: "Breath", 4: "Foot Controller",
    5: "Portamento Time", 6: "Data Entry MSB", 7: "Channel Volume",
    10: "Pan", 11: "Expression", 32: "Bank Select LSB", 38: "Data Entry LSB",
    64: "Sustain Pedal", 65: "Portamento", 66: "Sostenuto", 67: "Soft Pedal",
    91: "Reverb Send", 93: "Chorus Send", 98: "NRPN LSB", 99: "NRPN MSB",
    100: "RPN LSB", 101: "RPN MSB", 120: "All Sound Off", 121: "Reset Controllers",
    123: "All Notes Off",
}
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(slots=True)
class MidiMessage:
    data: bytes
    annotation: str
    sysex: bool = False


def note_name(value: int) -> str:
    return f"{NOTE_NAMES[value % 12]}{value // 12 - 1}"


def describe_message(data: bytes) -> str:
    if not data:
        return "空消息"
    status = data[0]
    if status == 0xF0:
        return describe_sysex(data)
    if status < 0xF0:
        channel = (status & 0x0F) + 1
        kind = status & 0xF0
        if kind == 0x80 and len(data) >= 3:
            return f"Note Off  CH{channel}  {note_name(data[1])}  velocity={data[2]}"
        if kind == 0x90 and len(data) >= 3:
            label = "Note Off" if data[2] == 0 else "Note On"
            return f"{label}  CH{channel}  {note_name(data[1])}  velocity={data[2]}"
        if kind == 0xA0 and len(data) >= 3:
            return f"Poly Pressure  CH{channel}  {note_name(data[1])}  pressure={data[2]}"
        if kind == 0xB0 and len(data) >= 3:
            return f"Control Change  CH{channel}  CC{data[1]} {CC_NAMES.get(data[1], '')}  value={data[2]}"
        if kind == 0xC0 and len(data) >= 2:
            return f"Program Change  CH{channel}  program={data[1]}"
        if kind == 0xD0 and len(data) >= 2:
            return f"Channel Pressure  CH{channel}  pressure={data[1]}"
        if kind == 0xE0 and len(data) >= 3:
            bend = (data[1] | (data[2] << 7)) - 8192
            return f"Pitch Bend  CH{channel}  value={bend}"
    system = {
        0xF1: "MTC Quarter Frame", 0xF2: "Song Position", 0xF3: "Song Select",
        0xF6: "Tune Request", 0xF8: "Timing Clock", 0xFA: "Start",
        0xFB: "Continue", 0xFC: "Stop", 0xFE: "Active Sensing", 0xFF: "System Reset",
    }
    return system.get(status, f"System/未识别状态 0x{status:02X}")


def describe_sysex(data: bytes) -> str:
    body = data[1:-1] if data.endswith(b"\xF7") else data[1:]
    suffix = "" if data.endswith(b"\xF7") else "（分段/未结束）"
    if body[:4] == bytes((0x7E, 0x7F, 0x09, 0x01)):
        return "SysEx · General MIDI System On" + suffix
    if body[:4] == bytes((0x7E, 0x7F, 0x09, 0x02)):
        return "SysEx · General MIDI 2 System On" + suffix
    if body[:4] == bytes((0x7E, 0x7F, 0x09, 0x03)):
        return "SysEx · General MIDI System Off" + suffix
    if body[:8] == bytes((0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00)):
        return "SysEx · Roland GS Reset" + suffix
    if body[:7] == bytes((0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00)):
        return "SysEx · Yamaha XG System On" + suffix
    if len(body) >= 3 and body[0] in (0x7E, 0x7F):
        rt = "Real-Time" if body[0] == 0x7F else "Non-Real-Time"
        return f"SysEx · Universal {rt}, device=0x{body[1]:02X}, sub-ID=0x{body[2]:02X}" + suffix
    makers = {0x41: "Roland", 0x42: "Korg", 0x43: "Yamaha", 0x44: "Casio", 0x47: "Akai"}
    maker = makers.get(body[0], f"Manufacturer 0x{body[0]:02X}") if body else "未知厂商"
    return f"SysEx · {maker}, payload={len(body)} bytes" + suffix


class MidiStreamParser:
    """Stateful MIDI 1.0 byte-stream parser with running-status and SysEx support."""

    def __init__(self) -> None:
        self.running_status: int | None = None
        self.pending = bytearray()
        self.sysex = bytearray()

    def feed(self, payload: bytes) -> list[MidiMessage]:
        result: list[MidiMessage] = []
        for value in payload:
            if self.sysex:
                self.sysex.append(value)
                if value == 0xF7:
                    raw = bytes(self.sysex)
                    result.append(MidiMessage(raw, describe_sysex(raw), True))
                    self.sysex.clear()
                elif value >= 0xF8:
                    self.sysex.pop()
                    result.append(MidiMessage(bytes((value,)), describe_message(bytes((value,)))))
                continue
            if value == 0xF0:
                self.pending.clear()
                self.running_status = None
                self.sysex.append(value)
                continue
            if value >= 0xF8:
                raw = bytes((value,))
                result.append(MidiMessage(raw, describe_message(raw)))
                continue
            if value & 0x80:
                self.pending = bytearray((value,))
                self.running_status = value if value < 0xF0 else None
                if SYSTEM_LENGTHS.get(value) == 1:
                    raw = bytes(self.pending)
                    result.append(MidiMessage(raw, describe_message(raw)))
                    self.pending.clear()
                continue
            if not self.pending:
                if self.running_status is None:
                    result.append(MidiMessage(bytes((value,)), "孤立数据字节（无状态）"))
                    continue
                self.pending.append(self.running_status)
            self.pending.append(value)
            status = self.pending[0]
            needed = CHANNEL_LENGTHS.get(status & 0xF0) if status < 0xF0 else SYSTEM_LENGTHS.get(status)
            if needed and len(self.pending) >= needed:
                raw = bytes(self.pending[:needed])
                result.append(MidiMessage(raw, describe_message(raw)))
                self.pending.clear()
        return result

    def flush_sysex_fragment(self) -> MidiMessage | None:
        if not self.sysex:
            return None
        raw = bytes(self.sysex)
        self.sysex.clear()
        return MidiMessage(raw, describe_sysex(raw), True)


def decode_ble_midi_packet(packet: bytes) -> tuple[int | None, bytes]:
    """Remove BLE-MIDI timestamp bytes and return (13-bit timestamp, MIDI bytes)."""
    if not packet or not packet[0] & 0x80:
        return None, packet
    high = packet[0] & 0x3F
    output = bytearray()
    timestamp: int | None = None
    index = 1
    expecting_timestamp = True
    while index < len(packet):
        value = packet[index]
        if expecting_timestamp and value & 0x80:
            timestamp = (high << 7) | (value & 0x7F)
            index += 1
            expecting_timestamp = False
            continue
        output.append(value)
        # A new timestamp-low byte may occur before each new MIDI status.
        expecting_timestamp = value >= 0x80 and value < 0xF8
        index += 1
    return timestamp, bytes(output)


def encode_ble_midi_packet(midi: bytes, timestamp_ms: int) -> bytes:
    timestamp = timestamp_ms & 0x1FFF
    return bytes((0x80 | (timestamp >> 7), 0x80 | (timestamp & 0x7F))) + midi
