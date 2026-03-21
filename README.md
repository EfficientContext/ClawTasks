# ClawBench

Benchmark for evaluating LLM inference optimizations on [OpenClaw](https://openclaw.ai) agent workloads.

## Contract Review Benchmark

An enterprise contract review workload: 18 private documents (260 KB), 30 multi-turn analysis tasks, 122 turns total.

See [`contextpilot-bench/README.md`](contextpilot-bench/README.md) for full details.

### Quick Start

```bash
# Run benchmark
python contextpilot-bench/scripts/run_bench.py --gpu 0

# Analyze results
python contextpilot-bench/scripts/analyze.py contextpilot-bench/results/results.jsonl
```

### Results (ContextPilot)

```
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

Accuracy
  OpenClaw + SGLang                      122/122 (100.0%)
  OpenClaw + ContextPilot + SGLang       122/122 (100.0%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## License

Apache 2.0
