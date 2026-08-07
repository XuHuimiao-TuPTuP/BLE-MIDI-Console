# BLE MIDI 调试器 V1.0.2

## 本版本修改记录

- 2026-08-06：参照 USB_MIDI V1.0.1 重新统一 UI 风格。
- 使用 Windows `vista` 原生主题、浅灰页面和白色功能面板。
- 日志区域改为 USB_MIDI 同款深色背景，RX 使用绿色、TX 使用青色、SysEx 使用紫色背景高亮。
- RX/TX 使用带标题边框的上下分栏，并增加纵向和横向滚动条。
- HEX 发送框移动到日志底部，增加回车发送、统一清空 RX/TX 和 SysEx 示例提示。
- 标题栏采用与 USB_MIDI 相同的主标题、版本号和功能副标题层级。
- 保留 BLE 专用的扫描列表、广播信息和完整 GATT 详情功能。

## 使用方法

运行 `release/BLE-MIDI-Debugger-V1.0.2.exe`，扫描并选择 BLE MIDI 设备连接。RX 与 TX 会在右侧上下同步显示；输入 MIDI HEX 后可点击“发送”或按 Enter。

## 构建

```powershell
cd V1.0.2\source
.\build.ps1
```
