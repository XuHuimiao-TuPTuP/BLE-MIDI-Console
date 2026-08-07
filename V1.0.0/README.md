# BLE MIDI 调试器 V1.0.0

首个可用版本，面向 Windows 11 的 BLE MIDI 外设调试。

## 功能

- 扫描附近 BLE 设备，实时显示名称、地址、RSSI，并按信号强度排序。
- 显示广播 Service UUID、Manufacturer Data、Service Data、TX Power 等原始字段。
- 连接后枚举全部 GATT Service、Characteristic、Descriptor、Handle 与属性。
- 自动识别标准 BLE MIDI Service `03B80E5A-EDE8-4B33-A751-6CE34EC4C700` 和 Characteristic `7772E5DB-3868-4112-A1A9-F2669D106BF3`。
- 独立的全部、RX、TX、原始 BLE 日志窗口；每个窗口均可单独清空。
- 毫秒级本机接收/发送时间戳，并显示 BLE MIDI 13-bit 时间戳。
- MIDI Channel Voice、System Common、System Real-Time 与 Running Status 解析。
- 跨通知包累计完整 SysEx，支持 GM On/Off、GM2、Roland GS Reset、Yamaha XG On 及常见厂商注释；SysEx 紫色显示。
- 支持以 HEX 形式发送 MIDI 消息，自动封装 BLE MIDI 时间戳头。

## 使用

1. 打开蓝牙，运行 `release/BLE-MIDI-Debugger-V1.0.0.exe`。
2. 点击“扫描 BLE”，选择设备后双击或点击“连接”。
3. 标准 BLE MIDI 设备连接后会自动订阅通知；数据出现在日志页。
4. 在“发送 HEX MIDI”输入标准 MIDI 字节，例如 `90 3C 7F`，点击发送。

Windows 可能隐藏未广播或未配对的设备。若扫描不到，确认设备正在广播、未被其他主机占用，并在 Windows 设置中允许蓝牙访问。

## 源码运行与构建

```powershell
cd V1.0.0\source
python -m pip install -r requirements.txt
python app.py
.\build.ps1
```

源码位于 `source`，构建产物位于 `release`。后续版本使用独立的 `V1.0.1`、`V1.0.2` 等目录。

## 本版本修改记录

- 2026-08-06：创建 V1.0.0，完成扫描、广播数据、GATT 详情、BLE MIDI 收发、日志分类、协议注释与 SysEx 高亮。

## 已知边界

- 仅能读取外设通过标准 BLE MIDI GATT Characteristic 实际发送到本机的数据；Windows 蓝牙栈内部未交付给应用的数据无法旁路抓取。
- 厂商私有 SysEx 的语义取决于厂商公开协议；未知消息仍会完整显示原始字节与厂商 ID。
