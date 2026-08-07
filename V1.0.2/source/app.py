"""BLE MIDI Monitor V1.0.0 - Windows desktop application."""
from __future__ import annotations

import json
import queue
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ble_worker import BleWorker
from midi_parser import MidiStreamParser, decode_ble_midi_packet, encode_ble_midi_packet

APP_NAME = "BLE MIDI 调试器"
VERSION = "V1.0.2"

BG = "#eef2f7"
PANEL = "#f8fafc"
INK = "#0f172a"
MUTED = "#64748b"
ACCENT = "#2563eb"
GREEN = "#86efac"
ORANGE = "#67e8f9"
SYSEX = "#f0abfc"
RED = "#fca5a5"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME}  {VERSION}")
        self.geometry("1680x900")
        self.minsize(1180, 700)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker = BleWorker(lambda kind, data: self.events.put((kind, data)))
        self.devices: dict[str, dict] = {}
        self.connected = False
        self.rx_parser = MidiStreamParser()
        self.tx_parser = MidiStreamParser()
        self._style()
        self._build()
        self.after(40, self._poll)

    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("vista")
        style.configure(".", background=BG, foreground=INK, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 18))
        style.configure("TButton", padding=(10, 5))
        style.configure("Accent.TButton", padding=(12, 6))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground=INK, rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background="#e6edf3", foreground=INK, relief="flat", font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#cfe6f7")], foreground=[("selected", INK)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 7))
        style.configure("TEntry", fieldbackground="#ffffff", foreground=INK, insertcolor=INK)
        style.configure("PanelTitle.TLabel", font=("Segoe UI Semibold", 12), background=PANEL, foreground=INK)
        style.configure("Hint.TLabel", font=("Segoe UI", 9), background=PANEL, foreground=MUTED)
        style.configure("TLabelframe", background=PANEL)
        style.configure("TLabelframe.Label", background=PANEL, foreground=INK, font=("Segoe UI Semibold", 10))

    def _build(self) -> None:
        header = ttk.Frame(self, padding=(18, 12))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=f"  {VERSION}  ·  BLE GATT / MIDI 监测", style="Muted.TLabel").pack(side="left")
        self.status = ttk.Label(header, text="●  未连接", foreground=MUTED)
        self.status.pack(side="right")

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        left = ttk.Frame(main, style="Panel.TFrame", padding=10)
        right = ttk.Frame(main, style="Panel.TFrame", padding=10)
        main.add(left, weight=4)
        main.add(right, weight=6)
        self._build_devices(left)
        self._build_logs(right)

    def _build_devices(self, parent) -> None:
        toolbar = ttk.Frame(parent, style="Panel.TFrame")
        toolbar.pack(fill="x", pady=(0, 8))
        self.scan_btn = ttk.Button(toolbar, text="扫描 BLE（7 秒）", style="Accent.TButton", command=self.scan)
        self.scan_btn.pack(side="left")
        self.connect_btn = ttk.Button(toolbar, text="连接", command=self.connect_selected)
        self.connect_btn.pack(side="left", padx=6)
        ttk.Button(toolbar, text="断开", command=self.worker.disconnect).pack(side="left")
        ttk.Button(toolbar, text="清空设备", command=self.clear_devices).pack(side="right")

        cols = ("midi", "name", "address", "rssi")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=13)
        labels = {"midi": "类型", "name": "设备名称", "address": "地址", "rssi": "RSSI"}
        widths = {"midi": 70, "name": 180, "address": 145, "rssi": 65}
        for col in cols:
            self.tree.heading(col, text=labels[col], command=lambda c=col: self._sort(c))
            self.tree.column(col, width=widths[col], anchor="w" if col in ("name", "address") else "center")
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self.show_device)
        self.tree.bind("<Double-1>", lambda _e: self.connect_selected())

        ttk.Label(parent, text="广播 / GATT 详细信息", style="PanelTitle.TLabel").pack(anchor="w", pady=(12, 5))
        self.detail = self._text(parent, height=18)
        self.detail.pack(fill="both", expand=True)
        self.detail.tag_configure("service", foreground=ACCENT)
        self.detail.tag_configure("char", foreground=GREEN)

    def _build_logs(self, parent) -> None:
        self.tabs = ttk.Notebook(parent)
        self.tabs.pack(fill="both", expand=True)
        self.logs = {}

        monitor = ttk.Frame(self.tabs, padding=6)
        split = ttk.Panedwindow(monitor, orient="vertical")
        split.pack(fill="both", expand=True)
        for key, label, color in (("rx", "RX  接收数据", GREEN), ("tx", "TX  发送数据", ORANGE)):
            pane, text = self._create_log_area(split, label, key, color)
            self.logs[key] = text
            split.add(pane, weight=1)
        self.tabs.add(monitor, text="RX / TX 实时监测")

        for key, label in (("all", "全部解析"), ("raw", "原始 BLE")):
            frame = ttk.Frame(self.tabs, padding=6)
            text = self._text(frame)
            text.pack(fill="both", expand=True)
            ttk.Button(frame, text=f"清空 {label}", command=lambda k=key: self.clear_log(k)).pack(anchor="e", pady=(6, 0))
            self.tabs.add(frame, text=label)
            self.logs[key] = text
        send = ttk.Frame(parent, style="Panel.TFrame")
        send.pack(fill="x", pady=(8, 0))
        self.send_value = tk.StringVar(value="90 3C 7F")
        entry = ttk.Entry(send, textvariable=self.send_value, font=("Cascadia Mono", 10))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry.bind("<Return>", lambda _e: self.send_midi())
        ttk.Button(send, text="发送", command=self.send_midi).pack(side="left", padx=(0, 6))
        ttk.Button(send, text="清空 RX/TX", command=lambda: (self.clear_log("rx"), self.clear_log("tx"))).pack(side="left")
        ttk.Label(parent, text="十六进制字节；SysEx 示例：F0 7E 7F 09 01 F7", style="Hint.TLabel").pack(anchor="w", pady=(5, 0))
        for text in self.logs.values():
            text.tag_configure("rx", foreground=GREEN)
            text.tag_configure("tx", foreground=ORANGE)
            text.tag_configure("sysex", foreground=SYSEX, background="#312e4a")
            text.tag_configure("raw", foreground="#93c5fd")
            text.tag_configure("error", foreground=RED)
            text.tag_configure("meta", foreground=MUTED)

    def _create_log_area(self, parent, title: str, key: str, color: str):
        frame = ttk.LabelFrame(parent, text=title, padding=(6, 4, 6, 6))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Button(frame, text=f"清空 {key.upper()}", command=lambda: self.clear_log(key)).grid(row=0, column=0, sticky="e", pady=(0, 4))
        log = self._text(frame)
        log.grid(row=1, column=0, sticky="nsew")
        sy = ttk.Scrollbar(frame, orient="vertical", command=log.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=log.xview)
        sy.grid(row=1, column=1, sticky="ns")
        sx.grid(row=2, column=0, sticky="ew")
        log.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        log.tag_configure(key, foreground=color)
        return frame, log

    def _text(self, parent, height=None):
        return tk.Text(parent, height=height, bg="#111827", fg="#cbd5e1", insertbackground="white",
                       selectbackground="#334155", relief="flat", padx=8, pady=8,
                       wrap="none", font=("Cascadia Mono", 9), state="disabled")

    def _stamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _append(self, key: str, line: str, tag: str = "meta") -> None:
        text = self.logs[key]
        text.configure(state="normal")
        text.insert("end", line + "\n", tag)
        text.see("end")
        text.configure(state="disabled")

    def scan(self) -> None:
        self._append("all", f"[{self._stamp()}] 扫描开始…", "meta")
        self.worker.scan()

    def clear_devices(self) -> None:
        self.devices.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._set_text(self.detail, "")

    def _sort(self, col: str) -> None:
        reverse = col == "rssi"
        rows = [(self.tree.set(row, col), row) for row in self.tree.get_children("")]
        if col == "rssi":
            rows.sort(key=lambda pair: int(pair[0]), reverse=reverse)
        else:
            rows.sort(key=lambda pair: pair[0].lower(), reverse=False)
        for index, (_, row) in enumerate(rows):
            self.tree.move(row, "", index)

    def connect_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(APP_NAME, "请先选择一个 BLE 设备。")
            return
        address = selection[0]
        self.status.configure(text="●  正在连接…", foreground=ORANGE)
        self.worker.connect(address)

    def show_device(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.devices.get(selection[0], {})
        self._set_text(self.detail, json.dumps(item, indent=2, ensure_ascii=False, default=str))

    def _set_text(self, widget, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", value)
        widget.configure(state="disabled")

    def _show_gatt(self, info: dict) -> None:
        text = self.detail
        text.configure(state="normal")
        text.delete("1.0", "end")
        for service in info["services"]:
            text.insert("end", f"SERVICE  {service['uuid']}  {service['description']}\n", "service")
            for char in service["characteristics"]:
                props = ", ".join(char["properties"])
                text.insert("end", f"  CHARACTERISTIC  {char['uuid']}\n", "char")
                text.insert("end", f"    handle={char['handle']}  properties=[{props}]\n")
                for desc in char["descriptors"]:
                    text.insert("end", f"    descriptor={desc}\n")
            text.insert("end", "\n")
        text.configure(state="disabled")

    def send_midi(self) -> None:
        try:
            cleaned = self.send_value.get().replace("0x", "").replace(",", " ")
            midi = bytes.fromhex(cleaned)
            if not midi:
                raise ValueError("数据为空")
            packet = encode_ble_midi_packet(midi, int(time.monotonic() * 1000))
            self.worker.send(packet)
        except ValueError as exc:
            messagebox.showerror(APP_NAME, f"HEX 输入无效：{exc}")

    def _handle_packet(self, direction: str, packet: bytes) -> None:
        timestamp, midi = decode_ble_midi_packet(packet)
        stamp = self._stamp()
        raw_line = f"[{stamp}] {direction.upper():2}  {packet.hex(' ').upper()}  BLE-ts={timestamp if timestamp is not None else '-'}"
        self._append("raw", raw_line, "raw")
        parser = self.rx_parser if direction == "rx" else self.tx_parser
        messages = parser.feed(midi)
        if not messages:
            self._append(direction, f"[{stamp}] {packet.hex(' ').upper()}  · 等待后续分段", "meta")
        for msg in messages:
            line = f"[{stamp}] {direction.upper():2}  {msg.data.hex(' ').upper():<36}  · {msg.annotation}"
            tag = "sysex" if msg.sysex else direction
            self._append(direction, line, tag)
            self._append("all", line, tag)

    def _poll(self) -> None:
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "device":
                    self.devices[data["address"]] = data
                    values = ("MIDI" if data["is_midi"] else "BLE", data["name"], data["address"], data["rssi"])
                    if self.tree.exists(data["address"]):
                        self.tree.item(data["address"], values=values)
                    else:
                        self.tree.insert("", "end", iid=data["address"], values=values)
                    self._sort("rssi")
                elif kind == "scan_state":
                    self.scan_btn.configure(state="disabled" if data else "normal")
                    if not data:
                        self._append("all", f"[{self._stamp()}] 扫描结束，共发现 {len(self.devices)} 台设备", "meta")
                elif kind == "connected":
                    self.connected = True
                    midi = "BLE MIDI 就绪" if data["midi_char"] else "未发现标准 MIDI 特征"
                    self.status.configure(text=f"●  已连接 · {midi}", foreground=GREEN if data["midi_char"] else ORANGE)
                    self._show_gatt(data)
                    self._append("all", f"[{self._stamp()}] 已连接 {data['address']} · {midi}", "meta")
                elif kind == "disconnected":
                    self.connected = False
                    self.status.configure(text="●  未连接", foreground=MUTED)
                    self._append("all", f"[{self._stamp()}] 连接已断开", "error")
                elif kind in ("rx", "tx"):
                    self._handle_packet(kind, data)
                elif kind == "error":
                    self.status.configure(text="●  操作失败", foreground=RED)
                    self._append("all", f"[{self._stamp()}] ERROR  {data}", "error")
        except queue.Empty:
            pass
        self.after(40, self._poll)

    def clear_log(self, key: str) -> None:
        text = self.logs[key]
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.configure(state="disabled")

    def on_close(self) -> None:
        self.worker.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
