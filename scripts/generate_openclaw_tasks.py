#!/usr/bin/env python3
"""
Generate OpenClaw on-device benchmark tasks.

Target: 130 tasks for edge/on-device OpenClaw deployment.
- Long prefill (web search results accumulate), short decode (concise output)
- Only tool: web_search
- Multi-turn chains: 10 tasks per topic, 13 topics
- By turn 10 the context has 9 previous turns of accumulated web search results
- Focus: planning & summarization (paper review, financial analysis, etc.)
- Document overlap: search queries within each chain overlap heavily

Turn flow (deepening investigation):
  1. Overview          — Broad search, 3 bullet summary
  2. Core details      — Key components/methodology
  3. Technical dive    — Specific technical aspect
  4. Limitations/risks — Critical assessment
  5. Comparison        — Vs alternatives
  6. Recent news       — Latest developments (2025-2026)
  7. Market dynamics   — Broader ecosystem
  8. Expert analysis   — Opinions and reviews
  9. Specific niche    — Niche aspect deep-dive
 10. Synthesis         — Pull it all together
"""

import json
import pathlib
import hashlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "openclaw_tasks"

# ── Skill info (only web_search) ────────────────────────────────────────────
WEB_SEARCH_INFO = [
    {"slug": "web_search", "displayName": "Web Search", "category": "search_web"}
]

