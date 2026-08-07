$ErrorActionPreference = "Stop"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VersionDir = Split-Path -Parent $SourceDir
$ReleaseDir = Join-Path $VersionDir "release"
$BuildDir = Join-Path $VersionDir "build"
$ProductName = "BLE-MIDI-Debugger-V1.0.3"
$AppDir = Join-Path $ReleaseDir $ProductName
$Archive = Join-Path $ReleaseDir "$ProductName-Windows-x64.zip"
$VersionFile = Join-Path $SourceDir "file_version_info.txt"

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

# onedir avoids the self-extracting bootloader used by --onefile. That bootloader is
# frequently flagged by heuristic antivirus engines even when the program is clean.
python -m PyInstaller --noconfirm --clean --onedir --windowed --noupx `
  --name $ProductName `
  --version-file $VersionFile `
  --distpath $ReleaseDir --workpath $BuildDir `
  --specpath $BuildDir `
  (Join-Path $SourceDir "app.py")

if (Test-Path $Archive) {
  Remove-Item -LiteralPath $Archive -Force
}
Compress-Archive -Path $AppDir -DestinationPath $Archive -CompressionLevel Optimal

$Hash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash
Set-Content -LiteralPath (Join-Path $ReleaseDir "SHA256SUMS.txt") `
  -Value "$Hash  $ProductName-Windows-x64.zip" -Encoding ascii

Write-Host "Build complete: $AppDir"
Write-Host "GitHub Release archive: $Archive"
Write-Host "SHA256: $Hash"
