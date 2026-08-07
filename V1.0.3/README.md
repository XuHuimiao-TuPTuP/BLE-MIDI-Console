# BLE MIDI 调试器 V1.0.3

## 本版本修改记录

- 2026-08-07：发布降低杀毒软件误报概率的 Windows 构建。
- PyInstaller 从 `--onefile` 改为 `--onedir`，不再使用运行时自解压模式。
- 明确禁用 UPX 压缩，减少启发式杀毒引擎对压缩可执行文件的误判。
- 为 EXE 加入 ProductName、FileDescription、FileVersion、ProductVersion 等 Windows 版本资源。
- GitHub Release 改为发布完整 ZIP，不再建议直接分发单个 EXE。
- 构建时生成 SHA-256 校验文件，方便确认下载文件未被修改。
- 软件功能和 V1.0.2 保持一致。

## 运行方法

1. 下载 `release/BLE-MIDI-Debugger-V1.0.3-Windows-x64.zip`。
2. 完整解压 ZIP。
3. 运行 `BLE-MIDI-Debugger-V1.0.3/BLE-MIDI-Debugger-V1.0.3.exe`。

不能将 EXE 单独移出目录，因为它依赖同目录中的 `_internal` 文件夹。

## 构建

```powershell
cd V1.0.3\source
python -m pip install -r requirements.txt
.\build.ps1
```

## 关于杀毒软件误报

V1.0.0 至 V1.0.2 使用 PyInstaller 单文件模式。单文件程序启动时需要将内嵌组件释放到临时目录，这种行为容易被部分启发式检测引擎误判。V1.0.3 取消了这一模式。

非自解压构建可以降低误报概率，但无法保证所有第三方杀毒引擎均不报警。获得最高信誉度仍需要使用受信任机构签发的 Windows 代码签名证书对 EXE 和安装包进行签名。
