#!/usr/bin/env bash
# Local CI Pipeline Reproducer Script
set -e

echo "================================================================================"
echo "   REPRODUCIBLE CI PIPELINE EXECUTION (MATCHES GITHUB ACTIONS DRIFT-GATE)"
echo "================================================================================"

echo "[CI Step 1] Validating Python environment..."
python --version
pip --version

echo "[CI Step 2] Running pytest test suite with code coverage..."
pytest -v tests/

echo "[CI Step 3] Executing Pre-Flight Drift Gate Check (Clean Scenario)..."
python cli/fintech_drift_val.py --service payment-processor --source-env staging --target-env production --scenario none

echo "[CI Step 4] Executing 50-Scenario Benchmark Experiment..."
python experiments/benchmark.py

echo "================================================================================"
echo " ✅ REPRODUCIBLE CI PIPELINE COMPLETED WITH EXIT CODE 0"
echo "================================================================================"
