# Mathematical Risk Model & Scoring Matrix Specification

This document details the mathematical model, weighting matrix, environmental scale factors, and threshold logic used by the Configuration-Drift Validator to calculate the unified Risk Score ($0 \text{ to } 100$) and estimate financial risk exposure.

---

## 1. Unified Risk Score Mathematical Formula

$$\text{Risk Score} = \min\left(100.0, \, \sum_{i=1}^{N} W(R_i) \cdot E(T) \cdot C(K_i)\right)$$

Where:
- $N$ is the total number of detected configuration discrepancies.
- $W(R_i)$ is the Base Severity Weight for risk level $R_i$.
- $E(T)$ is the Target Environment Multiplier for target environment $T$.
- $C(K_i)$ is the Category Impact Multiplier for category $K_i$.

---

## 2. Base Severity Weight Matrix $W(R_i)$

- **CRITICAL Risk Weight**: $W(\text{CRITICAL}) = 40.0$
  - Applied to unencrypted Production database transport (`sslmode=disable`), expired Vault secret keys, unmasked PAN credit card logging, and staging sandbox endpoint leaks.
- **HIGH Risk Weight**: $W(\text{HIGH}) = 20.0$
  - Applied to container memory allocation cap discrepancies (IaC 4Gi vs container 512MB) and secret version mismatches.
- **MEDIUM Risk Weight**: $W(\text{MEDIUM}) = 8.0$
  - Applied to unrotated vault keys approaching TTL expiration and unaligned timeout settings.
- **LOW Risk Weight**: $W(\text{LOW}) = 2.0$
  - Applied to verbose logging levels in non-production environments.
- **INFO Risk Weight**: $W(\text{INFO}) = 0.0$
  - Applied to expected environment scaling parameters (e.g. min replicas 2 in Staging vs 4 in Production).

---

## 3. Environmental & Category Multipliers

### Target Environment Multiplier $E(T)$
- Production ($T = \text{production}$): $E(\text{production}) = 1.0$
- Staging ($T = \text{staging}$): $E(\text{staging}) = 0.5$
- Development ($T = \text{development}$): $E(\text{development}) = 0.2$

### Category Impact Multiplier $C(K_i)$
- Security Category ($K_i = \text{Security}$): $C = 1.25$
- Compliance Category ($K_i = \text{Compliance}$): $C = 1.25$
- Operational & Financial ($K_i = \text{Operational}$): $C = 1.0$
- Reliability & Capacity ($K_i = \text{Reliability}$): $C = 1.0$

---

## 4. Threshold & Pre-Deployment Gating Logic

$$\text{Gate Decision} = \begin{cases} 
\text{APPROVED}, & \text{if } \text{Risk Score} < 25.0 \quad \text{AND} \quad N_{\text{CRITICAL}} = 0 \\
\text{BLOCKED}, & \text{if } \text{Risk Score} \ge 25.0 \quad \text{OR} \quad N_{\text{CRITICAL}} \ge 1
\end{cases}$$

### Justification for Threshold = 25.0
- A single **HIGH** discrepancy ($W = 20.0$) yields a Risk Score of $20.0$, which is under $25.0$ and permits deployment if no Critical issues exist.
- Two **HIGH** discrepancies ($20.0 + 20.0 = 40.0$) exceed $25.0$ and trigger an automatic block.
- Any single **CRITICAL** discrepancy ($W = 40.0$) automatically breaches both the $25.0$ threshold and the $N_{\text{CRITICAL}} = 0$ constraint, guaranteeing immediate pre-flight deployment abortion.

---

## 5. Financial Risk Estimation Formula

$$\text{Estimated Financial Risk} = \left(\text{Estimated Downtime Hours} \times \text{Hourly Revenue at Risk}\right) + \text{Regulatory Penalty Base}$$

- **Payment Outage (CRITICAL Secret Expiry / Insecure SSL)**:
  - Estimated Downtime: 1.5 hours
  - Hourly Revenue at Risk: $100,000 / hr
  - Regulatory Fine (PCI-DSS): $100,000
  - Total Financial Risk: $\$150,000 + \$100,000 = \$250,000+$
- **Out-of-Memory Pod Crash (IaC vs Runtime Memory Mismatch)**:
  - Estimated Downtime: 0.8 hours
  - Hourly Revenue at Risk: $100,000 / hr
  - Total Financial Risk: $\$80,000$
