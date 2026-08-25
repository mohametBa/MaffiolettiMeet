# Recupere un ffmpeg LGPL pour Windows (sidecar de Atex Italia Meeting).
#
# Pendant du script macOS scripts/build-ffmpeg-lgpl.sh : sur Windows on ne
# recompile pas ffmpeg, on prend la build LGPL publiee par BtbN/FFmpeg-Builds.
# Surtout PAS une build "gpl" ou "nonfree" : l'app n'en a pas besoin (encodage
# AAC natif + decodage) et elles ne seraient pas redistribuables.
#
# Usage : powershell -ExecutionPolicy Bypass -File scripts\fetch-ffmpeg-windows.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$vendorDir = Join-Path $scriptDir "..\src-tauri\vendor\ffmpeg"
$url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-lgpl.zip"

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
$zip = Join-Path $env:TEMP "ffmpeg-win64-lgpl.zip"
$tmp = Join-Path $env:TEMP "ffmpeg-win64-lgpl"

Write-Host "Telechargement de la build LGPL..."
Invoke-WebRequest -Uri $url -OutFile $zip

if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
Expand-Archive -Path $zip -DestinationPath $tmp

$exe = Get-ChildItem -Path $tmp -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
if (-not $exe) { throw "ffmpeg.exe introuvable dans l'archive" }

$dest = Join-Path $vendorDir "ffmpeg-x86_64-pc-windows-msvc.exe"
Copy-Item $exe.FullName $dest -Force
Remove-Item -Recurse -Force $tmp
Remove-Item -Force $zip

Write-Host "Binaire : $dest"
& $dest -version | Select-Object -First 2
