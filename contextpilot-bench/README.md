# ContextPilot Block-Dedup Benchmark

End-to-end benchmark measuring ContextPilot's block-level deduplication on OpenClaw agent workloads with SGLang.

## What it is

This benchmark simulates a realistic enterprise document review workload. A company (TechVentures Pte Ltd) has 4 vendor contracts for cloud, AI, security, and data services. Each contract is approximately 45KB and shares a common template (Articles 1-16, Schedules A-B) with vendor-specific terms (Article 17, headers, payment).

The benchmark runs 30 distinct contract-review scenarios, covering 122 total turns. These scenarios include commercial comparisons, liability reviews, data protection audits, and more.

## Why this is realistic

- **Enterprise Use Case**: Document review is a primary use case for local LLM agents in corporate environments.
- **Template Ubiquity**: Legal contracts are almost always based on standardized boilerplate templates.
- **Prefill-Heavy**: Multi-turn analysis of large documents involves significant prefill tokens.
- **Local Deployment**: Using SGLang and ContextPilot locally is essential for sensitive documents.

## Why SGLang Radix Cache alone can't help

Radix Cache only matches prefixes. In an agent workflow, shared template content often appears at different positions in the message array (after different system prompts or tool result headers) and not as a shared prefix.

ContextPilot's block-level deduplication identifies identical blocks across different tool results and replaces them with pointers, significantly reducing the total prefill tokens regardless of their position.

## How block-dedup works

1. **Content-Defined Chunking**: Tool results are split into blocks using content-based boundaries (determined by line hashes).
2. **SHA-256 Hashing**: Each block is hashed to identify identical content.
3. **Pointer Replacement**: The first occurrence of a block is preserved; subsequent identical blocks across different tool results are replaced with `[... identical block — see block N in earlier result ...]`.
4. **Attention Resolution**: The LLM resolves these pointers via attention to the original content preserved earlier in the context.

## Results Table

Dataset: 30 contract-review scenarios, 4 docs × ~45KB (182KB total), 122 turns/arm
Model: Qwen3-4B-Instruct-2507 · Engine: SGLang 0.5.9 · GPU: RTX PRO 6000 Blackwell

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

## File Structure

```text
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

## Quick Start

```bash
# 1. Generate contract data
python scripts/gen_data.py

# 2. Start SGLang
CUDA_VISIBLE_DEVICES=0 python -m sglang.launch_server \
  --model-path Qwen/Qwen3-4B-Instruct-2507 \
  --port 30002 --host 0.0.0.0 --tp-size 1 \
  --context-length 131072 --tool-call-parser hermes

# 3. Start ContextPilot (in another terminal)
python -m contextpilot.server.http_server \
  --port 8771 --infer-api-url http://localhost:30002

# 4. Run benchmark
python scripts/run_bench.py

# 5. Analyze results
python scripts/analyze.py results/results.jsonl
```
