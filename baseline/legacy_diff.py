"""
Simple Baseline Validator (Legacy Naive Script).
Represents traditional basic diff tools that perform flat line-by-line key comparisons
without AST schema awareness, secrets metadata parsing, runtime cross-checking,
or non-specialist risk evaluation.
"""

from typing import Dict, Any, List
from src.models import ServiceEnvironmentConfig


class LegacyBaselineDiff:
    """
    Naive baseline validator.
    Only checks string equality of environment variable keys present in both files.
    Demonstrates baseline failures: ignores host differences, but remains completely blind
    to secrets metadata expiry and runtime container snapshots.
    """

    @classmethod
    def validate(cls, source_config: ServiceEnvironmentConfig, target_config: ServiceEnvironmentConfig) -> Dict[str, Any]:
        s_vars = source_config.env_vars.vars
        t_vars = target_config.env_vars.vars

        discrepancies = []
        for k, s_val in s_vars.items():
            if k not in t_vars:
                discrepancies.append({
                    "key": k,
                    "type": "MISSING_KEY",
                    "details": f"Key {k} missing in target env"
                })
            else:
                # Legacy scripts ignore host/env name differences between staging and prod
                if any(h in k for h in ["HOST", "URL", "ENV", "ENVIRONMENT"]):
                    continue

                if t_vars[k] != s_val:
                    discrepancies.append({
                        "key": k,
                        "type": "VALUE_MISMATCH",
                        "details": f"{k}: {s_val} != {t_vars[k]}"
                    })

        # Naive baseline passes if missing keys/unignored var mismatches == 0
        passed = (len(discrepancies) == 0)

        return {
            "validator_type": "Legacy Naive Baseline",
            "service": source_config.service.value,
            "discrepancies_found": len(discrepancies),
            "discrepancies": discrepancies,
            "passed_deployment_gate": passed,
            "blindspots": [
                "Cannot inspect Infrastructure Definitions (IaC Specs vs Runtime)",
                "Completely ignores Secrets Metadata & Vault Expiration",
                "Completely ignores Runtime Container Snapshots & Active SSL state",
                "Cannot translate diffs to non-specialist business risk or financial impact"
            ]
        }
