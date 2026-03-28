# claw-tasks

Prefill-heavy, multi-turn tasks for benchmarking LLM inference optimizations on [OpenClaw](https://openclaw.ai) agent workloads. Includes document analysis and iterative coding scenarios.

## Prerequisites

- [OpenClaw](https://openclaw.ai) installed with Node.js v22+
- [SGLang](https://github.com/sgl-project/sglang) with a model (e.g., `Qwen/Qwen3-4B-Instruct-2507`)
- [ContextPilot](https://github.com/EfficientContext/ContextPilot) or any inference proxy to evaluate

The runner copies documents from `data/workspace/` to OpenClaw's workspace (`~/.openclaw/workspace/contracts/`) automatically.

## Quick Start

```bash
git clone https://github.com/EfficientContext/ClawTasks.git
cd ClawTasks

# Run all 70 tasks
python scripts/run_bench.py --gpu 0

# Run one category
python scripts/run_bench.py --category commercial
python scripts/run_bench.py --category coding

# Analyze results
python scripts/analyze.py results/results.jsonl
```

## Overview

22 synthetic enterprise documents (490 KB) + 1 codebase file (290 lines), 70 tasks across 5 categories, ~290 turns total.

| Category | Tasks | Focus |
|----------|-------|-------|
| [`commercial/`](claw-tasks/commercial/) | 10 | Contract values, SLAs, payments, proposal pricing, cost analysis |
| [`legal/`](claw-tasks/legal/) | 12 | Liability, IP, termination, confidentiality, NDA alignment, indemnification |
| [`compliance/`](claw-tasks/compliance/) | 18 | Data protection, policies, certifications, proposal compliance, security audit |
| [`strategic/`](claw-tasks/strategic/) | 20 | Vendor selection, procurement review, board briefings, lifecycle reviews |
| [`coding/`](claw-tasks/coding/) | 10 | Iterative code modification — agent outputs complete file each turn |

See [`claw-tasks/`](claw-tasks/) for per-task details and [`data/`](data/) for document sources and construction notes.

## Scenario

A technology company (Company A Pte Ltd) manages four vendor relationships for cloud, AI, security, and data services. The document workspace mirrors the full vendor management lifecycle:

```
NDA signed             Vendors submit         Company establishes     Individual contracts
before discussions     proposals              master framework        signed per vendor
      │                     │                       │                       │
      ▼                     ▼                       ▼                       ▼
 ┌─────────┐         ┌───────────┐           ┌───────────┐           ┌───────────┐
 │  NDAs   │────────▶│ Proposals │──────────▶│    MSA    │──────────▶│ Contracts │
 └─────────┘         └───────────┘           └───────────┘           └───────────┘
   2 files             4 files                 1 file                  4 files
   12 KB               242 KB                  9 KB                   182 KB
                                                                          │
                            ┌─────────────────────────────────────────────┤
                            │                                             │
                            ▼                                             ▼
                     ┌───────────┐    Internal policies              ┌───────────┐
                     │Amendments │    govern all vendors             │Assessments│
                     └───────────┘           │                       └───────────┘
                       4 files               ▼                         4 files
                       19 KB          ┌───────────┐                    16 KB
                                      │ Policies  │                      │
                                      └───────────┘                      │
                                        2 files                          ▼
                                        13 KB                    ┌───────────────┐
                                                                 │ Board Minutes │
                                                                 └───────────────┘
                                                                     1 file, 8 KB
                                                          Board reviews vendor performance
                                                          and approves renewal strategy
```

Each stage produces documents that reference earlier ones: proposals respond to requirements, contracts incorporate MSA terms, amendments modify contracts, assessments measure contract SLAs, and board minutes summarize assessment findings. This creates natural cross-document content overlap.

| Documents | Files | Size | Role in Lifecycle |
|-----------|-------|------|-------------------|
| NDAs | 2 | 12 KB | Signed first — protects confidential information during vendor evaluation |
| Vendor Proposals | 4 | 242 KB | Vendors respond to RFP with methodology, team, pricing, references |
| Master Service Agreement | 1 | 9 KB | Framework terms all vendor contracts inherit |
| Service Agreements | 4 | 182 KB | Per-vendor contracts with shared legal template (Articles 1-16) |
| Amendments | 4 | 19 KB | Modifications to contracts (scope, SLA, sustainability) |
| Vendor Assessments | 4 | 16 KB | Annual performance reviews measuring contract SLA compliance |
| Internal Policies | 2 | 13 KB | Information Security and Data Governance policies vendors must follow |
| Board Minutes | 1 | 8 KB | Board reviews vendor performance and approves renewal strategy |

The 60 document tasks cover every stage — from comparing proposals during vendor selection, to reviewing contracts for legal risk, to auditing compliance against internal policies, to preparing board briefings on vendor performance.

The 10 coding tasks simulate iterative code modification: the agent reads a 290-line Python service (`user_service.py`), then adds features across 3 turns, printing the complete updated file each time. Each turn's output is ~90% identical to the previous — only the new feature differs.

## Workload Profile

| Property | Value |
|----------|-------|
| Avg input tokens (all turns) | ~46K |
| Max input tokens | ~93K |
| Avg output tokens | ~760 |
| Input/output ratio | ~60:1 |
| Content overlap (contracts) | ~70% |
| Content overlap (proposals) | ~66% |

## Benchmark Results

SGLang 0.5.9, Qwen3-4B-Instruct-2507, 1× NVIDIA RTX PRO 6000 Blackwell, ContextPilot stateful proxy.

### Document Analysis (60 tasks, 245 turns)

|  | Avg | P50 | P99 |
|---|---|---|---|
| **Prompt Tokens Δ** | -24.4% | -15.7% | -52.7% |
| **Wall Time Δ** | -20.7% | -7.0% | -41.2% |
| **Prefill Δ** | **-63.6%** | -16.5% | **-73.7%** |
| **Accuracy** | 245/245 (100%) | — | — |

### Coding (10 tasks, Turn 3, 8 valid scenarios)

|  | Avg |
|---|---|
| **Prompt Tokens Δ** | -16.2% |
| **Wall Time Δ** | -12.4% |
| **Prefill Δ** | **-62.2%** |
| **Accuracy** | 8/8 OK |

## File Structure

```
├── README.md
├── data/
│   ├── README.md               # Data sources, construction notes, licensing
│   └── workspace/              # 22 enterprise documents (490 KB)
├── claw-tasks/
│   ├── README.md               # Per-task details with documents used
│   ├── commercial/tasks.json   # 10 tasks
│   ├── legal/tasks.json        # 12 tasks
│   ├── compliance/tasks.json   # 18 tasks
│   ├── strategic/tasks.json    # 20 tasks
│   └── coding/tasks.json      # 10 tasks
├── scripts/
│   ├── run_bench.py            # Main benchmark runner
│   ├── run_coding_sglang.py    # Coding-specific runner for SGLang
│   └── analyze.py
└── results/                    # Generated by run_bench.py
```

## License

Apache 2.0
