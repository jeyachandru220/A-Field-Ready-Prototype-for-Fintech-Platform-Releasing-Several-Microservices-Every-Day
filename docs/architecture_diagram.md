# System Architecture & Multi-Layer Inspection Flow

## High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Configuration Sources (4 Layers)
        L1[Layer 1: IaC Manifests<br/>K8s YAML / Docker Spec]
        L2[Layer 2: Environment Variables<br/>ConfigMaps / .env]
        L3[Layer 3: Secrets Metadata<br/>Vault Keys, Rotation, TTL]
        L4[Layer 4: Runtime Snapshots<br/>Active Pod Mem, SSL state]
    end

    subgraph Core Validation Engine
        AST[Multi-Layer AST Parser]
        SEM[Semantic Schema Checker]
        TRANS[Plain-English Translator]
        SCORE[Risk Score Calculator<br/>0 - 100 Meter]
    end

    subgraph CI/CD Pipeline & Gating
        GATE{Pre-Deployment Safety Gate<br/>Score < 25 & 0 Critical}
        LEGACY[Legacy CI/CD Pipeline]
        ROLLBACK[Automated Rollback Engine]
    end

    subgraph Target Environments
        STG[Staging Environment]
        PROD[Production Cluster]
    end

    L1 --> AST
    L2 --> AST
    L3 --> AST
    L4 --> AST

    AST --> SEM
    SEM --> TRANS
    TRANS --> SCORE
    SCORE --> GATE

    GATE -- Passed (Score < 25) --> PROD
    GATE -- Blocked (Critical > 0) --> ABORT[Abort Deployment & Notify Slack/PagerDuty]
    LEGACY -- Unshielded Mode --> PROD
    PROD -- Drift Detected Post-Deploy --> ROLLBACK
    ROLLBACK --> STG
```

---

## 4-Layer Inspection Workflow

1. **Layer 1: Infrastructure Definitions (IaC Specs)**
   - Compares declared CPU requests/limits, Memory requests/limits, min/max replica counts, container ports, and ingress TLS configurations.

2. **Layer 2: Environment Variables**
   - Evaluates key-value pairs for DB connection strings (`sslmode`), host endpoints, batch sizes, and mandatory compliance flags (`MANDATE_STRIP_PAN`).
   - Filters out expected environment differences (e.g. `db-staging` vs `db-production`) while flagging dangerous staging endpoint leaks into production.

3. **Layer 3: Secrets Metadata (Zero Raw Secret Exposure)**
   - Inspects Vault secret key paths, key versions, last rotation timestamps, and TTL expiration statuses without ever reading or exposing raw secret strings.

4. **Layer 4: Runtime Snapshots & IaC Cross-Checking**
   - Validates live running container metrics against IaC declarations.
   - Detects when active container pod memory allocation (e.g. 512MB) is capped lower than IaC specification (e.g. 4Gi), preventing silent OOM evictions.

---

## Pre-Deployment Safety Gate Logic

$$\text{Risk Score} = \min\left(100, \, 40.0 \times N_{\text{Critical}} + 20.0 \times N_{\text{High}} + 8.0 \times N_{\text{Medium}} + 2.0 \times N_{\text{Low}}\right)$$

$$\text{Gate Decision} = \begin{cases} 
\text{APPROVED}, & \text{if } \text{Risk Score} < 25.0 \text{ and } N_{\text{Critical}} = 0 \\
\text{BLOCKED}, & \text{otherwise}
\end{cases}$$
