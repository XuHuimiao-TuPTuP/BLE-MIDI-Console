# BLE MIDI 调试器 V1.0.1

Windows 11 BLE MIDI 外设扫描、连接、收发和协议监测工具。

## 本版本修改记录

- 2026-08-06：界面改为浅色、简洁、专业风格。
- RX 与 TX 改为默认页上下分栏，可同时观察收发数据，各自独立清空。
- 保留“全部解析”和“原始 BLE”独立日志页。
- 增强通用 MIDI 注释：MTC Quarter Frame、Song Position Pointer、Song Select。
- 增强通用 SysEx 注释：Identity Request/Reply、Master Volume、Master Balance 和 MIDI Machine Control。
- 延续 V1.0.0 的 GM、GM2、GS Reset、XG On、Channel Voice、System Real-Time、Running Status 与跨包 SysEx 解析。

## 使用方法

1. 运行 `release/BLE-MIDI-Debugger-V1.0.1.exe`。
2. 点击“扫描 BLE”，选择设备并连接。
3. 标准 BLE MIDI 设备的数据会自动显示在上方 RX 窗口；本软件发送的数据同步显示在下方 TX 窗口。
4. 输入 MIDI HEX（例如 `90 3C 7F`）并点击“发送”。

## 目录

- `source`：Python 源码和构建脚本。
- `release`：可独立运行的 Windows EXE。
- `build`：PyInstaller 中间文件，重新构建时自动产生。

## 源码运行和构建

```powershell
cd V1.0.1\source
python -m pip install -r requirements.txt
python app.py
.\build.ps1
```

## 技术边界

软件会完整显示应用实际收到的 GATT 数据。Windows 蓝牙栈未交付给应用的数据无法旁路捕获；未知厂商私有 SysEx 会保留完整原始字节并标注厂商 ID。
