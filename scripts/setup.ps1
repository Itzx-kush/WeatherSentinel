$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python launcher 'py' was not found." }
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Write-Host "WeatherSentinel environment is ready."
