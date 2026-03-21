# Contract Review Benchmark

A prefill-heavy, multi-turn document analysis benchmark for evaluating LLM inference optimizations on agentic workloads.

## Scenario

A technology company (TechVentures Pte Ltd) manages four vendor relationships for cloud infrastructure, AI/ML, cybersecurity, and data engineering. The company's private document workspace contains 18 files:

| Category | Files | Size | Description |
|----------|-------|------|-------------|
| Service Agreements | 4 | 182 KB | Vendor contracts sharing a common legal template with vendor-specific terms |
| Amendments | 4 | 19 KB | Contract modifications (scope expansion, SLA tightening, sustainability) |
| Master Service Agreement | 1 | 9 KB | Framework terms referenced by all vendor contracts |
| Vendor Assessments | 4 | 16 KB | Annual performance reviews with SLA metrics and scores |
| Internal Policies | 2 | 13 KB | Information Security Policy and Data Governance Policy |
| Board Minutes | 1 | 8 KB | Q4 2024 board meeting discussing vendor strategy |
| NDAs | 2 | 12 KB | Mutual non-disclosure agreements with two vendors |

**Total: 18 files, 260 KB (~65K tokens).**

## Tasks

30 multi-turn contract review tasks, each with 3-5 turns (122 turns total). Each task represents a realistic legal/compliance workflow where an employee asks an AI agent to analyze vendor documents.

| # | Task | Turns | What the user asks |
|---|------|-------|--------------------|
| s01 | Commercial Terms | 5 | Read each contract, compare values, durations, payment structures, produce comparison table |
| s02 | Liability Review | 4 | Extract liability and indemnification clauses from each contract, rank by exposure, write risk memo |
| s03 | Data Protection | 5 | Evaluate privacy clauses per contract, assess compliance gaps, produce scorecard |
| s04 | IP Ownership | 4 | Analyze IP assignment and licensing terms, identify protection gaps |
| s05 | Termination Rights | 4 | Compare termination triggers, notice periods, and consequences across all contracts |
| s06 | SLA Comparison | 4 | Extract and compare uptime, response time, and resolution targets |
| s07 | Insurance Audit | 4 | Review insurance coverage requirements, flag inadequacies |
| s08 | Dispute Resolution | 4 | Analyze arbitration and mediation provisions, write summary memo |
| s09 | Change Management | 4 | Compare change order processes and emergency change handling |
| s10 | Subcontracting | 4 | Review subcontractor restrictions and approval requirements |
| s11 | Warranty Terms | 4 | Compare warranty coverage, durations, and weak spots |
| s12 | Confidentiality | 4 | Analyze confidentiality scope, survival periods, and gaps |
| s13 | Payment Risk | 4 | Assess late payment penalties, audit rights, service credits |
| s14 | Force Majeure | 4 | Compare force majeure definitions, check if cyberattacks are covered |
| s15 | BCP/DR | 4 | Evaluate business continuity and disaster recovery requirements |
| s16 | Personnel Requirements | 4 | Compare qualification and certification standards for vendor staff |
| s17 | Acceptance Testing | 4 | Review deliverable acceptance procedures and timelines |
| s18 | Renewal Analysis | 4 | Map contract expiration dates and renewal terms |
| s19 | Compliance Scorecard | 5 | Rate all contracts on 5 compliance dimensions |
| s20 | Vendor Comparison | 4 | Side-by-side vendor ranking, identify highest-risk vendor |
| s21 | Cost Analysis | 4 | Calculate total financial commitments including bonuses and penalties |
| s22 | Audit Rights | 4 | Compare audit provisions across vendors |
| s23 | Knowledge Transfer | 4 | Assess transition and handover readiness for each vendor |
| s24 | Security Assessment | 4 | Evaluate security provisions, compare across all vendors |
| s25 | Exit Strategy | 4 | Develop exit plan with costs, timelines, and data retrieval |
| s26 | Open Source | 4 | Review open-source software and SBOM requirements |
| s27 | Cross-Border | 4 | Assess data sovereignty and cross-border transfer provisions |
| s28 | Breach Response | 4 | Compare breach notification timelines and remediation terms |
| s29 | Board Summary | 3 | Produce a one-page executive summary for the board of directors |
| s30 | Negotiation Prep | 4 | Identify unfavorable terms, propose specific amendment language |

## Why This Benchmark

**Realistic enterprise workload.** Contract review is one of the most common uses of AI agents in enterprise settings. Companies deploy agents (like OpenClaw) to help employees analyze vendor agreements, audit compliance, and prepare negotiation strategies. These are real tasks that real legal, procurement, and compliance teams perform.

**Natural content overlap.** Enterprise documents are not independent — they are template-based, cross-referenced, and share boilerplate language. The four service agreements in this benchmark use the same legal template (Articles 1-16, Schedules A-B), differing only in vendor-specific terms. Amendments reference original contracts. Vendor assessments quote contract SLA targets. This overlap pattern is universal in enterprise document workflows.

**Prefill-heavy, decode-light.** Each turn reads one or more large documents (~45KB contracts) and asks a focused analytical question. The agent's response is short relative to the input context. This workload profile — long input, short output — is where inference optimization matters most, as prefill dominates total latency.

**Private data, local deployment.** Sensitive contracts, NDAs, and internal policies cannot be sent to cloud APIs. This benchmark targets local LLM inference (e.g., SGLang) where efficiency directly impacts user experience and hardware cost.

**Multi-turn context growth.** As the agent reads more documents across turns, the conversation history grows. By turn 4, the context may contain 3-4 full contracts (~180KB of tool results). This creates a natural stress test for context management and caching strategies.

## Workload Characteristics

| Property | Value |
|----------|-------|
| Documents per task | 2-4 (read across turns) |
| Avg input tokens (turn 0) | ~25K |
| Avg input tokens (turn 3) | ~65K |
| Max input tokens observed | ~93K |
| Avg output tokens | ~740 |
| Input/output ratio | ~60:1 |
| Content overlap between contracts | ~70% (shared template) |

## Quick Start

```bash
# Run benchmark (copies documents to OpenClaw workspace, manages server lifecycle)
python scripts/run_bench.py --gpu 0

# Analyze results
python scripts/analyze.py results/results.jsonl
```

Options:
```bash
python scripts/run_bench.py --gpu 2                    # specify GPU
python scripts/run_bench.py --trials 3                 # multiple trials for statistical significance
python scripts/run_bench.py --scenarios s01_commercial_terms s02_liability_review  # run specific tasks
```

## File Structure

```
contract-review/
├── README.md
├── data/
│   ├── tasks.json              # 30 task definitions (name + turns)
│   └── workspace/              # 18 enterprise documents (260 KB)
│       ├── contract_*.txt      # 4 vendor service agreements
│       ├── amendment_*.txt     # 4 contract amendments
│       ├── vendor_assessment_*.txt
│       ├── master_service_agreement.txt
│       ├── policy_*.txt
│       ├── board_minutes_*.txt
│       └── nda_*.txt
├── results/                    # Generated by run_bench.py
└── scripts/
    ├── run_bench.py            # Benchmark runner
    └── analyze.py              # Results analysis
```
