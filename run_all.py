"""
Unified Execution Script for Fintech Configuration-Drift Validator.
Runs Pytest test suite, CLI validation checks, automated rollback verification, benchmark experiment, and optional Web Server startup.
"""

import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_command(cmd, desc):
    print("================================================================================")
    print(f" EXECUTION STEP: {desc}")
    print(f" Command: {cmd}")
    print("--------------------------------------------------------------------------------")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"❌ Step failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"✅ Step completed successfully.\n")


def main():
    print("================================================================================")
    print("   FINTECH MICROSERVICE CONFIGURATION-DRIFT VALIDATOR (AGY SUITE RUNNER)")
    print("================================================================================\n")

    # 1. Run Pytest Suite
    run_command("pytest -v tests/", "Running Pytest Automated Test Suite")

    # 2. Run CLI Validation Demonstration
    run_command(
        "python cli/fintech_drift_val.py --service payment-processor --scenario none",
        "CLI Pre-Flight Drift Check (Clean Release)"
    )

    # 3. Run Automated Rollback Verification Step
    run_command(
        "python -c \"from pipeline.legacy_deploy import DeploymentPipeline, PipelineMode; from src.models import MicroserviceName, Environment; p = DeploymentPipeline(); p.execute_deployment(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, Environment.PRODUCTION, PipelineMode.LEGACY_UNSHIELDED, 'insecure_db'); r = p.trigger_rollback(MicroserviceName.PAYMENT_PROCESSOR); print('Rollback Verification Status:', r['status'])\"",
        "Verifying SHA-256 Snapshot Delta Tracking & Automated Rollback Engine"
    )

    # 4. Run Benchmark Experiment
    run_command("python experiments/benchmark.py", "Executing 50-Scenario Benchmark Experiment")

    print("================================================================================")
    print(" ALL VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print(" To start the interactive Web Dashboard, run:")
    print("   python -m uvicorn web.app:app --host 127.0.0.1 --port 8000")
    print("================================================================================")


if __name__ == "__main__":
    main()
