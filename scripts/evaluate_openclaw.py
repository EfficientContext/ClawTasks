#!/usr/bin/env python3
"""
LLM-as-judge evaluation for OpenClaw benchmark tasks.

Scores model outputs against ground truth reference answers using an LLM judge.

Scoring dimensions:
  - Factual accuracy (0-5): Does the output contain the key facts?
  - Completeness (0-5): Does it cover the main points from the reference?
  - Conciseness (pass/fail): Is it within the word limit?
  - Composite score: (accuracy + completeness) / 10, with conciseness penalty

Usage:
    # Evaluate a results file against tasks with ground truth
    python scripts/evaluate_openclaw.py results/run_20260317_001457.json \
        --tasks-file openclaw_tasks_all.json

    # Evaluate with a specific model (Anthropic or OpenAI)
    python scripts/evaluate_openclaw.py results/run_20260317_001457.json \
        --tasks-file openclaw_tasks_all.json --model gpt-5.4-mini
"""

import argparse
import json
import os
import pathlib
import sys
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _is_openai_model(model: str) -> bool:
    """Check if a model name is an OpenAI model (not Anthropic)."""
    return not model.startswith("claude")


def _call_llm(prompt: str, system: str, model: str = "claude-3-5-haiku-20241022") -> str:
    """Call the LLM API for judge evaluation. Auto-detects provider from model name."""
    if _is_openai_model(model):
        return _call_openai(prompt, system, model)
    return _call_anthropic(prompt, system, model)


