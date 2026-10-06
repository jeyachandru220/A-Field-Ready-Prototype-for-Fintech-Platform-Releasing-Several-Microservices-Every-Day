# User & Stakeholder Operational Guide

This guide provides instructions for developers, DevOps engineers, and non-specialist reviewers to operate the **Fintech Microservices Configuration-Drift Validator**.

---

## 1. Quick Start Guide

### System Prerequisites
- **Python 3.10+** (Tested on Python 3.13.2)
- Installed dependencies: `fastapi`, `uvicorn`, `pydantic`, `pytest`

### Starting the Interactive Web Dashboard
Run the following command from the workspace root:

```bash
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 2. Using the Interactive Web Dashboard

### Feature Overview
1. **Top Control Panel**: Select target microservice (`payment-processor`, `ledger-core`, `auth-vault`, `risk-engine`), environment route, and inject drift scenarios.
2. **Reviewer Mode Toggle**: Switch between **Non-Specialist Executive View** (plain-English risk summaries, financial risk estimates, regulatory standards, 1-click remediation actions) and **Developer Deep-Dive View** (AST JSON diffs and raw keys).
3. **Pre-Deployment Safety Gate Card**: Displays the live Risk Score (0–100), risk breakdown counts, and gating status (`PASSED` vs `BLOCKED`).
4. **4-Layer Audit Cards**: Real-time status badges across Infrastructure Definitions (IaC), Environment Variables, Secrets Metadata, and Runtime Container Snapshots.
5. **Deployment Pipeline Simulator**:
   - `Shielded Gate Deploy`: Pre-flight drift check blocks risky releases before production.
   - `Legacy Pipeline Deploy`: Demonstrates unshielded release where drift reaches production.
   - `Execute Automated Rollback`: 1-click restoration of production state to last verified safe baseline.
6. **50-Scenario Benchmark Runner**: Click **Run 50-Scenario Benchmark** to execute the benchmark experiment and display the metrics comparison table.

---

## 3. Using the Command-Line Interface (CLI)

The CLI tool allows developers and CI/CD pipelines to run pre-flight drift checks directly in terminal.

### Basic Usage

```bash
# Validate payment-processor Staging -> Production with clean config
python cli/fintech_drift_val.py --service payment-processor --scenario none

# Test edge case: Insecure DB SSL mode
python cli/fintech_drift_val.py --service payment-processor --scenario insecure_db

# Output raw JSON report for CI pipeline parsing
python cli/fintech_drift_val.py --service auth-vault --scenario expired_vault_key --json
```

---

## 4. Running the Pytest Test Suite

Execute the full automated test suite covering edge cases, pipeline migration, and rollbacks:

```bash
pytest -v tests/
```
