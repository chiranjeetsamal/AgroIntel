$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
& "$projectRoot/.venv/Scripts/python.exe" -m agrointel.web
exit $LASTEXITCODE
