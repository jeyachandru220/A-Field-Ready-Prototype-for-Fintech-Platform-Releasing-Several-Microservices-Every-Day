"""
Command Line Interface (CLI) for Fintech Microservices Configuration-Drift Validator.
Allows developers and CI/CD pipelines to run pre-flight drift validation from terminal.
"""

import sys
import argparse
import json
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import MicroserviceName, Environment
from src.validator import ConfigurationDriftValidator
from simulation.environment_generator import EnvironmentSimulator
from pipeline.legacy_deploy import DeploymentPipeline, PipelineMode


def main():
    parser = argparse.ArgumentParser(
        description="Fintech Microservice Configuration-Drift Validator CLI"
    )
    parser.add_argument(
        "--service",
        type=str,
        choices=[s.value for s in MicroserviceName],
        default="payment-processor",
        help="Target microservice name"
    )
    parser.add_argument(
        "--source-env",
        type=str,
        choices=[e.value for e in Environment],
        default="staging",
        help="Source environment (e.g. staging)"
    )
    parser.add_argument(
        "--target-env",
        type=str,
        choices=[e.value for e in Environment],
        default="production",
        help="Target environment (e.g. production)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="none",
        choices=["none", "insecure_db", "expired_vault_key", "memory_mismatch", "missing_compliance_flag", "sandbox_url_leak"],
        help="Drift scenario to simulate"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full validation report in raw JSON"
    )
    parser.add_argument(
        "--deploy-mode",
        type=str,
        choices=["legacy", "shielded"],
        default="shielded",
        help="Simulate deployment pipeline in legacy or shielded mode"
    )

    args = parser.parse_args()

    svc = MicroserviceName(args.service)
    src_env = Environment(args.source_env)
    tgt_env = Environment(args.target_env)

    src_cfg = EnvironmentSimulator.get_service_config(svc, src_env, "none")
    tgt_cfg = EnvironmentSimulator.get_service_config(svc, tgt_env, args.scenario)

    if args.json:
        report = ConfigurationDriftValidator.validate_deployment(src_cfg, tgt_cfg)
        print(json.dumps(report.dict(), indent=2))
        sys.exit(0 if report.passed_deployment_gate else 1)

    print("================================================================================")
    print(f"       FINTECH CONFIGURATION-DRIFT VALIDATOR CLI (AGY SHIELD v2.4)")
    print("================================================================================")
    print(f" Service:      {svc.value.upper()}")
    print(f" Pipeline:     {args.deploy_mode.upper()} MODE")
    print(f" Route:        {src_env.value.upper()} -> {tgt_env.value.upper()}")
    print(f" Scenario:     {args.scenario}")
    print("--------------------------------------------------------------------------------")

    pipeline = DeploymentPipeline()
    mode = PipelineMode.SHIELDED_VALIDATOR if args.deploy_mode == "shielded" else PipelineMode.LEGACY_UNSHIELDED
    res = pipeline.execute_deployment(svc, src_env, tgt_env, mode, args.scenario)

    print(f"\nSTATUS: {res['status']}")
    print(f"GATE PASSED: {res['gate_passed']}")
    print(f"MESSAGE: {res['message']}\n")

    if "report" in res:
        rep = res["report"]
        print(f"Risk Score: {rep['risk_score']}/100")
        print(f"Total Discrepancies: {rep['total_discrepancies']}")
        print(f"  - CRITICAL: {rep['critical_count']}")
        print(f"  - HIGH:     {rep['high_count']}")
        print(f"  - MEDIUM:   {rep['medium_count']}")
        print(f"  - LOW:      {rep['low_count']}\n")

        print("Top Non-Specialist Risk Recommendations:")
        for idx, d in enumerate(rep["drifts"], 1):
            print(f" [{idx}] Layer: {d['layer']} | Key: {d['key']}")
            print(f"     Risk Level:    {d['risk_level']} ({d['category']})")
            print(f"     Plain Summary: {d['plain_english_summary']}")
            print(f"     Est. Cost:     {d['financial_risk_estimate']}")
            print(f"     Regulation:    {d['regulatory_impact']}")
            print(f"     Action Needed: {d['recommended_action']}\n")

    sys.exit(0 if res["gate_passed"] else 1)


if __name__ == "__main__":
    main()