def _call_anthropic(prompt: str, system: str, model: str) -> str:
    """Call the Anthropic API for LLM-as-judge evaluation."""
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _call_openai(prompt: str, system: str, model: str) -> str:
    """Call the OpenAI API for LLM-as-judge evaluation."""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("openai package not installed. Run: pip install openai")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    response = client.chat.completions.create(
        model=model,
        max_tokens=300,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


JUDGE_SYSTEM = """You are an evaluation judge for a benchmark. You score model outputs against reference answers.

You MUST respond with ONLY a JSON object (no markdown, no explanation) with these fields:
{
  "factual_accuracy": <0-5 integer>,
  "completeness": <0-5 integer>,
  "reasoning": "<1-2 sentence explanation>"
}

Scoring guide:
- factual_accuracy (0-5): How many key facts from the reference are present in the output?
  0 = no correct facts, 1 = one fact correct, 2-3 = some facts, 4 = most facts, 5 = all key facts
- completeness (0-5): How well does the output cover the main points?
  0 = completely off-topic, 1 = barely relevant, 2-3 = partial coverage, 4 = good coverage, 5 = comprehensive

Be lenient with paraphrasing. The same fact expressed differently should count.
Numbers don't need to match exactly if they're in the right ballpark."""


def judge_single(output: str, reference_answer: str, key_facts: list[str],
                 task_description: str, model: str = "claude-3-5-haiku-20241022") -> dict:
    """Use LLM-as-judge to score a single output against reference."""
    facts_str = "\n".join(f"  - {f}" for f in key_facts)
    prompt = f"""## Task
{task_description}

## Reference Answer
{reference_answer}

## Key Facts (must be present for full accuracy score)
{facts_str}

## Model Output to Evaluate
{output}

Score the model output. Respond with ONLY a JSON object."""

    raw = _call_llm(prompt, JUDGE_SYSTEM, model)

    # Parse JSON from response (handle potential markdown wrapping)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [WARN] Failed to parse judge response: {raw[:200]}")
        scores = {"factual_accuracy": 0, "completeness": 0, "reasoning": "parse_error"}

    return scores


def score_conciseness(output: str, max_tokens: int) -> bool:
    """Check if output is within the word limit. Simple word count."""
    word_count = len(output.split())
    # Allow ~30% margin since token != word and the model might count differently
    return word_count <= max_tokens * 1.3


def evaluate_single_task(result: dict, task: dict, model: str = "claude-3-5-haiku-20241022") -> dict:
    """Evaluate a single task result against its ground truth."""
    gt = task.get("ground_truth")
    if not gt:
        return {"skipped": True, "reason": "no_ground_truth"}

    output = result.get("stdout", "").strip()
    if not output:
        return {
            "factual_accuracy": 0,
            "completeness": 0,
            "conciseness": False,
            "composite_score": 0.0,
            "reasoning": "empty_output",
        }

    # LLM judge for accuracy and completeness
    judge_scores = judge_single(
        output=output,
        reference_answer=gt["reference_answer"],
        key_facts=gt["key_facts"],
        task_description=task["description"],
        model=model,
    )

    accuracy = judge_scores.get("factual_accuracy", 0)
    completeness = judge_scores.get("completeness", 0)

    # Programmatic conciseness check
    max_tokens = gt.get("max_expected_tokens", 150)
    concise = score_conciseness(output, max_tokens)

    # Composite: (accuracy + completeness) / 10, penalize verbose outputs
    base_score = (accuracy + completeness) / 10.0
    composite = base_score * (1.0 if concise else 0.8)  # 20% penalty for verbose

    return {
        "factual_accuracy": accuracy,
        "completeness": completeness,
        "conciseness": concise,
        "composite_score": round(composite, 3),
        "reasoning": judge_scores.get("reasoning", ""),
        "word_count": len(output.split()),
        "max_expected_tokens": max_tokens,
    }


def evaluate_results(results: list[dict], task_map: dict[str, dict],
                     results_dir: pathlib.Path = None,
                     model: str = "claude-3-5-haiku-20241022") -> list[dict]:
    """Evaluate all results against ground truth using LLM-as-judge.

    Args:
        results: List of result dicts from run_bench
        task_map: Dict mapping task name -> task dict (with ground_truth)
        results_dir: Optional directory to save per-task eval results
        model: Model to use for judging (auto-detects Anthropic vs OpenAI from name)
    """
    evals = []
    tasks_with_gt = 0
    total_composite = 0.0
    total_accuracy = 0
    total_completeness = 0
    concise_count = 0

    print(f"\n{'='*60}")
    print("LLM-as-Judge Evaluation")
    print(f"{'='*60}\n")

    for result in results:
        task_name = result.get("task_name", "")
        task = task_map.get(task_name)

        if not task or not task.get("ground_truth"):
            print(f"  [{task_name}] SKIP (no ground truth)")
            evals.append({"task_name": task_name, "skipped": True})
            continue

        if not result.get("success"):
            print(f"  [{task_name}] SKIP (task failed)")
            evals.append({"task_name": task_name, "skipped": True, "reason": "task_failed"})
            continue

        print(f"  [{task_name}] Judging...", end=" ", flush=True)
        eval_result = evaluate_single_task(result, task, model)
        eval_result["task_name"] = task_name
        eval_result["topic"] = result.get("topic", "")
        eval_result["chain_position"] = result.get("chain_position", 1)
        evals.append(eval_result)

        if not eval_result.get("skipped"):
            tasks_with_gt += 1
            total_composite += eval_result["composite_score"]
            total_accuracy += eval_result["factual_accuracy"]
            total_completeness += eval_result["completeness"]
            if eval_result["conciseness"]:
                concise_count += 1

        score_str = f"acc={eval_result['factual_accuracy']}/5 " \
                    f"comp={eval_result['completeness']}/5 " \
                    f"concise={'Y' if eval_result['conciseness'] else 'N'} " \
                    f"composite={eval_result['composite_score']:.2f}"
        print(score_str)

    # Summary
    if tasks_with_gt > 0:
        print(f"\n{'─'*60}")
        print(f"Evaluation Summary ({tasks_with_gt} tasks with ground truth):")
        print(f"  Avg composite score: {total_composite / tasks_with_gt:.3f}")
        print(f"  Avg factual accuracy: {total_accuracy / tasks_with_gt:.2f}/5")
        print(f"  Avg completeness: {total_completeness / tasks_with_gt:.2f}/5")
        print(f"  Conciseness rate: {concise_count}/{tasks_with_gt} "
              f"({100 * concise_count / tasks_with_gt:.0f}%)")
        print(f"{'─'*60}")

    # Save eval results alongside run results
    if results_dir:
        results_dir.mkdir(exist_ok=True)
        from datetime import datetime, timezone
        eval_file = results_dir / f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        eval_data = {
            "model": model,
            "tasks_evaluated": tasks_with_gt,
            "summary": {
                "avg_composite": round(total_composite / tasks_with_gt, 3) if tasks_with_gt else 0,
                "avg_accuracy": round(total_accuracy / tasks_with_gt, 2) if tasks_with_gt else 0,
                "avg_completeness": round(total_completeness / tasks_with_gt, 2) if tasks_with_gt else 0,
                "conciseness_rate": round(concise_count / tasks_with_gt, 3) if tasks_with_gt else 0,
            },
            "evaluations": evals,
        }
        eval_file.write_text(json.dumps(eval_data, indent=2))
        print(f"\nEval output: {eval_file}")

    return evals


def evaluate_results_file(results_path: pathlib.Path, tasks_path: pathlib.Path,
                          model: str = "claude-3-5-haiku-20241022"):
    """Evaluate a results JSON file against tasks with ground truth."""
    results_data = json.loads(results_path.read_text())
    results = results_data.get("results", [])
    if not results:
        sys.exit(f"No results found in {results_path}")

    tasks = json.loads(tasks_path.read_text())
    task_map = {t["name"]: t for t in tasks}

    evaluate_results(results, task_map, results_path.parent, model)


def main():
    parser = argparse.ArgumentParser(description="LLM-as-judge evaluation for OpenClaw benchmark")
    parser.add_argument("results_file", type=str,
                       help="Path to results JSON file")
    parser.add_argument("--tasks-file", type=str,
                       default=str(ROOT / "openclaw_tasks_all.json"),
                       help="Path to tasks JSON with ground truth")
    parser.add_argument("--model", type=str,
                       default="claude-3-5-haiku-20241022",
                       help="Model for judging (auto-detects provider: claude-* → Anthropic, else → OpenAI)")
    args = parser.parse_args()

    evaluate_results_file(
        pathlib.Path(args.results_file),
        pathlib.Path(args.tasks_file),
        args.model,
    )


if __name__ == "__main__":
    main()
