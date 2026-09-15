$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run .\scripts\setup.ps1 first." }
& $Python -m compileall -q backend tests
if ($LASTEXITCODE -ne 0) { throw "Compile check failed." }
$env:PYTHONPATH = "backend"
& $Python -m unittest discover -s tests -t . -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Unit/integration tests failed." }
& $Python -m ruff check backend tests
if ($LASTEXITCODE -ne 0) { throw "Ruff failed." }
& $Python -m pytest
if ($LASTEXITCODE -ne 0) { throw "Pytest failed." }
Write-Host "All configured checks passed."
