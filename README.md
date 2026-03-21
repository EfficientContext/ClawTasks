# ClawBench

Benchmarks for evaluating LLM inference optimizations on [OpenClaw](https://openclaw.ai) agent workloads.

## Contract Review

Enterprise contract review: 18 private documents (260 KB), 30 multi-turn analysis tasks, 122 turns. Prefill-heavy, decode-light. Documents share ~70% template content.

See [`contract-review/`](contract-review/) for scenario details, task descriptions, and usage.

```bash
python contract-review/scripts/run_bench.py --gpu 0
python contract-review/scripts/analyze.py contract-review/results/results.jsonl
```

## License

Apache 2.0