TASK_TEMPLATES = [

    # ════════════════════════════════════════════════════════════════════════
    # 1. PAPER REVIEW — Transformer Architecture
    # Foundational paper, massive web coverage, overlapping tutorial/survey URLs
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "paper-transformer-overview",
        "topic": "paper-transformer",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'Attention Is All You Need transformer paper summary'. "
            "Summarize the paper's main contribution in 3 bullet points. "
            "Keep your response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-architecture",
        "topic": "paper-transformer",
        "chain_position": 2,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer architecture encoder decoder multi-head attention details'. "
            "Based on the search results and previous context, list the 5 key components of the transformer architecture "
            "(encoder, decoder, attention heads, positional encoding, feed-forward layers). "
            "One sentence per component. Keep response under 120 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-self-attention",
        "topic": "paper-transformer",
        "chain_position": 3,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer self-attention mechanism query key value computation explained'. "
            "Many results will overlap with earlier transformer searches. "
            "Explain how self-attention computes query, key, and value matrices, and how attention scores work. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-limitations",
        "topic": "paper-transformer",
        "chain_position": 4,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer architecture limitations quadratic attention complexity context length'. "
            "Many results will overlap with earlier searches about transformers. "
            "Identify the top 3 limitations of the original transformer design. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-variants",
        "topic": "paper-transformer",
        "chain_position": 5,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer variants efficient attention Linformer Performer Longformer comparison'. "
            "The same transformer overview pages from earlier turns will appear. "
            "Compare 3 major transformer variants (Linformer, Performer, Longformer) -- "
            "name each and state its key modification in one sentence."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-recent",
        "topic": "paper-transformer",
        "chain_position": 6,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer architecture latest developments 2025 2026 long context scaling'. "
            "Results will overlap with earlier transformer searches. "
            "What are the most important recent advances in transformer architectures? "
            "List 3 developments with one sentence each. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-ecosystem",
        "topic": "paper-transformer",
        "chain_position": 7,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer model ecosystem GPT BERT T5 LLaMA foundation models'. "
            "Results will overlap with earlier transformer searches. "
            "List the 4 most influential transformer-based models (GPT, BERT, T5, LLaMA) "
            "with one sentence each on their key contribution. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-analysis",
        "topic": "paper-transformer",
        "chain_position": 8,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer architecture expert analysis criticism scaling laws debate'. "
            "Results will overlap heavily with earlier searches. "
            "What do researchers say about transformer scaling limits? "
            "Summarize the bull and bear cases in 2 sentences each. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-training",
        "topic": "paper-transformer",
        "chain_position": 9,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer training optimization techniques learning rate warmup mixed precision'. "
            "Results will overlap with earlier transformer searches. "
            "List 3 key training techniques used for large transformers. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-transformer-synthesis",
        "topic": "paper-transformer",
        "chain_position": 10,
        "depends_on": "paper-transformer-overview",
        "description": (
            "Use web_search to search for 'transformer impact NLP computer vision multimodal AI legacy'. "
            "Results will heavily overlap with earlier transformer searches. "
            "Synthesize the overall impact of the transformer architecture: "
            "strengths, weaknesses, and lasting legacy. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 2. PAPER REVIEW — Mamba / State Space Models
    # Recent SSM paper, tons of comparison-with-transformer articles
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "paper-mamba-overview",
        "topic": "paper-mamba",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'Mamba state space model paper summary selective SSM'. "
            "Summarize Mamba's main contribution vs transformers in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-mechanism",
        "topic": "paper-mamba",
        "chain_position": 2,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba selective state space model mechanism hardware-aware design'. "
            "Same SSM/Mamba articles from previous turn will appear. "
            "Explain the selective scan mechanism and hardware-aware design in 2-3 sentences each. "
            "Keep response under 120 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-math",
        "topic": "paper-mamba",
        "chain_position": 3,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'state space model S4 discretization A B C D matrices math explained'. "
            "Many results will overlap with earlier Mamba searches. "
            "Explain the core SSM formulation (A, B, C, D matrices and discretization) "
            "in simple terms. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-limitations",
        "topic": "paper-mamba",
        "chain_position": 4,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba SSM limitations in-context learning recall associative memory'. "
            "Many results overlap with earlier Mamba searches. "
            "List the top 3 limitations of Mamba compared to transformers. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-vs-transformer",
        "topic": "paper-mamba",
        "chain_position": 5,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba vs transformer comparison scaling efficiency benchmarks speed memory'. "
            "Same overview articles will appear again. "
            "Compare Mamba and Transformers on 3 axes: speed, memory, quality. "
            "One sentence per axis. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-recent",
        "topic": "paper-mamba",
        "chain_position": 6,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba 2 state space model latest developments 2025 2026'. "
            "Results will overlap with earlier SSM searches. "
            "What are the latest developments in SSM research since the original Mamba paper? "
            "List 3 advances. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-hybrid",
        "topic": "paper-mamba",
        "chain_position": 7,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'hybrid SSM transformer models Jamba Zamba architecture design'. "
            "Results will overlap with earlier searches. "
            "What are hybrid SSM-transformer architectures and why are they promising? "
            "Name 2 examples and explain the design rationale. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-benchmarks",
        "topic": "paper-mamba",
        "chain_position": 8,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba SSM benchmark results language modeling long context performance'. "
            "Results overlap heavily with earlier searches. "
            "How does Mamba perform on standard language modeling benchmarks vs transformers? "
            "Summarize in 3 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-applications",
        "topic": "paper-mamba",
        "chain_position": 9,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'state space model applications genomics audio time series beyond NLP'. "
            "Results overlap with earlier SSM searches. "
            "List 3 non-NLP application domains where SSMs show particular promise. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mamba-synthesis",
        "topic": "paper-mamba",
        "chain_position": 10,
        "depends_on": "paper-mamba-overview",
        "description": (
            "Use web_search to search for 'Mamba SSM future outlook transformer replacement subquadratic attention'. "
            "Results overlap with earlier SSM searches. "
            "Synthesize: will SSMs replace transformers? Summarize the consensus view, "
            "key strengths, and remaining gaps. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 3. FINANCIAL — NVIDIA and AI Chip Market
    # Most-searched AI company, current financial data, many analyst articles
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "finance-nvidia-overview",
        "topic": "finance-nvidia",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'NVIDIA financial performance revenue 2025 2026'. "
            "Summarize NVIDIA's current financial position in 3 bullet points. "
            "Include latest revenue figure. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-products",
        "topic": "finance-nvidia",
        "chain_position": 2,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA Blackwell H200 B200 data center GPU product lineup'. "
            "Same NVIDIA articles from previous turn will appear. "
            "List NVIDIA's top 3 AI chip products and their target market. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-cuda",
        "topic": "finance-nvidia",
        "chain_position": 3,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA CUDA ecosystem moat developer tools AI frameworks'. "
            "Many results will overlap with earlier NVIDIA searches. "
            "Explain NVIDIA's CUDA software moat: why is it hard for competitors to replicate? "
            "Answer in 3 sentences. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-risks",
        "topic": "finance-nvidia",
        "chain_position": 4,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA risks export controls China competition valuation'. "
            "Many results overlap with earlier NVIDIA searches. "
            "What are the top 3 risks to NVIDIA's business? "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-competition",
        "topic": "finance-nvidia",
        "chain_position": 5,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA vs AMD MI300X vs Google TPU v5 AI training inference'. "
            "Same AI chip articles will appear again. "
            "Compare NVIDIA, AMD, and Google TPU on training and inference capabilities. "
            "One sentence per competitor. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-earnings",
        "topic": "finance-nvidia",
        "chain_position": 6,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA latest earnings Q4 2025 revenue guidance Blackwell ramp'. "
            "Results will overlap with earlier NVIDIA searches. "
            "Summarize NVIDIA's most recent quarterly earnings: revenue, guidance, "
            "and Blackwell production ramp status. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-market",
        "topic": "finance-nvidia",
        "chain_position": 7,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'AI chip market demand supply shortage hyperscaler capex 2026'. "
            "Results will overlap with earlier searches. "
            "What is the current state of AI chip demand vs supply? "
            "How much are hyperscalers spending? Summarize in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-analyst",
        "topic": "finance-nvidia",
        "chain_position": 8,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA stock analyst ratings bull bear case 2026'. "
            "Results overlap heavily with earlier searches. "
            "What are the bull and bear cases for NVIDIA stock? "
            "Summarize each in 2 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-inference",
        "topic": "finance-nvidia",
        "chain_position": 9,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA inference optimization TensorRT deployment edge vs cloud'. "
            "Results will overlap with earlier NVIDIA searches. "
            "How is NVIDIA positioning for the inference market vs training? "
            "What role does TensorRT play? Answer in 3 sentences. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-nvidia-synthesis",
        "topic": "finance-nvidia",
        "chain_position": 10,
        "depends_on": "finance-nvidia-overview",
        "description": (
            "Use web_search to search for 'NVIDIA investment thesis summary strengths weaknesses outlook'. "
            "Results will heavily overlap with earlier searches. "
            "Synthesize the overall NVIDIA investment thesis: key strengths, "
            "main risks, and outlook. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 4. FINANCIAL — Global Semiconductor Supply Chain
    # Geopolitical + tech + financial angles, TSMC/Intel overlap with NVIDIA
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "finance-semiconductor-overview",
        "topic": "finance-semiconductor",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'global semiconductor industry market size revenue 2025 2026'. "
            "Summarize the semiconductor market in 3 bullet points. "
            "Include market size. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-leaders",
        "topic": "finance-semiconductor",
        "chain_position": 2,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'TSMC Samsung Intel foundry market share advanced nodes'. "
            "Same semiconductor articles from previous turn will appear. "
            "List the top 3 foundries and their technology position. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-process",
        "topic": "finance-semiconductor",
        "chain_position": 3,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'semiconductor process technology 3nm 2nm GAA transistor roadmap'. "
            "Many results will overlap with earlier semiconductor searches. "
            "Explain the current state of advanced semiconductor process nodes: "
            "where are 3nm and 2nm, and what is GAA? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-risks",
        "topic": "finance-semiconductor",
        "chain_position": 4,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'semiconductor supply chain risks geopolitics Taiwan China export controls'. "
            "Many results overlap with earlier semiconductor searches. "
            "What are the top 3 geopolitical risks to the semiconductor supply chain? "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-reshoring",
        "topic": "finance-semiconductor",
        "chain_position": 5,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'CHIPS Act semiconductor reshoring US Europe Japan fab construction'. "
            "Same semiconductor articles will appear. "
            "Compare reshoring efforts in US, EU, and Japan. "
            "One sentence per region on current progress."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-ai-demand",
        "topic": "finance-semiconductor",
        "chain_position": 6,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'AI chip demand semiconductor industry growth driver HBM packaging 2026'. "
            "Results will overlap with earlier semiconductor searches. "
            "How is AI demand reshaping the semiconductor industry? "
            "What role does HBM and advanced packaging play? Answer in 3 sentences. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-equipment",
        "topic": "finance-semiconductor",
        "chain_position": 7,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'semiconductor equipment ASML EUV lithography market monopoly'. "
            "Results will overlap with earlier searches. "
            "Explain ASML's role in the semiconductor supply chain and EUV lithography. "
            "Why is it a chokepoint? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-analysis",
        "topic": "finance-semiconductor",
        "chain_position": 8,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'semiconductor industry analyst forecast cycle upturn downturn 2026'. "
            "Results overlap heavily with earlier searches. "
            "What do analysts say about the semiconductor cycle? "
            "Is the industry in an upturn or downturn? Summarize in 3 sentences. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-china",
        "topic": "finance-semiconductor",
        "chain_position": 9,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'China semiconductor self-sufficiency SMIC Huawei chip development progress'. "
            "Results will overlap with earlier semiconductor searches. "
            "How far has China progressed in semiconductor self-sufficiency? "
            "What are SMIC and Huawei's latest achievements? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-semiconductor-synthesis",
        "topic": "finance-semiconductor",
        "chain_position": 10,
        "depends_on": "finance-semiconductor-overview",
        "description": (
            "Use web_search to search for 'semiconductor industry outlook 2026 2027 AI demand geopolitics forecast'. "
            "Results overlap with earlier semiconductor searches. "
            "Synthesize the semiconductor industry outlook: growth drivers, "
            "key risks, and market forecast. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 5. TECH REVIEW — Edge AI Inference Frameworks
    # Directly relevant to on-device scenario, active framework comparison
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "tech-edge-ai-overview",
        "topic": "tech-edge-ai",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'edge AI inference frameworks on-device deployment 2025 2026'. "
            "Summarize the edge AI landscape in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-frameworks",
        "topic": "tech-edge-ai",
        "chain_position": 2,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI framework comparison TensorRT ONNX Runtime Core ML TFLite'. "
            "Same edge AI articles from previous turn will appear. "
            "Compare 4 frameworks: TensorRT, ONNX Runtime, Core ML, TFLite. "
            "One sentence each on their primary platform. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-quantization",
        "topic": "tech-edge-ai",
        "chain_position": 3,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'model quantization techniques INT8 INT4 GPTQ AWQ edge deployment'. "
            "Many results will overlap with earlier edge AI searches. "
            "Explain the main quantization approaches (PTQ, QAT, GPTQ, AWQ) "
            "and their accuracy vs speed tradeoffs. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-challenges",
        "topic": "tech-edge-ai",
        "chain_position": 4,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI deployment challenges memory latency power constraints LLM'. "
            "Many results overlap with earlier edge AI searches. "
            "List the top 3 challenges for deploying LLMs on edge devices. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-hardware",
        "topic": "tech-edge-ai",
        "chain_position": 5,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI hardware NPU Apple Neural Engine Qualcomm Snapdragon comparison'. "
            "Same edge AI articles will appear. "
            "Compare the major edge AI hardware: Apple Neural Engine, Qualcomm Snapdragon NPU, "
            "and Google Tensor TPU. One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-llm",
        "topic": "tech-edge-ai",
        "chain_position": 6,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'on-device LLM deployment Apple Intelligence Gemini Nano Phi small models'. "
            "Results will overlap with earlier edge AI searches. "
            "What on-device LLMs are shipping in 2025-2026? "
            "List 3 examples with model size and device. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-privacy",
        "topic": "tech-edge-ai",
        "chain_position": 7,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI privacy advantages on-device processing data sovereignty'. "
            "Results will overlap with earlier searches. "
            "What are the privacy and latency advantages of on-device AI vs cloud? "
            "List 3 key benefits. One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-benchmarks",
        "topic": "tech-edge-ai",
        "chain_position": 8,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI inference benchmark MLPerf mobile performance comparison 2025'. "
            "Results overlap heavily with earlier searches. "
            "What do MLPerf and other benchmarks show about edge AI performance? "
            "Summarize in 3 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-optimization",
        "topic": "tech-edge-ai",
        "chain_position": 9,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI optimization techniques pruning distillation speculative decoding'. "
            "Results will overlap with earlier edge AI searches. "
            "List 3 key optimization techniques beyond quantization for on-device inference. "
            "One sentence each on the tradeoff. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-edge-ai-synthesis",
        "topic": "tech-edge-ai",
        "chain_position": 10,
        "depends_on": "tech-edge-ai-overview",
        "description": (
            "Use web_search to search for 'edge AI future on-device LLM trends 2026 2027 outlook'. "
            "Results overlap with earlier edge AI searches. "
            "Synthesize: what is the future of on-device AI? "
            "Key trends, remaining challenges, and outlook. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 6. TECH REVIEW — Vector Database Comparison
    # Hot RAG topic, many comparison/benchmark articles with heavy overlap
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "tech-vectordb-overview",
        "topic": "tech-vectordb",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'vector database comparison 2025 2026 Pinecone Weaviate Milvus'. "
            "Summarize the vector DB landscape in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-comparison",
        "topic": "tech-vectordb",
        "chain_position": 2,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'Pinecone vs Weaviate vs Milvus vs Qdrant features benchmark'. "
            "Same vector DB articles from previous turn will appear. "
            "Compare 4 vector databases. One sentence each on their key differentiator. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-indexing",
        "topic": "tech-vectordb",
        "chain_position": 3,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'vector database indexing algorithms HNSW IVF PQ ANN comparison'. "
            "Many results will overlap with earlier vector DB searches. "
            "Explain the main ANN indexing algorithms (HNSW, IVF, PQ) "
            "and their recall vs speed tradeoffs. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-challenges",
        "topic": "tech-vectordb",
        "chain_position": 4,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'vector database challenges scaling cost accuracy filtering'. "
            "Many results overlap with earlier vector DB searches. "
            "List the top 3 challenges when operating vector databases at scale. "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-rag",
        "topic": "tech-vectordb",
        "chain_position": 5,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'vector database RAG retrieval augmented generation architecture best practices'. "
            "Same vector DB articles will appear. "
            "How are vector databases used in RAG pipelines? "
            "Describe the typical architecture in 3 sentences. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-embedding",
        "topic": "tech-vectordb",
        "chain_position": 6,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'embedding models for vector databases OpenAI ada Cohere voyage comparison 2025'. "
            "Results will overlap with earlier vector DB searches. "
            "Compare the leading embedding models used with vector databases. "
            "List 3 models with one sentence each. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-hybrid",
        "topic": "tech-vectordb",
        "chain_position": 7,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'hybrid search vector database keyword BM25 sparse dense retrieval'. "
            "Results will overlap with earlier searches. "
            "What is hybrid search and why is it better than pure vector search? "
            "Explain in 3 sentences. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-benchmarks",
        "topic": "tech-vectordb",
        "chain_position": 8,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'vector database benchmark ann-benchmarks performance comparison 2025 2026'. "
            "Results overlap heavily with earlier searches. "
            "What do benchmarks show about vector database performance? "
            "Which databases lead on latency, recall, and throughput? "
            "Summarize in 3 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-multimodal",
        "topic": "tech-vectordb",
        "chain_position": 9,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'multimodal vector database image text cross-modal search CLIP'. "
            "Results will overlap with earlier vector DB searches. "
            "How are vector databases supporting multimodal search? "
            "List 3 approaches. One sentence each. Keep response under 80 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "tech-vectordb-synthesis",
        "topic": "tech-vectordb",
        "chain_position": 10,
        "depends_on": "tech-vectordb-overview",
        "description": (
            "Use web_search to search for 'vector database future trends market outlook embedded serverless'. "
            "Results overlap with earlier vector DB searches. "
            "Synthesize: where is the vector database market heading? "
            "Key trends, consolidation, and outlook. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 7. DOMAIN — CRISPR Gene Editing Clinical Trials
    # Active clinical trials, approved treatments (2025), specific data points
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "domain-crispr-overview",
        "topic": "domain-crispr",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'CRISPR gene editing clinical trials progress 2025 2026'. "
            "Summarize the current state of CRISPR clinical trials in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-treatments",
        "topic": "domain-crispr",
        "chain_position": 2,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR approved treatments Casgevy sickle cell beta thalassemia gene therapy'. "
            "Same CRISPR articles from previous turn will appear. "
            "List the top 3 approved or late-stage CRISPR treatments. "
            "One sentence each on the target disease. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-mechanism",
        "topic": "domain-crispr",
        "chain_position": 3,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR Cas9 mechanism guide RNA double strand break repair explained'. "
            "Many results will overlap with earlier CRISPR searches. "
            "Explain how CRISPR-Cas9 works: guide RNA, Cas9 cutting, and DNA repair pathways. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-safety",
        "topic": "domain-crispr",
        "chain_position": 4,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR safety concerns off-target effects delivery challenges immunogenicity'. "
            "Many results overlap with earlier CRISPR searches. "
            "What are the top 3 safety concerns? One sentence each. "
            "Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-alternatives",
        "topic": "domain-crispr",
        "chain_position": 5,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR vs base editing prime editing gene therapy comparison accuracy'. "
            "Same gene editing articles will appear. "
            "Compare CRISPR, base editing, and prime editing. "
            "One sentence each on the key advantage. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-delivery",
        "topic": "domain-crispr",
        "chain_position": 6,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR in vivo delivery methods lipid nanoparticle AAV virus-like particles 2025'. "
            "Results will overlap with earlier CRISPR searches. "
            "What are the main delivery methods for getting CRISPR into cells in vivo? "
            "List 3 approaches. One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-companies",
        "topic": "domain-crispr",
        "chain_position": 7,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR therapeutics companies Editas Intellia Beam pipeline market'. "
            "Results will overlap with earlier searches. "
            "List the top 3 CRISPR therapy companies and their lead programs. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-regulation",
        "topic": "domain-crispr",
        "chain_position": 8,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR gene editing regulation FDA EMA approval pathway ethics'. "
            "Results overlap heavily with earlier searches. "
            "How are regulators approaching CRISPR therapies? "
            "What are the key regulatory and ethical considerations? "
            "Summarize in 3 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-cancer",
        "topic": "domain-crispr",
        "chain_position": 9,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR cancer treatment CAR-T cell therapy clinical trials results'. "
            "Results will overlap with earlier CRISPR searches. "
            "How is CRISPR being used in cancer immunotherapy? "
            "Describe the CAR-T connection and latest trial results. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-crispr-synthesis",
        "topic": "domain-crispr",
        "chain_position": 10,
        "depends_on": "domain-crispr-overview",
        "description": (
            "Use web_search to search for 'CRISPR gene editing future outlook 2026 2030 applications promise'. "
            "Results overlap with earlier CRISPR searches. "
            "Synthesize the CRISPR outlook: most promising applications, "
            "remaining barriers, and timeline to broader clinical use. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 8. DOMAIN — Quantum Computing
    # Recent milestones (Google Willow, IBM), specific qubit counts and dates
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "domain-quantum-overview",
        "topic": "domain-quantum",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'quantum computing progress 2025 2026 logical qubits error correction'. "
            "Summarize the current state of quantum computing in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-hardware",
        "topic": "domain-quantum",
        "chain_position": 2,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing hardware approaches superconducting trapped ion photonic'. "
            "Same quantum articles from previous turn will appear. "
            "Compare 3 qubit technologies: superconducting, trapped ion, and photonic. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-error-correction",
        "topic": "domain-quantum",
        "chain_position": 3,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum error correction surface code topological codes overhead explained'. "
            "Many results will overlap with earlier quantum searches. "
            "Explain quantum error correction: why it's needed and how surface codes work. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-challenges",
        "topic": "domain-quantum",
        "chain_position": 4,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing challenges decoherence scaling qubit overhead'. "
            "Many results overlap with earlier quantum searches. "
            "What are the top 3 obstacles to fault-tolerant quantum computing? "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-companies",
        "topic": "domain-quantum",
        "chain_position": 5,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing companies Google IBM Microsoft qubit count milestones 2025'. "
            "Same quantum articles will appear. "
            "Compare the 3 leading quantum computing companies and their latest milestone. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-google-willow",
        "topic": "domain-quantum",
        "chain_position": 6,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'Google Willow quantum chip error correction breakthrough details'. "
            "Results will overlap with earlier quantum searches. "
            "What did Google achieve with the Willow quantum chip? "
            "Describe the key breakthrough and its significance. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-applications",
        "topic": "domain-quantum",
        "chain_position": 7,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing applications cryptography drug discovery optimization use cases'. "
            "Results will overlap with earlier searches. "
            "What are the 3 most promising near-term applications for quantum computing? "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-software",
        "topic": "domain-quantum",
        "chain_position": 8,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing software frameworks Qiskit Cirq PennyLane SDK comparison'. "
            "Results overlap heavily with earlier searches. "
            "Compare the 3 main quantum computing SDKs. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-investment",
        "topic": "domain-quantum",
        "chain_position": 9,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing investment funding venture capital government spending 2025 2026'. "
            "Results will overlap with earlier quantum searches. "
            "How much is being invested in quantum computing? "
            "Summarize public and private investment levels. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-quantum-synthesis",
        "topic": "domain-quantum",
        "chain_position": 10,
        "depends_on": "domain-quantum-overview",
        "description": (
            "Use web_search to search for 'quantum computing timeline practical advantage forecast 2030 outlook'. "
            "Results overlap with earlier quantum searches. "
            "Synthesize: when will quantum computers achieve practical advantage? "
            "Key milestones, remaining barriers, and realistic timeline. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 9. DOMAIN — Nuclear Fusion Energy
    # Private company investments, ITER updates, specific engineering milestones
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "domain-fusion-overview",
        "topic": "domain-fusion",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'nuclear fusion energy progress ITER private companies 2025 2026'. "
            "Summarize the current state of fusion energy in 3 bullet points. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-approaches",
        "topic": "domain-fusion",
        "chain_position": 2,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion energy approaches tokamak stellarator laser inertial confinement comparison'. "
            "Same fusion articles from previous turn will appear. "
            "Compare 3 main fusion approaches: tokamak, stellarator, and inertial confinement. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-plasma",
        "topic": "domain-fusion",
        "chain_position": 3,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion plasma containment magnetic confinement temperature pressure conditions'. "
            "Many results will overlap with earlier fusion searches. "
            "What conditions are needed for sustained fusion? "
            "Explain plasma temperature, pressure, and confinement time requirements. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-challenges",
        "topic": "domain-fusion",
        "chain_position": 4,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion energy challenges plasma containment materials tritium supply'. "
            "Many results overlap with earlier fusion searches. "
            "What are the top 3 engineering challenges for commercial fusion? "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-companies",
        "topic": "domain-fusion",
        "chain_position": 5,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'private fusion companies Commonwealth Fusion TAE Helion funding milestones'. "
            "Same fusion articles will appear. "
            "List the top 3 private fusion companies and their approach. "
            "One sentence each. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-iter",
        "topic": "domain-fusion",
        "chain_position": 6,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'ITER project status update timeline delay cost 2025 2026'. "
            "Results will overlap with earlier fusion searches. "
            "What is the current status of ITER? "
            "Summarize the timeline, cost overruns, and expected first plasma date. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-materials",
        "topic": "domain-fusion",
        "chain_position": 7,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion reactor materials tungsten first wall blanket neutron damage'. "
            "Results will overlap with earlier searches. "
            "What are the key materials challenges for fusion reactors? "
            "Discuss first-wall materials and neutron damage. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-hts",
        "topic": "domain-fusion",
        "chain_position": 8,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'high temperature superconducting magnets HTS fusion compact tokamak SPARC'. "
            "Results overlap heavily with earlier searches. "
            "How are HTS magnets changing the fusion landscape? "
            "What advantage do they give compact tokamaks like SPARC? "
            "Summarize in 3 sentences. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-economics",
        "topic": "domain-fusion",
        "chain_position": 9,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion energy economics cost per MWh competitiveness solar wind comparison'. "
            "Results will overlap with earlier fusion searches. "
            "Can fusion compete economically with renewables? "
            "What is the projected cost of fusion electricity? "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "domain-fusion-synthesis",
        "topic": "domain-fusion",
        "chain_position": 10,
        "depends_on": "domain-fusion-overview",
        "description": (
            "Use web_search to search for 'fusion energy timeline commercial power grid 2030 2035 outlook realistic'. "
            "Results overlap with earlier fusion searches. "
            "Synthesize: when will fusion reach commercial viability? "
            "Key milestones ahead, main barriers, and realistic timeline. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 10. FINANCIAL — Electric Vehicle Market
    # Global scope, policy comparison across regions, specific sales numbers
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "finance-ev-overview",
        "topic": "finance-ev-market",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'electric vehicle market size growth 2025 2026 global sales'. "
            "Summarize the global EV market in 3 bullet points. "
            "Include total sales figures. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-leaders",
        "topic": "finance-ev-market",
        "chain_position": 2,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV market leaders Tesla BYD market share 2025 2026'. "
            "Same EV market articles from previous turn will appear. "
            "List the top 4 EV manufacturers by market share with one sentence each. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-battery",
        "topic": "finance-ev-market",
        "chain_position": 3,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV battery technology LFP NMC solid state cost per kWh trends'. "
            "Many results will overlap with earlier EV searches. "
            "Compare LFP and NMC battery chemistries for EVs. "
            "What is the current cost per kWh? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-challenges",
        "topic": "finance-ev-market",
        "chain_position": 4,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'electric vehicle adoption barriers charging infrastructure range anxiety cost'. "
            "Many results overlap with earlier EV searches. "
            "What are the top 3 barriers to EV adoption? "
            "One sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-policy",
        "topic": "finance-ev-market",
        "chain_position": 5,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV subsidies tax credits policy US EU China 2025 2026'. "
            "Same EV market articles will appear. "
            "Compare EV policy incentives in US, EU, and China. "
            "One sentence per region. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-charging",
        "topic": "finance-ev-market",
        "chain_position": 6,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV charging infrastructure deployment fast charging NACS CCS standards 2025 2026'. "
            "Results will overlap with earlier EV searches. "
            "What is the state of EV charging infrastructure? "
            "Discuss fast charging rollout and connector standard convergence. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-china",
        "topic": "finance-ev-market",
        "chain_position": 7,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'China EV market BYD exports dominance global competition tariffs'. "
            "Results will overlap with earlier searches. "
            "How is China's EV industry reshaping the global market? "
            "Discuss BYD's rise and trade tensions. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-analysis",
        "topic": "finance-ev-market",
        "chain_position": 8,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV market analyst forecast growth slowdown demand 2026 outlook'. "
            "Results overlap heavily with earlier searches. "
            "What do analysts say about EV growth rates? "
            "Is growth accelerating or decelerating? Summarize in 3 sentences. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-supply-chain",
        "topic": "finance-ev-market",
        "chain_position": 9,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'EV supply chain lithium cobalt nickel mining critical minerals shortage'. "
            "Results will overlap with earlier EV searches. "
            "What are the critical mineral supply chain risks for EVs? "
            "List 3 key minerals and their supply constraints. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "finance-ev-synthesis",
        "topic": "finance-ev-market",
        "chain_position": 10,
        "depends_on": "finance-ev-overview",
        "description": (
            "Use web_search to search for 'electric vehicle market forecast 2030 penetration rate projection outlook'. "
            "Results overlap with earlier EV searches. "
            "Synthesize: what is the consensus EV market forecast for 2030? "
            "Growth drivers, headwinds, and market share projections. "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 11. PAPER REVIEW — Hyper-Connections
    # Novel residual connection replacement, addresses gradient vanishing vs
    # representation collapse seesaw effect
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "paper-hyperconn-overview",
        "topic": "paper-hyperconn",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'Hyper-Connections paper residual connections alternative deep learning'. "
            "Summarize the paper's main contribution in 3 bullet points. "
            "Keep your response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-mechanism",
        "topic": "paper-hyperconn",
        "chain_position": 2,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections mechanism dynamic layer connection strength depth features'. "
            "Same hyper-connections articles from previous turn will appear. "
            "Explain how hyper-connections work: expansion rate, connection weights, and layer reorganization. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-residual",
        "topic": "paper-hyperconn",
        "chain_position": 3,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'residual connections deep learning problems gradient vanishing representation collapse'. "
            "Many results overlap with earlier hyper-connections searches. "
            "Explain the seesaw effect between gradient vanishing and representation collapse in residual connections. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-limitations",
        "topic": "paper-hyperconn",
        "chain_position": 4,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections limitations training instability identity mapping scalability'. "
            "Results overlap with earlier searches. "
            "What are the main limitations of hyper-connections? "
            "List 3 issues, one sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-vs-residual",
        "topic": "paper-hyperconn",
        "chain_position": 5,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections vs residual connections vs highway networks skip connections comparison'. "
            "Results overlap with earlier searches. "
            "Compare hyper-connections with standard residual connections and highway networks. "
            "One key difference per approach. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-llm",
        "topic": "paper-hyperconn",
        "chain_position": 6,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections large language model pretraining dense sparse MoE results'. "
            "Results overlap with earlier searches. "
            "How do hyper-connections perform in LLM pretraining for both dense and sparse models? "
            "Summarize key results. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-vision",
        "topic": "paper-hyperconn",
        "chain_position": 7,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections computer vision image classification performance results'. "
            "Results overlap with earlier searches. "
            "How do hyper-connections perform on vision tasks? "
            "Summarize results and compare to residual baselines. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-analysis",
        "topic": "paper-hyperconn",
        "chain_position": 8,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections gradient flow analysis representation learning deep network theory'. "
            "Results overlap heavily with earlier searches. "
            "What theoretical insights do hyper-connections provide about gradient flow and representation learning? "
            "Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-implementation",
        "topic": "paper-hyperconn",
        "chain_position": 9,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections implementation expansion rate hyperparameters practical guidelines'. "
            "Results overlap with earlier searches. "
            "What are the key implementation details and hyperparameters for hyper-connections? "
            "List the main practical considerations. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-hyperconn-synthesis",
        "topic": "paper-hyperconn",
        "chain_position": 10,
        "depends_on": "paper-hyperconn-overview",
        "description": (
            "Use web_search to search for 'hyper-connections impact residual connection alternatives future architecture design'. "
            "Results heavily overlap with earlier searches. "
            "Synthesize: strengths, weaknesses, and potential impact of hyper-connections "
            "on future neural network architecture design. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 12. PAPER REVIEW — Attention Residuals (AttnRes)
    # Kimi Team, replaces fixed residual accumulation with softmax attention
    # over preceding layer outputs
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "paper-attnres-overview",
        "topic": "paper-attnres",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'Attention Residuals AttnRes paper Kimi Team residual connections softmax'. "
            "Summarize the paper's main contribution in 3 bullet points. "
            "Keep your response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-mechanism",
        "topic": "paper-attnres",
        "chain_position": 2,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals mechanism softmax attention preceding layer outputs aggregation'. "
            "Same articles from previous turn will appear. "
            "Explain how AttnRes replaces fixed residual accumulation with learned attention-based aggregation. "
            "Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-block",
        "topic": "paper-attnres",
        "chain_position": 3,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Block AttnRes block-level attention residuals memory efficiency scaling'. "
            "Results overlap with earlier searches. "
            "Explain Block AttnRes: how it groups layers into blocks and reduces memory overhead "
            "while preserving performance. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-prenorm",
        "topic": "paper-attnres",
        "chain_position": 4,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'PreNorm dilution hidden state growth residual connections deep transformers problem'. "
            "Results overlap with earlier searches. "
            "Explain the PreNorm dilution problem that AttnRes addresses: "
            "how uniform residual accumulation causes hidden-state growth and dilutes layer contributions. "
            "Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-vs-alternatives",
        "topic": "paper-attnres",
        "chain_position": 5,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals vs hyper-connections vs standard residual connections comparison'. "
            "Results overlap with earlier searches. "
            "Compare AttnRes with standard residual connections and hyper-connections. "
            "One key difference per approach. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-kimi",
        "topic": "paper-attnres",
        "chain_position": 6,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Kimi Linear architecture 48B parameters 3B activated MoE sparse model'. "
            "Results overlap with earlier searches. "
            "Describe the Kimi Linear architecture where AttnRes was implemented: "
            "model size, activation ratio, and training details. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-scaling",
        "topic": "paper-attnres",
        "chain_position": 7,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals scaling laws experiments model size performance improvement'. "
            "Results overlap with earlier searches. "
            "What do the scaling law experiments show about AttnRes benefits at different model sizes? "
            "Summarize key findings. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-gradient",
        "topic": "paper-attnres",
        "chain_position": 8,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals gradient distribution output uniformity depth analysis'. "
            "Results overlap heavily with earlier searches. "
            "How does AttnRes improve gradient distribution and output uniformity across depth? "
            "Summarize the analysis findings. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-ablation",
        "topic": "paper-attnres",
        "chain_position": 9,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals ablation study content-dependent depth-wise selection results'. "
            "Results overlap with earlier searches. "
            "What do the ablation studies reveal about the importance of content-dependent "
            "depth-wise selection in AttnRes? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-attnres-synthesis",
        "topic": "paper-attnres",
        "chain_position": 10,
        "depends_on": "paper-attnres-overview",
        "description": (
            "Use web_search to search for 'Attention Residuals impact future deep learning architecture residual replacement'. "
            "Results heavily overlap with earlier searches. "
            "Synthesize: strengths, limitations, and potential impact of Attention Residuals "
            "on future model architectures. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },

    # ════════════════════════════════════════════════════════════════════════
    # 13. PAPER REVIEW — mHC (Manifold-Constrained Hyper-Connections)
    # Fixes HC training instability with manifold projection, restores
    # identity mapping property
    # ════════════════════════════════════════════════════════════════════════
    {
        "name": "paper-mhc-overview",
        "topic": "paper-mhc",
        "chain_position": 1,
        "depends_on": None,
        "description": (
            "Use web_search to search for 'mHC manifold-constrained hyper-connections paper identity mapping scalability'. "
            "Summarize the paper's main contribution in 3 bullet points. "
            "Keep your response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-mechanism",
        "topic": "paper-mhc",
        "chain_position": 2,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'manifold-constrained hyper-connections manifold projection residual space framework'. "
            "Same articles from previous turn will appear. "
            "Explain how mHC uses manifold projection to constrain hyper-connections "
            "while restoring identity mapping. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-identity",
        "topic": "paper-mhc",
        "chain_position": 3,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'identity mapping property residual connections importance deep learning training stability'. "
            "Results overlap with earlier searches. "
            "Why is the identity mapping property important for training stability? "
            "How does HC compromise it and how does mHC restore it? Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-vs-hc",
        "topic": "paper-mhc",
        "chain_position": 4,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'mHC vs hyper-connections training instability scalability comparison improvements'. "
            "Results overlap with earlier searches. "
            "Compare mHC with the original HC: what specific problems does mHC fix? "
            "List 3 improvements, one sentence each. Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-vs-attnres",
        "topic": "paper-mhc",
        "chain_position": 5,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'mHC vs attention residuals vs standard residual connections architecture comparison'. "
            "Results overlap with earlier searches. "
            "Compare mHC with Attention Residuals and standard residual connections. "
            "Key tradeoffs between the approaches. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-scaling",
        "topic": "paper-mhc",
        "chain_position": 6,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'mHC manifold hyper-connections large scale training foundation models scalability results'. "
            "Results overlap with earlier searches. "
            "How does mHC perform at large scale? Summarize scalability results "
            "and training stability improvements. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-efficiency",
        "topic": "paper-mhc",
        "chain_position": 7,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'mHC computational efficiency infrastructure optimization practical deployment'. "
            "Results overlap with earlier searches. "
            "What are the computational costs and efficiency tradeoffs of mHC? "
            "Summarize infrastructure considerations. Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-theory",
        "topic": "paper-mhc",
        "chain_position": 8,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'manifold constraint neural network residual space projection mathematical framework theory'. "
            "Results overlap heavily with earlier searches. "
            "Explain the theoretical framework behind manifold-constrained connections: "
            "what manifold is used and why? Keep response under 80 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-applications",
        "topic": "paper-mhc",
        "chain_position": 9,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'mHC manifold hyper-connections applications language models vision multimodal'. "
            "Results overlap with earlier searches. "
            "What applications and model types benefit most from mHC? "
            "List key application domains and results. Keep response under 100 words."
        ),
        "category": "planning", "difficulty": "medium", "expected_steps": 3,
    },
    {
        "name": "paper-mhc-synthesis",
        "topic": "paper-mhc",
        "chain_position": 10,
        "depends_on": "paper-mhc-overview",
        "description": (
            "Use web_search to search for 'residual connection alternatives future hyper-connections attention residuals mHC outlook'. "
            "Results heavily overlap with earlier searches. "
            "Synthesize the residual connection innovation landscape: "
            "HC, mHC, AttnRes — which approach is most promising and why? "
            "Keep response under 100 words."
        ),
        "category": "summarization", "difficulty": "medium", "expected_steps": 3,
    },
]

assert len(TASK_TEMPLATES) == 130, f"Expected 130 tasks, got {len(TASK_TEMPLATES)}"


def generate_task_id(task: dict) -> str:
    raw = f"{task['name']}-web_search"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_task(template: dict) -> dict:
    task_id = generate_task_id(template)
    return {
        "id": task_id,
        "name": template["name"],
        "topic": template["topic"],
        "chain_position": template["chain_position"],
        "depends_on": template["depends_on"],
        "description": template["description"],
        "category": template["category"],
        "difficulty": template["difficulty"],
        "expected_steps": template["expected_steps"],
        "skills_required": ["web_search"],
        "skills_info": WEB_SEARCH_INFO,
        "num_skills": 1,
        "ground_truth": None,
    }


def main():
    if TASKS_DIR.exists():
        for f in TASKS_DIR.glob("*.json"):
            f.unlink()
    TASKS_DIR.mkdir(exist_ok=True)

    all_tasks = []
    for tmpl in TASK_TEMPLATES:
        task = build_task(tmpl)
        all_tasks.append(task)
        (TASKS_DIR / f"{task['name']}.json").write_text(
            json.dumps(task, indent=2, ensure_ascii=False)
        )

    (ROOT / "openclaw_tasks_all.json").write_text(
        json.dumps(all_tasks, indent=2, ensure_ascii=False)
    )

    # ── Summary ──────────────────────────────────────────────────────────
    topics = {}
    for t in all_tasks:
        topics.setdefault(t["topic"], []).append(t)

    print(f"Generated {len(all_tasks)} tasks, {len(topics)} topics x 10 tasks each\n")

    print("Topic chains (seed -> dependents):")
    for topic, tasks in sorted(topics.items()):
        seed = [t for t in tasks if t["chain_position"] == 1][0]
        deps = [t for t in tasks if t["chain_position"] > 1]
        print(f"  {topic:30s} {seed['name']} -> {len(deps)} follow-ups")

    print()
    categories = Counter(t["category"] for t in all_tasks)
    print("Category distribution:")
    for cat, count in categories.most_common():
        print(f"  {cat:20s} {count:3d}/{len(all_tasks)}")

    print(f"\nOutput: openclaw_tasks_all.json + {len(all_tasks)} files in openclaw_tasks/")


if __name__ == "__main__":
    main()
