# ContextPilot Benchmark — Contract Review

End-to-end benchmark for evaluating LLM inference proxy optimizations on prefill-heavy OpenClaw agent workloads.

## Scenario

A company (TechVentures Pte Ltd) has 4 vendor service agreements:

| Contract | Vendor | Service | Size |
|----------|--------|---------|------|
| Alpha | CloudNine Solutions | Cloud infrastructure | ~45 KB |
| Beta | DeepMind Analytics | AI/ML platform | ~45 KB |
| Gamma | CyberShield | Cybersecurity operations | ~45 KB |
| Delta | DataStream Technologies | Data engineering | ~45 KB |

All 4 contracts share a common legal template (Articles 1–16, Schedules A–B) with vendor-specific terms in Article 17, payment schedules, and headers. Total corpus: **182 KB (~45K tokens)**.

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
# 1. Generate contract data into OpenClaw workspace
python scripts/gen_data.py

# 2. Start SGLang (terminal 1)
CUDA_VISIBLE_DEVICES=0 python -m sglang.launch_server \
  --model-path Qwen/Qwen3-4B-Instruct-2507 \
  --port 30002 --host 0.0.0.0 --tp-size 1 \
  --context-length 131072 --tool-call-parser hermes

# 3. Start ContextPilot proxy (terminal 2)
python -m contextpilot.server.http_server \
  --port 8771 --infer-api-url http://localhost:30002

# 4. Run benchmark
python scripts/run_bench.py

# 5. Analyze results
python scripts/analyze.py results/results.jsonl
```

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
│   └── contract_template.txt   # Shared legal template (Articles 1-16, Schedules)
├── results/
│   └── results.jsonl           # Benchmark results (30 scenarios × 2 arms)
└── scripts/
    ├── gen_data.py             # Generate 4 contracts into OpenClaw workspace
    ├── run_bench.py            # Run benchmark (manages SGLang/CP lifecycle)
    └── analyze.py              # Print paper-ready results table
```
