#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path


def analyze(results_path):
    if not Path(results_path).exists():
        print(f"Error: File not found: {results_path}")
        return

    all_results = []
    with open(results_path, "r") as f:
        for line in f:
            if line.strip():
                all_results.append(json.loads(line))

    if not all_results:
        print("No results found.")
        return

    scenarios = sorted(list(set(r["name"] for r in all_results)))
    arms = sorted(list(set(r["arm"] for r in all_results)))

    print("\n" + "=" * 130)
    print("SUMMARY — Averages across all turns")
    print("=" * 130)
    print(f"{'Arm':<30s} {'PTok (Avg)':>12s} {'Wall (Avg)':>12s} {'CTok (Avg)':>12s}")
    print("-" * 130)

    for arm in arms:
        arm_rows = [r for r in all_results if r["arm"] == arm]
        if not arm_rows:
            continue

        avg_ptok = sum(r.get("prompt_tokens", 0) for r in arm_rows) / len(arm_rows)
        avg_wall = sum(r.get("wall_s", 0) for r in arm_rows) / len(arm_rows)
        avg_ctok = sum(r.get("completion_tokens", 0) for r in arm_rows) / len(arm_rows)

        print(f"{arm:<30s} {avg_ptok:>12.0f} {avg_wall:>11.2f}s {avg_ctok:>12.0f}")

    print("\n" + "=" * 130)
    print("PAPER RESULTS TABLE")
    print("=" * 130)

    # Calculate aggregate stats for Paper Table
    def get_stats(arm_label):
        rows = [r for r in all_results if r["arm"] == arm_label]
        if not rows:
            return None
        ptoks = sorted([r.get("prompt_tokens", 0) for r in rows])
        walls = sorted([r.get("wall_s", 0) for r in rows])
        ctoks = sorted([r.get("completion_tokens", 0) for r in rows])

        def p50(l):
            return l[len(l) // 2]

        def p99(l):
            return l[int(len(l) * 0.99)]

        def avg(l):
            return sum(l) / len(l)

        return {
            "ptok": {"avg": avg(ptoks), "p50": p50(ptoks), "p99": p99(ptoks)},
            "wall": {"avg": avg(walls), "p50": p50(walls), "p99": p99(walls)},
            "ctok": {"avg": avg(ctoks), "p50": p50(ctoks), "p99": p99(ctoks)},
            "count": len(rows),
        }

    direct = get_stats("Direct")
    cp = get_stats("CP")

    if direct and cp:
        print(f"{'':<45s} {'Avg':>10s} {'P50':>10s} {'P99':>10s}")
        print("-" * 80)

        for metric, label in [
            ("ptok", "Prompt Tokens"),
            ("wall", "Wall Time (s)"),
            ("ctok", "Completion Tokens"),
        ]:
            d = direct[metric]
            c = cp[metric]
            print(f"{label}")
            print(
                f"  OpenClaw + SGLang {'':<22s} {d['avg']:>10.1f} {d['p50']:>10.1f} {d['p99']:>10.1f}"
            )
            print(
                f"  OpenClaw + ContextPilot + SGLang {'':<7s} {c['avg']:>10.1f} {c['p50']:>10.1f} {c['p99']:>10.1f}"
            )

            delta_avg = (c["avg"] - d["avg"]) / d["avg"] * 100 if d["avg"] else 0
            delta_p50 = (c["p50"] - d["p50"]) / d["p50"] * 100 if d["p50"] else 0
            delta_p99 = (c["p99"] - d["p99"]) / d["p99"] * 100 if d["p99"] else 0
            print(
                f"  Δ {'':<38s} {delta_avg:>9.1f}% {delta_p50:>9.1f}% {delta_p99:>9.1f}%"
            )
            print()

    # Accuracy check
    if direct and cp:
        d_rows = [r for r in all_results if r["arm"] == "Direct"]
        c_rows = [r for r in all_results if r["arm"] == "CP"]
        d_ok = sum(1 for r in d_rows if r.get("output_chars", 0) >= 50)
        c_ok = sum(1 for r in c_rows if r.get("output_chars", 0) >= 50)
        print(f"Accuracy (substantive output)")
        print(
            f"  OpenClaw + SGLang                        {d_ok}/{len(d_rows)} ({d_ok / len(d_rows) * 100:.1f}%)"
        )
        print(
            f"  OpenClaw + ContextPilot + SGLang          {c_ok}/{len(c_rows)} ({c_ok / len(c_rows) * 100:.1f}%)"
        )
        print()

    print("\nPER-TURN BREAKDOWN")
    print("-" * 130)
    for scenario in scenarios:
        print(f"\nScenario: {scenario}")
        print(
            f"  {'Turn':>4s}  {'PTok_D':>10s} {'PTok_CP':>10s} {'Δ%':>8s}  {'Wall_D':>8s} {'Wall_CP':>8s} {'WΔ%':>8s}"
        )

        s_rows = [r for r in all_results if r["name"] == scenario]
        turns = sorted(list(set(r["turn"] for r in s_rows)))

        for t in turns:
            dr = [r for r in s_rows if r["turn"] == t and r["arm"] == "Direct"]
            cr = [r for r in s_rows if r["turn"] == t and r["arm"] == "CP"]

            if dr and cr:
                dp = sum(r["prompt_tokens"] for r in dr) / len(dr)
                cp_val = sum(r["prompt_tokens"] for r in cr) / len(cr)
                dw = sum(r["wall_s"] for r in dr) / len(dr)
                cw = sum(r["wall_s"] for r in cr) / len(cr)

                pp = (cp_val - dp) / dp * 100 if dp else 0
                wp = (cw - dw) / dw * 100 if dw else 0

                print(
                    f"  {t:>4d}  {dp:>10.0f} {cp_val:>10.0f} {pp:>+7.1f}%  {dw:>7.2f}s {cw:>7.2f}s {wp:>+7.1f}%"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("results_jsonl", help="Path to results.jsonl")
    args = parser.parse_args()
    analyze(args.results_jsonl)
