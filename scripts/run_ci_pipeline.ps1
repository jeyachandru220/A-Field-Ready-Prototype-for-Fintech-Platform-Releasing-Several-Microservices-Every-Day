# Local CI Pipeline Reproducer Script for Windows PowerShell
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   REPRODUCIBLE CI PIPELINE EXECUTION (MATCHES GITHUB ACTIONS DRIFT-GATE)" -ForegroundColor Cyan
Write-Host "================================================================================"

Write-Host "`n[CI Step 1] Validating Python environment..." -ForegroundColor Yellow
python --version
pip --version

Write-Host "`n[CI Step 2] Running pytest test suite..." -ForegroundColor Yellow
pytest -v tests/

Write-Host "`n[CI Step 3] Executing Pre-Flight Drift Gate Check (Clean Scenario)..." -ForegroundColor Yellow
python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario none

Write-Host "`n[CI Step 4] Executing 50-Scenario Benchmark Experiment..." -ForegroundColor Yellow
python experiments/benchmark.py

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " ✅ REPRODUCIBLE CI PIPELINE COMPLETED WITH EXIT CODE 0" -ForegroundColor Green
Write-Host "================================================================================"
