# BLE MIDI Debugger

一款面向 Windows 11 的 BLE MIDI 外设扫描、连接、收发与协议分析工具。它可以像串口调试助手一样直接观察 BLE MIDI 的原始数据，并将常见 MIDI 消息和 SysEx 命令解析为便于阅读的注释。

> 当前版本：**V1.0.2** · 支持 Windows 11 · 提供免安装 EXE

## 功能亮点

- 扫描附近可连接的 BLE 设备，并按照 RSSI 信号强度排序。
- 显示设备名称、地址、RSSI、Service UUID、Manufacturer Data、Service Data 和 TX Power。
- 连接后枚举 GATT Service、Characteristic、Descriptor、Handle 及读写属性。
- 自动识别并订阅标准 BLE MIDI Service 和 Characteristic。
- RX 与 TX 日志上下分栏，可同时查看发送和接收的数据。
- 提供“全部解析”和“原始 BLE”独立日志页面。
- 日志时间戳精确到毫秒，同时显示 BLE MIDI 13-bit 时间戳。
- 显示完整十六进制数据，并为通用 MIDI 消息追加中文含义。
- 支持跨通知包拼接 SysEx，SysEx 使用独立颜色高亮。
- 支持输入十六进制 MIDI 数据并通过 BLE 发送。
- RX、TX、全部解析和原始数据日志均可独立清空。

## 支持解析的消息

### Channel Voice

- Note On / Note Off
- Polyphonic Key Pressure
- Control Change，以及常见 CC 控制器名称
- Program Change
- Channel Pressure
- Pitch Bend
- Running Status

### System Message

- MTC Quarter Frame
- Song Position Pointer
- Song Select
- Tune Request
- Timing Clock、Start、Continue、Stop
- Active Sensing、System Reset

### SysEx

- General MIDI System On / Off
- General MIDI 2 System On
- Roland GS Reset
- Yamaha XG System On
- Universal Identity Request / Reply
- Universal Master Volume / Master Balance
- MIDI Machine Control
- 常见厂商 ID 识别
- 未知厂商私有 SysEx 的完整原始数据显示

## 界面布局

界面针对 1920 × 1080 屏幕设计：

- 左侧用于 BLE 扫描、设备选择、广播信息和 GATT 详情。
- 右侧默认显示 RX/TX 实时监测，上方为 RX，下方为 TX。
- 日志采用深色背景，RX 为绿色、TX 为青色、SysEx 为紫色高亮。
- 底部提供 HEX 数据输入、发送和日志清理操作。

## 快速开始

### 直接运行

1. 下载 [BLE-MIDI-Debugger-V1.0.2.exe](V1.0.2/release/BLE-MIDI-Debugger-V1.0.2.exe)。
2. 打开 Windows 蓝牙，并确保 BLE MIDI 外设处于广播状态。
3. 运行程序，点击“扫描 BLE”。
4. 选择目标设备，然后点击“连接”或双击设备。
5. 连接成功后，设备发送的数据会自动显示在 RX 日志中。

程序为单文件 EXE，不要求目标电脑预先安装 Python。

### 发送 MIDI

在底部输入空格分隔的十六进制字节，然后点击“发送”或按 Enter：

```text
90 3C 7F
```

以上示例表示：MIDI Channel 1，C4 Note On，力度 127。

发送 GM System On SysEx：

```text
F0 7E 7F 09 01 F7
```

## 标准 BLE MIDI UUID

| 类型 | UUID |
| --- | --- |
| MIDI Service | `03B80E5A-EDE8-4B33-A751-6CE34EC4C700` |
| MIDI I/O Characteristic | `7772E5DB-3868-4112-A1A9-F2669D106BF3` |

程序连接设备后会自动查找上述 Characteristic，并在支持的设备上启用通知和数据发送。

## 源码运行

环境要求：

- Windows 11
- Python 3.14
- 已正确安装并启用蓝牙驱动

```powershell
cd V1.0.2\source
python -m pip install -r requirements.txt
python app.py
```

主要依赖：

- [Bleak](https://github.com/hbldh/bleak)：BLE 扫描和 GATT 通信
- Tkinter：Windows 桌面界面
- PyInstaller：生成独立 EXE

## 构建 EXE

```powershell
cd V1.0.2\source
.\build.ps1
```

构建完成后，EXE 位于：

```text
V1.0.2\release\BLE-MIDI-Debugger-V1.0.2.exe
```

## 项目结构

```text
BLE_MIDI/
├─ README.md
├─ V1.0.0/
├─ V1.0.1/
└─ V1.0.2/
   ├─ README.md
   ├─ source/
   │  ├─ app.py
   │  ├─ ble_worker.py
   │  ├─ midi_parser.py
   │  ├─ requirements.txt
   │  └─ build.ps1
   └─ release/
      ├─ BLE-MIDI-Debugger-V1.0.2.exe
      └─ README.md
```

每个版本使用独立目录保存源码、Release 和修改记录，便于回溯及对比。

## 版本记录

| 版本 | 主要内容 |
| --- | --- |
| [V1.0.2](V1.0.2/README.md) | 统一 USB_MIDI 风格，优化 RX/TX 上下分栏、滚动条和发送区 |
| [V1.0.1](V1.0.1/README.md) | 浅色界面，增强通用 MIDI 和 Universal SysEx 注释 |
| [V1.0.0](V1.0.0/README.md) | 首个版本，实现 BLE 扫描、GATT 枚举、MIDI 收发和日志解析 |

## 使用限制

- 本工具只能显示 Windows 蓝牙栈实际交付给应用程序的 GATT 数据，无法旁路捕获蓝牙控制器层或系统内部未上报的数据。
- BLE MIDI 设备必须处于广播状态，并且没有被其他主机独占连接。
- 厂商私有 SysEx 的含义取决于对应厂商协议。无法识别的消息仍会完整显示原始字节。
- 当前版本仅面向 Windows 11 进行开发和构建。

## 问题反馈

提交 Issue 时建议附上以下信息：

- Windows 版本
- BLE MIDI 设备品牌和型号
- 操作步骤与错误提示
- “原始 BLE”日志内容
- 问题发生时的截图

请在分享日志前检查其中是否包含设备地址或其他不希望公开的信息。
