#!/usr/bin/env python3
"""
ContextPilot Block-Dedup Benchmark Runner
=========================================
Standalone runner for the ContextPilot block-dedup benchmark.
Manages SGLang and ContextPilot lifecycles and runs OpenClaw agent tasks.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import requests

# Default Configuration
MODEL = "Qwen/Qwen3-4B-Instruct-2507"
PORT_SGLANG = 30002
PORT_CP = 8771
GPU_ID = "0"

# Paths
OPENCLAW_PATH = os.path.expanduser("~/openclaw/openclaw.mjs")
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
RESULTS_DIR = Path(__file__).parent.parent / "results"
SGLANG_LOG = "/tmp/sglang_bench.log"
CP_LOG = "/tmp/cp_bench.log"

_NO_WEB = "Do not search the web — only analyze the contract text."

SCENARIOS = [
    {
        "name": "s01_commercial_terms",
        "turns": [
            "List all files in the contracts/ folder.",
            f"Read contracts/contract_alpha_cloud.txt and summarize: parties, total amount, duration, payment schedule, and service scope. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt and compare its commercial terms with Alpha. What is identical vs different? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. How do the payment terms compare across all three? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Create a comparison table of all four contracts: value, duration, payment structure, SLA targets. {_NO_WEB}",
        ],
    },
    {
        "name": "s02_liability_review",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract all liability and indemnification clauses. Quote the text. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are the liability caps and exclusions identical to Alpha? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Rank all four by liability exposure. {_NO_WEB}",
            f"Write a risk assessment memo on liability gaps and recommended amendments. {_NO_WEB}",
        ],
    },
    {
        "name": "s03_data_protection",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and evaluate its data protection clauses. List any gaps. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. How do its privacy terms compare with Alpha? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Assess its breach notification and incident response terms. {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Review the data retention provisions. {_NO_WEB}",
            f"Produce a data protection compliance scorecard for all four contracts. {_NO_WEB}",
        ],
    },
    {
        "name": "s04_ip_ownership",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and summarize the IP ownership and assignment clauses. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are the IP terms different given it involves AI/ML work? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare IP clauses across all four. {_NO_WEB}",
            f"Are there any gaps in IP protection that could expose our company? Write recommendations. {_NO_WEB}",
        ],
    },
    {
        "name": "s05_termination_rights",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. What are the termination rights for both parties? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Compare its termination clauses with Alpha. {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Are there any termination-for-cause triggers unique to the security contract? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Create a summary of termination rights across all four contracts with notice periods and consequences. {_NO_WEB}",
        ],
    },
    {
        "name": "s06_sla_comparison",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract all SLA targets: uptime, response times, resolution times. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Does it have the same SLA structure? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. What SLA commitments are specific to security operations? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare SLA targets across all four and identify which vendor has the weakest commitments. {_NO_WEB}",
        ],
    },
    {
        "name": "s07_insurance_audit",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract the insurance requirements. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are the insurance requirements identical? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Does the security vendor have higher cyber insurance requirements? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Summarize insurance requirements across all four and flag any inadequacies. {_NO_WEB}",
        ],
    },
    {
        "name": "s08_dispute_resolution",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and outline the dispute resolution process step by step. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Is the dispute mechanism the same? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Are there any differences in arbitration or governing law? {_NO_WEB}",
            f"Write a memo summarizing the dispute resolution framework across all four contracts. {_NO_WEB}",
        ],
    },
    {
        "name": "s09_change_management",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and describe the change management process. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. How flexible are the change order terms for AI projects? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Are emergency changes handled differently in the security contract? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare change management across all four. {_NO_WEB}",
        ],
    },
    {
        "name": "s10_subcontracting",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract subcontracting restrictions. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are subcontracting terms different for AI development? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Are there heightened subcontracting controls for security? {_NO_WEB}",
            f"Summarize subcontracting risks across all four vendors. {_NO_WEB}",
        ],
    },
    {
        "name": "s11_warranty_terms",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and list all warranties and their durations. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are the warranty terms adequate for an AI platform? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. What warranties does the security vendor provide? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare warranty coverage across all four and identify weak spots. {_NO_WEB}",
        ],
    },
    {
        "name": "s12_confidentiality",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and analyze the confidentiality obligations. How long do they survive? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are there any differences in confidentiality scope? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare confidentiality terms. {_NO_WEB}",
            f"Are there any gaps in confidentiality protection? Write a recommendation. {_NO_WEB}",
        ],
    },
    {
        "name": "s13_payment_risk",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and analyze payment risk: late payment penalties, audit rights, service credits. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What performance bonuses or penalties exist? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. How are incident response fees structured? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare financial risk across all four contracts. {_NO_WEB}",
        ],
    },
    {
        "name": "s14_force_majeure",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract the force majeure clause. What events are covered? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Is the force majeure definition the same? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Are cyberattacks included in force majeure? {_NO_WEB}",
            f"Write a summary of force majeure coverage across all four and recommend improvements. {_NO_WEB}",
        ],
    },
    {
        "name": "s15_bcp_dr",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and evaluate the business continuity and disaster recovery requirements. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are there BCP/DR requirements for the AI platform? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. What RTOs are specified for the security SOC? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare BCP/DR across all four. {_NO_WEB}",
        ],
    },
    {
        "name": "s16_personnel_reqs",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and list personnel qualification requirements. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What certifications are required for AI personnel? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. What certifications are required for SOC analysts? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare personnel requirements across all four. {_NO_WEB}",
        ],
    },
    {
        "name": "s17_acceptance_testing",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and describe the acceptance testing process. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. How are AI model deliverables accepted? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare acceptance criteria. {_NO_WEB}",
            f"Are the acceptance testing timelines reasonable? Recommend improvements. {_NO_WEB}",
        ],
    },
    {
        "name": "s18_renewal_analysis",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. When does it expire and what are the renewal terms? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Compare its term with Alpha. {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. What is its duration? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Create a renewal timeline for all four with key dates. {_NO_WEB}",
        ],
    },
    {
        "name": "s19_compliance_scorecard",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. Evaluate its regulatory compliance provisions. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Assess AI governance and data provenance safeguards. {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Check incident response and vulnerability management. {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Review data quality and retention. {_NO_WEB}",
            f"Produce a compliance scorecard rating each contract on 5 dimensions. {_NO_WEB}",
        ],
    },
    {
        "name": "s20_vendor_comparison",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and contracts/contract_beta_ai.txt. Compare these two vendors side by side. {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare these two vendors. {_NO_WEB}",
            f"Which vendor has the most favorable terms for our company? Rank all four. {_NO_WEB}",
            f"Which vendor poses the highest risk? Explain with specific clause references. {_NO_WEB}",
        ],
    },
    {
        "name": "s21_cost_analysis",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. What is the total cost including potential penalties and bonuses? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What is the maximum financial exposure including performance bonuses? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Calculate total financial commitments. {_NO_WEB}",
            f"What is our total vendor spend across all four contracts? Provide a cost breakdown. {_NO_WEB}",
        ],
    },
    {
        "name": "s22_audit_rights",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract all audit rights. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What audit provisions exist for AI model governance? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. Are there audit rights specific to security operations? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare audit rights across all four. Are they adequate? {_NO_WEB}",
        ],
    },
    {
        "name": "s23_knowledge_transfer",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and review the knowledge transfer and transition provisions. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are AI model handover procedures adequate? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. What transition support is guaranteed? {_NO_WEB}",
            f"Write a transition readiness assessment for all four vendors. {_NO_WEB}",
        ],
    },
    {
        "name": "s24_security_assessment",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and evaluate all security-related provisions. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are there adequate security controls for AI training data? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. This is the security vendor — are their own security terms comprehensive? {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare security posture across all four vendors. {_NO_WEB}",
        ],
    },
    {
        "name": "s25_exit_strategy",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. What happens if we need to exit this contract? Describe the process. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What are the exit costs and data retrieval provisions? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare exit provisions. {_NO_WEB}",
            f"Develop an exit strategy plan covering all four vendors with timeline and cost estimates. {_NO_WEB}",
        ],
    },
    {
        "name": "s26_open_source",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and check for open-source software provisions. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What are the open-source disclosure requirements for AI models? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Are there software bill of materials requirements? {_NO_WEB}",
            f"Summarize open-source risk across all four vendors. {_NO_WEB}",
        ],
    },
    {
        "name": "s27_cross_border",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt. What are the data sovereignty and cross-border transfer provisions? {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. Are there restrictions on where AI training happens? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Compare cross-border data provisions. {_NO_WEB}",
            f"Are we compliant with Singapore PDPA cross-border requirements across all four contracts? {_NO_WEB}",
        ],
    },
    {
        "name": "s28_breach_response",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and extract data breach notification timelines and procedures. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What are the breach notification obligations? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt. The security vendor should have the most detailed breach response — verify this. {_NO_WEB}",
            f"Read contracts/contract_delta_data.txt. Compare breach response across all four and identify gaps. {_NO_WEB}",
        ],
    },
    {
        "name": "s29_board_summary",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and contracts/contract_beta_ai.txt. Prepare a board-level summary of these two contracts. {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Prepare the same for these two. {_NO_WEB}",
            f"Write a one-page executive summary of all four vendor contracts suitable for the board of directors. {_NO_WEB}",
        ],
    },
    {
        "name": "s30_negotiation_prep",
        "turns": [
            f"Read contracts/contract_alpha_cloud.txt and identify the top 3 clauses we should renegotiate. {_NO_WEB}",
            f"Read contracts/contract_beta_ai.txt. What terms are most unfavorable to us? {_NO_WEB}",
            f"Read contracts/contract_gamma_security.txt and contracts/contract_delta_data.txt. Identify weak negotiation positions. {_NO_WEB}",
            f"Prepare a negotiation strategy document covering all four contracts with specific amendment proposals. {_NO_WEB}",
        ],
    },
]

_sglang_proc = None
_cp_proc = None

def kill_sglang():
    global _sglang_proc
    if _sglang_proc:
        try: _sglang_proc.kill(); _sglang_proc.wait(timeout=5)
        except: pass
        _sglang_proc = None
    subprocess.run("fuser -k 30002/tcp 2>/dev/null", shell=True, capture_output=True)
    time.sleep(2)

def kill_cp():
    global _cp_proc
    if _cp_proc:
        try: _cp_proc.kill(); _cp_proc.wait(timeout=5)
        except: pass
        _cp_proc = None
    subprocess.run("fuser -k 8771/tcp 2>/dev/null", shell=True, capture_output=True)
    time.sleep(1)

def start_sglang(gpu_id):
    global _sglang_proc
    kill_sglang()
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": gpu_id, "SGLANG_DISABLE_CUDNN_CHECK": "1"}
    cmd = [
        sys.executable, "-m", "sglang.launch_server",
        "--model-path", MODEL,
        "--port", str(PORT_SGLANG),
        "--host", "0.0.0.0",
        "--tp-size", "1",
        "--context-length", "131072",
        "--tool-call-parser", "hermes",
        "--attention-backend", "triton",
        "--skip-server-warmup"
    ]
    print(f"  Starting SGLang on GPU {gpu_id}...")
    log_f = open(SGLANG_LOG, "w")
    _sglang_proc = subprocess.Popen(cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT)
    
    for i in range(180):
        time.sleep(1)
        try:
            with open(SGLANG_LOG) as f:
                content = f.read()
            if "ready to roll" in content:
                print(f"  SGLang ready ({i+1}s)")
                return
        except: pass
    raise RuntimeError("SGLang failed to start")

def start_contextpilot():
    global _cp_proc
    kill_cp()
    cmd = [
        sys.executable, "-m", "contextpilot.server.http_server",
        "--port", str(PORT_CP),
        "--infer-api-url", f"http://localhost:{PORT_SGLANG}"
    ]
    print("  Starting ContextPilot...")
    _cp_proc = subprocess.Popen(cmd, env=os.environ.copy(), stdout=open(CP_LOG, "w"), stderr=subprocess.STDOUT)
    
    for i in range(30):
        time.sleep(1)
        try:
            r = requests.get(f"http://localhost:{PORT_CP}/health", timeout=2)
            if r.status_code in (200, 503):
                print(f"  ContextPilot ready ({i+1}s)")
                return
        except: pass
    raise RuntimeError("ContextPilot failed to start")

def set_openclaw_url(url):
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    cfg["models"]["providers"]["sglang"]["baseUrl"] = url
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def run_agent_turn(session_id, message):
    cmd = [
        "node", OPENCLAW_PATH, "agent", "--local",
        "--session-id", session_id,
        "--message", message,
        "--json", "--timeout", "180"
    ]
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    
    try:
        json_start = result.stdout.index("{")
        data = json.loads(result.stdout[json_start:])
        meta = data.get("meta", {})
        agent = meta.get("agentMeta", {})
        usage = agent.get("lastCallUsage", agent.get("usage", {}))
        return {
            "wall_s": round(wall, 3),
            "prompt_tokens": usage.get("input", 0),
            "completion_tokens": usage.get("output", 0),
            "output_chars": len(data.get("payloads", [{}])[0].get("text", ""))
        }
    except:
        return {"error": "parse_failed", "wall_s": round(wall, 3), "stdout": result.stdout[:200]}

def run_scenario(scenario, arm_label, base_url, trial, gpu_id):
    session_id = f"bench-{scenario['name']}-{arm_label}-t{trial}-{int(time.time())}"
    set_openclaw_url(base_url)
    start_sglang(gpu_id)
    if arm_label == "CP":
        start_contextpilot()
    
    print(f"\n  [{scenario['name']}] arm={arm_label} trial={trial}")
    results = []
    for i, msg in enumerate(scenario["turns"]):
        print(f"    Turn {i}: ", end="", flush=True)
        r = run_agent_turn(session_id, msg)
        r.update(turn=i, arm=arm_label, trial=trial, name=scenario["name"])
        results.append(r)
        print(f"ptok={r.get('prompt_tokens',0):,} wall={r.get('wall_s',0):.1f}s")
    
    kill_sglang()
    kill_cp()
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--scenarios", nargs="*", default=None)
    args = parser.parse_args()
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []
    
    scenarios = SCENARIOS
    if args.scenarios:
        scenarios = [s for s in SCENARIOS if s["name"] in args.scenarios]

    for trial in range(args.trials):
        for scenario in scenarios:
            for arm, url in [("Direct", f"http://localhost:{PORT_SGLANG}/v1"), ("CP", f"http://localhost:{PORT_CP}/v1")]:
                try:
                    all_results.extend(run_scenario(scenario, arm, url, trial, args.gpu))
                except Exception as e:
                    print(f"Error: {e}")
                    kill_sglang(); kill_cp()

    outfile = RESULTS_DIR / "results.jsonl"
    with open(outfile, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults saved to {outfile}")

if __name__ == "__main__":
    main()
