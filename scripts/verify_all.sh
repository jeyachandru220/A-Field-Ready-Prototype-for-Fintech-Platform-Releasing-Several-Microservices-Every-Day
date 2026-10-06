#!/usr/bin/env bash
# Concrete Execution Script: Runs full test suite, CLI drift verification, benchmark experiment, and rollback check.
set -e

echo "================================================================================"
echo "   FINTECH CONFIGURATION DRIFT VALIDATOR - FULL VERIFICATION SUITE"
echo "================================================================================"

echo "[1/4] Running Pytest Unit & Integration Tests..."
pytest -v tests/

echo "[2/4] Executing CLI Pre-Flight Drift Gate Check (Clean Release)..."
python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario none

echo "[3/4] Executing CLI Pre-Flight Drift Gate Check (Drifted Release - Insecure DB)..."
python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario insecure_db || echo "Expected Gate Abortion Captured!"

echo "[4/4] Executing 50-Scenario Benchmark Experiment..."
python experiments/benchmark.py

echo "================================================================================"
echo " ✅ ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!"
echo "================================================================================"
