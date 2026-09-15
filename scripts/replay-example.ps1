param([double]$Speed = 60)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run .\scripts\setup.ps1 first." }
$env:PYTHONPATH = "backend"
& $Python -m app.cli replay --input data\examples\aws_synthetic_normal.csv --dataset-id imd-demo-synthetic-v1 --source-type synthetic --speed $Speed
if ($LASTEXITCODE -ne 0) { throw "Replay failed." }
