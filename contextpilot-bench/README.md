# ContextPilot Benchmark — Contract Review

End-to-end benchmark for evaluating LLM inference proxy optimizations on prefill-heavy OpenClaw agent workloads.

## Scenario

A company (TechVentures Pte Ltd) manages its technology vendor relationships through a private document workspace containing 18 files across 7 document types:

| Category | Files | Size | Description |
|----------|-------|------|-------------|
| Service Agreements | 4 | 182 KB | Vendor contracts (cloud, AI, security, data) sharing Articles 1–16 template |
| Amendments | 4 | 19 KB | Contract modifications (scope expansion, SLA tightening, sustainability) |
| Master Service Agreement | 1 | 9 KB | Framework terms referenced by all vendor contracts |
| Vendor Assessments | 4 | 16 KB | Annual performance reviews with SLA metrics and scores |
| Internal Policies | 2 | 13 KB | Information Security Policy and Data Governance Policy |
| Board Minutes | 1 | 8 KB | Q4 2024 board meeting discussing vendor strategy |
| NDAs | 2 | 12 KB | Mutual non-disclosure agreements with two vendors |

**Total corpus: 18 files, 260 KB (~65K tokens).**

Documents share content naturally: contracts use the same legal template, amendments reference original contracts, vendor assessments quote contract SLA targets, policies are referenced in the MSA, and board minutes summarize vendor performance.

30 contract-review tasks simulate realistic legal workflows:

| # | Task | Turns | Description |
|---|------|-------|-------------|
| s01 | Commercial Terms | 5 | Compare contract values, durations, payment structures |
| s02 | Liability Review | 4 | Extract and compare liability caps and indemnification |
| s03 | Data Protection | 5 | Evaluate privacy clauses and compliance gaps |
| s04 | IP Ownership | 4 | Analyze IP assignment and licensing terms |
| s05 | Termination Rights | 4 | Compare termination triggers and notice periods |
| s06 | SLA Comparison | 4 | Compare uptime, response time, resolution targets |
| s07 | Insurance Audit | 4 | Review insurance coverage requirements |
| s08 | Dispute Resolution | 4 | Analyze arbitration and mediation provisions |
| s09 | Change Management | 4 | Compare change order processes |
| s10 | Subcontracting | 4 | Review subcontractor restrictions |
| s11 | Warranty Terms | 4 | Compare warranty coverage and durations |
| s12 | Confidentiality | 4 | Analyze confidentiality scope and survival periods |
| s13 | Payment Risk | 4 | Assess late payment, audit rights, service credits |
| s14 | Force Majeure | 4 | Compare force majeure definitions and coverage |
| s15 | BCP/DR | 4 | Evaluate business continuity requirements |
| s16 | Personnel Requirements | 4 | Compare qualification and certification standards |
| s17 | Acceptance Testing | 4 | Review deliverable acceptance procedures |
| s18 | Renewal Analysis | 4 | Map contract terms and renewal timelines |
| s19 | Compliance Scorecard | 5 | Rate all contracts on 5 compliance dimensions |
| s20 | Vendor Comparison | 4 | Side-by-side vendor ranking |
| s21 | Cost Analysis | 4 | Calculate total financial commitments |
| s22 | Audit Rights | 4 | Compare audit provisions across vendors |
| s23 | Knowledge Transfer | 4 | Assess transition and handover readiness |
| s24 | Security Assessment | 4 | Evaluate security provisions across all vendors |
| s25 | Exit Strategy | 4 | Develop exit plan with costs and timelines |
| s26 | Open Source | 4 | Review open-source and SBOM requirements |
| s27 | Cross-Border | 4 | Assess data sovereignty and transfer provisions |
| s28 | Breach Response | 4 | Compare breach notification and remediation terms |
| s29 | Board Summary | 3 | Produce executive summary for board |
| s30 | Negotiation Prep | 4 | Identify unfavorable terms and propose amendments |

Total: **122 turns per arm**.

## Why This Benchmark

- **Realistic enterprise workload**: Contract review is a primary use case for deployed LLM agents. Companies use OpenClaw to help employees analyze vendor agreements, compliance documents, and legal terms.
- **Template-based documents**: Legal contracts are ubiquitously based on standardized boilerplate — same structure, different specifics. This creates natural content overlap across documents that a proxy can exploit.
- **Prefill-heavy, decode-light**: Each turn reads one or more 45KB contracts (high prefill), then asks a focused analytical question (short output). This is the workload profile where context optimization matters most.
- **Private data, local deployment**: Sensitive contracts require local LLM inference (SGLang) rather than cloud APIs, making inference efficiency critical.
- **SGLang Radix Cache limitation**: Radix Cache only matches token prefixes. When an agent reads multiple contracts in sequence, shared template content appears at different positions across tool results — not as a prefix. A proxy-level optimization can reduce these tokens before they reach the engine.

## Results (ContextPilot)

```
Dataset: 30 scenarios, 4 docs × ~45KB (182KB total), 122 turns/arm
Model: Qwen3-4B-Instruct-2507 · SGLang 0.5.9 · RTX PRO 6000 Blackwell

                                                  Avg          P50          P99
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prompt Tokens
  OpenClaw + SGLang                            43,914       43,840       93,022
  OpenClaw + ContextPilot + SGLang             31,000       31,476       44,631
  Δ                                            -29.4%       -28.2%       -52.0%

Wall Time (s)
  OpenClaw + SGLang                              25.2         23.7         68.8
  OpenClaw + ContextPilot + SGLang               18.4         20.2         35.7
  Δ                                            -26.9%       -14.8%       -48.1%

Completion Tokens
  OpenClaw + SGLang                               744          910         1024
  OpenClaw + ContextPilot + SGLang                731          880         1024
  Δ                                             -1.7%        -3.2%        +0.0%

Accuracy (substantive output)
  OpenClaw + SGLang                      122/122 (100.0%)
  OpenClaw + ContextPilot + SGLang       122/122 (100.0%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quick Start

```bash
# 1. Run benchmark (auto-copies documents to OpenClaw workspace, manages SGLang/CP lifecycle)
python scripts/run_bench.py --gpu 0

# 2. Analyze results
python scripts/analyze.py results/results.jsonl
```

The runner handles everything: copies documents to OpenClaw workspace, starts/stops SGLang and ContextPilot for each scenario, and saves results to `results/results.jsonl`.

Options:
```bash
python scripts/run_bench.py --gpu 2           # specify GPU
python scripts/run_bench.py --trials 3        # multiple trials
python scripts/run_bench.py --scenarios s01_commercial_terms s02_liability_review
```

## File Structure

```
contextpilot-bench/
├── README.md
├── data/
│   ├── tasks.json              # 30 scenario definitions (name + turns)
│   └── workspace/              # 18 enterprise documents (260 KB)
│       ├── contract_*.txt      # 4 vendor service agreements (~45 KB each)
│       ├── amendment_*.txt     # 4 contract amendments
│       ├── vendor_assessment_*.txt  # 4 annual vendor reviews
│       ├── master_service_agreement.txt
│       ├── policy_*.txt        # Information security + data governance
│       ├── board_minutes_*.txt # Q4 2024 board meeting
│       └── nda_*.txt           # 2 mutual NDAs
├── results/
│   └── results.jsonl           # Benchmark results (30 scenarios × 2 arms)
└── scripts/
    ├── run_bench.py            # Run benchmark
    └── analyze.py              # Print paper-ready results table
```
