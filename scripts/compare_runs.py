#!/usr/bin/env python3
"""Compare two benchmark runs side-by-side (e.g. ContextPilot vs baseline).

Shows per-turn prefill (TTFT) and end-to-end (elapsed) latency comparison.

Usage:
    python scripts/compare_runs.py results/run_A.json results/run_B.json
    python scripts/compare_runs.py results/run_A.json results/run_B.json --topic paper-transformer
"""

import argparse
import json
import pathlib
import sys


def load_run(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def _fmt_ms(val):
    if val is None:
        return "n/a"
    return f"{val:.0f}ms"


def _fmt_s(val):
    if val is None:
        return "n/a"
    return f"{val:.1f}s"


def _speedup(a, b):
    """Speedup of A over B (>1 means A is faster)."""
    if a is None or b is None or a <= 0:
        return None
    return b / a


def _fmt_speedup(val):
    if val is None:
        return ""
    return f"{val:.2f}x"


def compare(run_a: dict, run_b: dict, label_a: str, label_b: str,
            topic_filter: str | None = None):
    results_a = {r["task_name"]: r for r in run_a["results"]}
    results_b = {r["task_name"]: r for r in run_b["results"]}

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
    print(f"\n{'='*100}")
    print(f"Run Comparison")
    print(f"  A: {label_a}")
    print(f"  B: {label_b}")
    print(f"{'='*100}")

    all_prefill_a = []
    all_prefill_b = []
    all_e2e_a = []
    all_e2e_b = []

    for topic in sorted(topics):
        task_names = topics[topic]

        print(f"\n{'─'*100}")
        print(f"  Topic: {topic} ({len(task_names)} turns)")
        print(f"{'─'*100}")

        # Table header
        print(f"  {'Turn':<5} {'Task':<28}"
              f" {'A prefill':>9} {'B prefill':>9} {'Speedup':>8}"
              f" │ {'A e2e':>8} {'B e2e':>8} {'Speedup':>8}")
        print(f"  {'─'*4:<5} {'─'*26:<28}"
              f" {'─'*8:>9} {'─'*8:>9} {'─'*6:>8}"
              f" │ {'─'*7:>8} {'─'*7:>8} {'─'*6:>8}")

        topic_prefill_a = []
        topic_prefill_b = []
        topic_e2e_a = []
        topic_e2e_b = []

        for name in task_names:
            ra = results_a[name]
            rb = results_b[name]
            pos = ra.get("chain_position", 1)

            # Prefill = TTFT (proxy-measured)
            pa = ra.get("proxy_ttft_first_ms")
            pb = rb.get("proxy_ttft_first_ms")
            if pa is not None:
                topic_prefill_a.append(pa)
                all_prefill_a.append(pa)
            if pb is not None:
                topic_prefill_b.append(pb)
                all_prefill_b.append(pb)

            # E2E = elapsed time
            ea = ra.get("elapsed_seconds")
            eb = rb.get("elapsed_seconds")
            if ea is not None:
                topic_e2e_a.append(ea)
                all_e2e_a.append(ea)
            if eb is not None:
                topic_e2e_b.append(eb)
                all_e2e_b.append(eb)

            prefill_sp = _speedup(pa, pb)
            e2e_sp = _speedup(ea, eb)

            short_name = name.replace(f"{topic}-", "")
            status_a = "OK" if ra.get("success") else "FAIL"
            status_b = "OK" if rb.get("success") else "FAIL"
            if status_a != "OK" or status_b != "OK":
                short_name += f" [{status_a}/{status_b}]"

            print(f"  {pos:<5} {short_name:<28}"
                  f" {_fmt_ms(pa):>9} {_fmt_ms(pb):>9} {_fmt_speedup(prefill_sp):>8}"
                  f" │ {_fmt_s(ea):>8} {_fmt_s(eb):>8} {_fmt_speedup(e2e_sp):>8}")

        # Topic summary
        print(f"  {'─'*4:<5} {'─'*26:<28}"
              f" {'─'*8:>9} {'─'*8:>9} {'─'*6:>8}"
              f" │ {'─'*7:>8} {'─'*7:>8} {'─'*6:>8}")

        avg_pa = sum(topic_prefill_a) / len(topic_prefill_a) if topic_prefill_a else None
        avg_pb = sum(topic_prefill_b) / len(topic_prefill_b) if topic_prefill_b else None
        avg_ea = sum(topic_e2e_a) / len(topic_e2e_a) if topic_e2e_a else None
        avg_eb = sum(topic_e2e_b) / len(topic_e2e_b) if topic_e2e_b else None

        print(f"  {'Avg':<5} {'':<28}"
              f" {_fmt_ms(avg_pa):>9} {_fmt_ms(avg_pb):>9} {_fmt_speedup(_speedup(avg_pa, avg_pb)):>8}"
              f" │ {_fmt_s(avg_ea):>8} {_fmt_s(avg_eb):>8} {_fmt_speedup(_speedup(avg_ea, avg_eb)):>8}")

        # Show prefill trend if data exists
        if topic_prefill_a and len(topic_prefill_a) >= 3:
            first = topic_prefill_a[0]
            last = topic_prefill_a[-1]
            trend = ((last - first) / first) * 100 if first > 0 else 0
            direction = "↓" if trend < 0 else "↑"
            print(f"        {'A prefill trend:':<28}"
                  f" turn 1: {_fmt_ms(first):<8} → turn {len(topic_prefill_a)}: {_fmt_ms(last):<8}"
                  f" ({direction}{abs(trend):.0f}%)")
        if topic_prefill_b and len(topic_prefill_b) >= 3:
            first = topic_prefill_b[0]
            last = topic_prefill_b[-1]
            trend = ((last - first) / first) * 100 if first > 0 else 0
            direction = "↓" if trend < 0 else "↑"
            print(f"        {'B prefill trend:':<28}"
                  f" turn 1: {_fmt_ms(first):<8} → turn {len(topic_prefill_b)}: {_fmt_ms(last):<8}"
                  f" ({direction}{abs(trend):.0f}%)")

    # Overall summary
    print(f"\n{'='*100}")
    print(f"Overall Summary ({len(common)} tasks)")
    print(f"{'='*100}")

    print(f"\n  {'Metric':<30} {'A':>12} {'B':>12} {'Speedup':>10}")
    print(f"  {'─'*28:<30} {'─'*10:>12} {'─'*10:>12} {'─'*8:>10}")

    # Prefill summary
    if all_prefill_a or all_prefill_b:
        avg_pa = sum(all_prefill_a) / len(all_prefill_a) if all_prefill_a else None
        avg_pb = sum(all_prefill_b) / len(all_prefill_b) if all_prefill_b else None
        sp = _speedup(avg_pa, avg_pb)
        print(f"  {'Avg prefill (TTFT)':<30} {_fmt_ms(avg_pa):>12} {_fmt_ms(avg_pb):>12} {_fmt_speedup(sp):>10}")

        if all_prefill_a:
            p50a = sorted(all_prefill_a)[len(all_prefill_a) // 2]
            print(f"  {'P50 prefill (A)':<30} {_fmt_ms(p50a):>12}")
        if all_prefill_b:
            p50b = sorted(all_prefill_b)[len(all_prefill_b) // 2]
            print(f"  {'P50 prefill (B)':<30} {'':>12} {_fmt_ms(p50b):>12}")

    # E2E summary
    avg_ea = sum(all_e2e_a) / len(all_e2e_a) if all_e2e_a else None
    avg_eb = sum(all_e2e_b) / len(all_e2e_b) if all_e2e_b else None
    total_ea = sum(all_e2e_a) if all_e2e_a else None
    total_eb = sum(all_e2e_b) if all_e2e_b else None

    sp = _speedup(avg_ea, avg_eb)
    print(f"  {'Avg e2e latency':<30} {_fmt_s(avg_ea):>12} {_fmt_s(avg_eb):>12} {_fmt_speedup(sp):>10}")
    sp = _speedup(total_ea, total_eb)
    print(f"  {'Total e2e time':<30} {_fmt_s(total_ea):>12} {_fmt_s(total_eb):>12} {_fmt_speedup(sp):>10}")

    # Pass rate
    passed_a = sum(1 for n in common if results_a[n].get("success"))
    passed_b = sum(1 for n in common if results_b[n].get("success"))
    print(f"  {'Tasks passed':<30} {passed_a:>12} {passed_b:>12}")

    print(f"{'='*100}\n")


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
