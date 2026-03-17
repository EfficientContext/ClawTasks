#!/usr/bin/env python3
"""Compare two benchmark runs side-by-side (e.g. ContextPilot vs baseline).

Usage:
    python scripts/compare_runs.py results/run_A.json results/run_B.json
    python scripts/compare_runs.py results/run_A.json results/run_B.json --topic paper-transformer
"""

import argparse
import json
import pathlib
import sys


def load_run(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text())
    return data


def compare(run_a: dict, run_b: dict, label_a: str, label_b: str,
            topic_filter: str | None = None):
    results_a = {r["task_name"]: r for r in run_a["results"]}
    results_b = {r["task_name"]: r for r in run_b["results"]}

    # Find common tasks
    common = sorted(set(results_a) & set(results_b),
                    key=lambda n: (results_a[n].get("topic", ""),
                                  results_a[n].get("chain_position", 1)))

    if topic_filter:
        common = [n for n in common
                  if results_a[n].get("topic", "").startswith(topic_filter)]

    if not common:
        sys.exit("No common tasks found between the two runs.")

    # Group by topic
    topics: dict[str, list[str]] = {}
    for name in common:
        topic = results_a[name].get("topic", "unknown")
        topics.setdefault(topic, []).append(name)

    # Header
    print(f"\n{'='*80}")
    print(f"Run Comparison")
    print(f"  A: {label_a}")
    print(f"  B: {label_b}")
    print(f"{'='*80}")

    overall_a_elapsed = []
    overall_b_elapsed = []
    overall_a_ttft = []
    overall_b_ttft = []

    for topic in sorted(topics):
        task_names = topics[topic]
        print(f"\n{'─'*80}")
        print(f"  Topic: {topic} ({len(task_names)} turns)")
        print(f"{'─'*80}")
        print(f"  {'Turn':<6} {'Task':<35} {'A elapsed':>10} {'B elapsed':>10} {'Speedup':>8}"
              f"  {'A TTFT':>8} {'B TTFT':>8}")
        print(f"  {'─'*4:<6} {'─'*33:<35} {'─'*8:>10} {'─'*8:>10} {'─'*6:>8}"
              f"  {'─'*6:>8} {'─'*6:>8}")

        topic_a_elapsed = []
        topic_b_elapsed = []

        for name in task_names:
            ra = results_a[name]
            rb = results_b[name]
            pos = ra.get("chain_position", 1)

            ea = ra.get("elapsed_seconds", 0)
            eb = rb.get("elapsed_seconds", 0)
            topic_a_elapsed.append(ea)
            topic_b_elapsed.append(eb)
            overall_a_elapsed.append(ea)
            overall_b_elapsed.append(eb)

            speedup = eb / ea if ea > 0 else 0
            speedup_str = f"{speedup:.2f}x" if ea > 0 else "n/a"

            ta = ra.get("proxy_ttft_first_ms")
            tb = rb.get("proxy_ttft_first_ms")
            if ta is not None:
                overall_a_ttft.append(ta)
            if tb is not None:
                overall_b_ttft.append(tb)

            ta_str = f"{ta:.0f}ms" if ta is not None else "n/a"
            tb_str = f"{tb:.0f}ms" if tb is not None else "n/a"

            status_a = "OK" if ra.get("success") else "FAIL"
            status_b = "OK" if rb.get("success") else "FAIL"
            short_name = name.replace(f"{topic}-", "")
            if status_a != "OK" or status_b != "OK":
                short_name += f" [{status_a}/{status_b}]"

            print(f"  {pos:<6} {short_name:<35} {ea:>9.1f}s {eb:>9.1f}s {speedup_str:>8}"
                  f"  {ta_str:>8} {tb_str:>8}")

        # Topic summary
        avg_a = sum(topic_a_elapsed) / len(topic_a_elapsed) if topic_a_elapsed else 0
        avg_b = sum(topic_b_elapsed) / len(topic_b_elapsed) if topic_b_elapsed else 0
        total_a = sum(topic_a_elapsed)
        total_b = sum(topic_b_elapsed)
        topic_speedup = total_b / total_a if total_a > 0 else 0

        print(f"  {'':─<6} {'':─<35} {'':─>10} {'':─>10} {'':─>8}")
        print(f"  {'Avg':<6} {'':<35} {avg_a:>9.1f}s {avg_b:>9.1f}s")
        print(f"  {'Total':<6} {'':<35} {total_a:>9.1f}s {total_b:>9.1f}s {topic_speedup:.2f}x")

    # Overall summary
    print(f"\n{'='*80}")
    print(f"Overall Summary ({len(common)} tasks)")
    print(f"{'='*80}")

    total_a = sum(overall_a_elapsed)
    total_b = sum(overall_b_elapsed)
    avg_a = total_a / len(overall_a_elapsed) if overall_a_elapsed else 0
    avg_b = total_b / len(overall_b_elapsed) if overall_b_elapsed else 0

    print(f"  {'Metric':<30} {'A':>12} {'B':>12} {'Ratio':>8}")
    print(f"  {'─'*28:<30} {'─'*10:>12} {'─'*10:>12} {'─'*6:>8}")

    overall_speedup = total_b / total_a if total_a > 0 else 0
    print(f"  {'Total elapsed':<30} {total_a:>11.1f}s {total_b:>11.1f}s {overall_speedup:>7.2f}x")
    print(f"  {'Avg elapsed/task':<30} {avg_a:>11.1f}s {avg_b:>11.1f}s")

    if overall_a_ttft:
        avg_ttft_a = sum(overall_a_ttft) / len(overall_a_ttft)
        print(f"  {'Avg TTFT (A only)':<30} {avg_ttft_a:>10.0f}ms")
    if overall_b_ttft:
        avg_ttft_b = sum(overall_b_ttft) / len(overall_b_ttft)
        print(f"  {'Avg TTFT (B only)':<30} {'':>12} {avg_ttft_b:>10.0f}ms")

    passed_a = sum(1 for n in common if results_a[n].get("success"))
    passed_b = sum(1 for n in common if results_b[n].get("success"))
    print(f"  {'Tasks passed':<30} {passed_a:>12} {passed_b:>12}")

    # Load eval files if they exist
    for label, run_data, run_label in [(label_a, run_a, "A"), (label_b, run_b, "B")]:
        if "eval_summary" in run_data:
            s = run_data["eval_summary"]
            print(f"\n  Eval ({run_label}): composite={s.get('avg_composite', 0):.3f} "
                  f"accuracy={s.get('avg_accuracy', 0):.2f}/5 "
                  f"completeness={s.get('avg_completeness', 0):.2f}/5")

    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two benchmark runs (e.g. ContextPilot vs baseline)")
    parser.add_argument("run_a", type=str, help="First run (e.g. with ContextPilot)")
    parser.add_argument("run_b", type=str, help="Second run (e.g. baseline)")
    parser.add_argument("--label-a", type=str, default=None, help="Label for run A")
    parser.add_argument("--label-b", type=str, default=None, help="Label for run B")
    parser.add_argument("--topic", type=str, default=None, help="Filter by topic")
    args = parser.parse_args()

    path_a = pathlib.Path(args.run_a)
    path_b = pathlib.Path(args.run_b)

    if not path_a.exists():
        sys.exit(f"File not found: {path_a}")
    if not path_b.exists():
        sys.exit(f"File not found: {path_b}")

    label_a = args.label_a or path_a.stem
    label_b = args.label_b or path_b.stem

    compare(load_run(path_a), load_run(path_b), label_a, label_b, args.topic)


if __name__ == "__main__":
    main()
