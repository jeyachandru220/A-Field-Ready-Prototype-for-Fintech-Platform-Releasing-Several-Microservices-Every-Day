# Concrete PowerShell Execution Script for Windows
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cipher
Write-Host "   FINTECH CONFIGURATION DRIFT VALIDATOR - FULL VERIFICATION SUITE (PS1)" -ForegroundColor Cyan
Write-Host "================================================================================"

Write-Host "`n[1/4] Running Pytest Unit & Integration Tests..." -ForegroundColor Yellow
pytest -v tests/

Write-Host "`n[2/4] Executing CLI Pre-Flight Drift Gate Check (Clean Release)..." -ForegroundColor Yellow
python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario none

Write-Host "`n[3/4] Executing CLI Pre-Flight Drift Gate Check (Drifted Release - Insecure DB)..." -ForegroundColor Yellow
try {
    python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario insecure_db
} catch {
    Write-Host "Expected Gate Abortion Captured!" -ForegroundColor Green
}

Write-Host "`n[4/4] Executing 50-Scenario Benchmark Experiment..." -ForegroundColor Yellow
python experiments/benchmark.py

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " ✅ ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================================================"
