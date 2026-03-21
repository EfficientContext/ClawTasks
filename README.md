# claw-tasks

Prefill-heavy, multi-turn document analysis tasks for benchmarking LLM inference optimizations on [OpenClaw](https://openclaw.ai) agent workloads.

## Quick Start

```bash
git clone https://github.com/EfficientContext/ClawBench.git
cd ClawBench

# Run all 60 tasks
python scripts/run_bench.py --gpu 0

# Run one category
python scripts/run_bench.py --category commercial

# Analyze results
python scripts/analyze.py results/results.jsonl
```

## Data

An enterprise workspace of 18 private documents (260 KB total). A technology company manages four vendor relationships — each with contracts, amendments, assessments, NDAs, and internal policies.

The documents were constructed to reflect how enterprise document sets actually work: contracts use a shared legal template (Articles 1-16) with vendor-specific addenda. Amendments reference the original contracts. Vendor assessments quote SLA targets from the contracts. Internal policies are referenced in the MSA. Board minutes summarize vendor performance from the assessments.

This creates natural, realistic content overlap (~70% shared template across contracts) without any artificial duplication.

| Document Type | Files | Size | Content |
|---------------|-------|------|---------|
| Service Agreements | 4 | 182 KB | Cloud, AI, security, data vendor contracts |
| Amendments | 4 | 19 KB | Scope expansion, SLA tightening, sustainability terms |
| Master Service Agreement | 1 | 9 KB | Framework terms referenced by all contracts |
| Vendor Assessments | 4 | 16 KB | Annual reviews with SLA metrics, ratings, recommendations |
| Internal Policies | 2 | 13 KB | Information Security Policy, Data Governance Policy |
| Board Minutes | 1 | 8 KB | Q4 2024 board meeting on vendor strategy and risks |
| NDAs | 2 | 12 KB | Mutual non-disclosure agreements |

## Tasks

60 multi-turn tasks across 4 categories. Each task has 3-5 turns where a user asks an OpenClaw agent to read and analyze documents from the workspace.

### [`commercial/`](claw-tasks/commercial/) — 10 tasks

| Task | Turns | Documents Used | What the user asks |
|------|-------|----------------|-------------------|
| s01 Commercial Terms | 5 | 4 contracts | Compare values, durations, payment structures |
| s06 SLA Comparison | 4 | 4 contracts | Compare uptime, response, resolution targets |
| s13 Payment Risk | 4 | 4 contracts | Late payment penalties, audit rights, service credits |
| s18 Renewal Analysis | 4 | 4 contracts | Map expiration dates and renewal terms |
| s21 Cost Analysis | 4 | 4 contracts | Total financial commitments with bonuses/penalties |
| s31 Amendment Impact | 4 | contracts + amendments | Revised spend after amendments |
| s32 Assessment vs SLA | 4 | contracts + assessments | Did vendors meet their SLA targets? |
| s33 MSA Pricing | 4 | MSA + contracts | Are payment terms MSA-compliant? |
| s48 Service Credits | 4 | contract + assessment + amendment | Service credit exposure analysis |
| s49 Budget Reconciliation | 4 | board minutes + contracts | CFO's reported spend vs contract values |

### [`legal/`](claw-tasks/legal/) — 13 tasks

| Task | Turns | Documents Used | What the user asks |
|------|-------|----------------|-------------------|
| s02 Liability Review | 4 | 4 contracts | Extract and rank liability exposure |
| s04 IP Ownership | 4 | 4 contracts | IP assignment and licensing terms |
| s05 Termination Rights | 4 | 4 contracts | Termination triggers, notice, consequences |
| s08 Dispute Resolution | 4 | 4 contracts | Arbitration and mediation provisions |
| s11 Warranty Terms | 4 | 4 contracts | Warranty coverage and durations |
| s12 Confidentiality | 4 | 4 contracts | Confidentiality scope and survival |
| s14 Force Majeure | 4 | 4 contracts | Force majeure definitions and coverage |
| s34 NDA vs Contract | 4 | NDAs + contracts | NDA and contract confidentiality consistency |
| s35 Amendment Legal | 4 | contracts + amendments | Legal risks introduced by amendments |
| s36 MSA Legal Framework | 4 | MSA + contracts | Dispute resolution alignment with MSA |
| s50 Survival Clauses | 4 | contracts + NDAs | Post-termination protection gaps |
| s51 Assignment Restrictions | 4 | MSA + contracts | M&A assignment protections |
| s52 Indemnity Comparison | 4 | 4 contracts | Indemnification coverage ranking |

### [`compliance/`](claw-tasks/compliance/) — 20 tasks

| Task | Turns | Documents Used | What the user asks |
|------|-------|----------------|-------------------|
| s03 Data Protection | 5 | 4 contracts | Privacy clause compliance scorecard |
| s07 Insurance Audit | 4 | 4 contracts | Insurance coverage adequacy |
| s10 Subcontracting | 4 | 4 contracts | Subcontractor restrictions |
| s15 BCP/DR | 4 | 4 contracts | Business continuity requirements |
| s16 Personnel Requirements | 4 | 4 contracts | Staff qualification standards |
| s17 Acceptance Testing | 4 | 4 contracts | Deliverable acceptance procedures |
| s19 Compliance Scorecard | 5 | 4 contracts | Multi-dimension compliance rating |
| s22 Audit Rights | 4 | 4 contracts | Audit provision comparison |
| s26 Open Source | 4 | 4 contracts | SBOM and open-source requirements |
| s27 Cross-Border | 4 | 4 contracts | Data sovereignty and transfers |
| s28 Breach Response | 4 | 4 contracts | Breach notification and remediation |
| s37 Policy vs Contract | 4 | security policy + contracts | Contracts vs InfoSec policy gaps |
| s38 Data Governance | 4 | data governance policy + contracts | Data quality and retention compliance |
| s39 MSA Compliance | 4 | MSA + assessments | Vendor re-qualification status |
| s40 Amendment Compliance | 4 | amendments + policy | Amendment compliance with policies |
| s41 Cross-Doc Privacy | 5 | policy + contract + NDA + MSA | Cross-document privacy compliance matrix |
| s53 Certification Tracking | 4 | assessments + policy | Vendor certification expiry tracker |
| s54 Incident History | 4 | assessments + board minutes + policy | Incident handling compliance |
| s55 Data Retention Audit | 4 | data governance policy + contracts | Retention period compliance matrix |
| s56 Access Control Review | 4 | policy + contract + MSA | Access control gap analysis |

### [`strategic/`](claw-tasks/strategic/) — 17 tasks

| Task | Turns | Documents Used | What the user asks |
|------|-------|----------------|-------------------|
| s09 Change Management | 4 | 4 contracts | Change order process comparison |
| s20 Vendor Comparison | 4 | 4 contracts | Side-by-side vendor ranking |
| s23 Knowledge Transfer | 4 | 4 contracts | Transition readiness assessment |
| s24 Security Assessment | 4 | 4 contracts | Security provision comparison |
| s25 Exit Strategy | 4 | 4 contracts | Exit plan with costs and timelines |
| s29 Board Summary | 3 | 4 contracts | Executive summary for board |
| s30 Negotiation Prep | 4 | 4 contracts | Unfavorable terms and amendments |
| s42 Board Follow-up | 4 | board minutes + assessments + amendment | Board action item status |
| s43 Risk Register | 4 | board minutes + contracts + policy | Risk mitigation coverage mapping |
| s44 Vendor Renewal Strategy | 4 | assessments + amendment + board minutes | Renewal strategy document |
| s45 Onboarding Checklist | 4 | MSA + both policies | New vendor onboarding checklist |
| s46 Incident Readiness | 5 | contract + policy + assessment + board minutes | Incident readiness assessment |
| s47 Full Portfolio Review | 4 | MSA + 4 assessments + 2 policies + board minutes | Comprehensive annual review |
| s57 CTO Briefing | 4 | board minutes + assessments + amendment | CTO board briefing prep |
| s58 Transition Plan | 4 | contract + MSA + assessment | Vendor replacement plan |
| s59 Sustainability Report | 4 | amendments + board minutes | ESG disclosure draft |
| s60 Annual Review Package | 4 | assessments + MSA + board minutes | Complete vendor review package |

## Workload Characteristics

| Property | Value |
|----------|-------|
| Total tasks | 60 |
| Total turns | ~250 |
| Documents per task | 2-8 |
| Avg input tokens (turn 0) | ~25K |
| Avg input tokens (turn 3) | ~65K |
| Max input tokens | ~93K |
| Avg output tokens | ~740 |
| Input/output ratio | ~60:1 |
| Content overlap (contracts) | ~70% |

## File Structure

```
├── README.md
├── data/
│   └── workspace/              # 18 enterprise documents (260 KB)
├── claw-tasks/
│   ├── commercial/tasks.json   # 10 tasks
│   ├── legal/tasks.json        # 13 tasks
│   ├── compliance/tasks.json   # 20 tasks
│   └── strategic/tasks.json    # 17 tasks
├── scripts/
│   ├── run_bench.py
│   └── analyze.py
└── results/                    # Generated by run_bench.py
```

## License

Apache 2.0
