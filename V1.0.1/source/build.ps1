$ErrorActionPreference = "Stop"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VersionDir = Split-Path -Parent $SourceDir
$ReleaseDir = Join-Path $VersionDir "release"
$BuildDir = Join-Path $VersionDir "build"

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name "BLE-MIDI-Debugger-V1.0.1" `
  --distpath $ReleaseDir --workpath $BuildDir `
  --specpath $BuildDir `
  (Join-Path $SourceDir "app.py")

Write-Host "Build complete: $ReleaseDir"
