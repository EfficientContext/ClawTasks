# ContextPilot × ClawBench: Subagent Prefix Sharing Analysis

## 问题: 为什么现有 ClawBench task 看不到 ContextPilot end-to-end 效果

### 现有 task 的问题

30 个 task 全是同一模式: `web_search → web_fetch → summarize → rewrite → save`

1. **OpenClaw 有内置 `web_search` / `web_fetch`** — agent 不需要读任何 SKILL.md
2. **任务纯顺序** — 没有独立并行的 sub-task，agent 不会 spawn subagent
3. **Tool result 内容小且无结构** — 搜索结果不足以体现 reorder 价值
4. **System prompt 在 session 内不变** — SGLang RadixCache 天然 prefix cache hit

所以 ContextPilot 只能做到微量 prefill latency 改善 (搜索结果 JSON reorder)，end-to-end 几乎为零。

---

## SGLang RadixCache 能做 vs 不能做

### SGLang 天然处理好的 (不需要 ContextPilot)

| 场景 | SGLang 原生行为 |
|------|---------------|
| Main agent turn N → turn N+1 | System prompt 不变 + 旧 messages 不变 = prefix cache hit |
| Subagent A turn N → turn N+1 | 同上，subagent 自己的 session 内 prefix 不变 |
| Subagent A → Subagent B (同一 parent) | System prompt 几乎一样 (minimal mode)，仅 `## Subagent Context` 不同，前面全部 cache hit |

### SGLang 做不到的 (只有 ContextPilot 能做)

| 场景 | 为什么 SGLang 做不到 | ContextPilot 怎么做 |
|------|---------------------|-------------------|
| **Main agent → Subagent** prefix sharing | Tooling section 内容不同 (main 有 25 tools，subagent 有 18 tools)，在 prompt 第 ~3 行就 diverge | Reorder sections: 把 Safety/CLI/Skills/Workspace 等 **byte-identical** 的 section 移到 Tooling 前面 |
| **Cross-turn tool result reorder** | 搜索结果顺序变了 = 不同 tokens = prefix break | 对 JSON results array 重排使 overlapping docs 顺序一致 |
| **Cross-turn content dedup** | 相同内容但在不同 message 位置 = 无法 prefix match | Hash-based 识别已见过的 content，替换为 hint |
| **EXTERNAL_UNTRUSTED_CONTENT ID strip** | 每次 random hex ID 不同 = prefix break | 正则 strip random IDs |

---

## Main → Subagent Prefix Divergence 分析

### OpenClaw System Prompt Section 排列 (当前顺序)

**Full mode (main agent):**
```
1. Identity line                          ← IDENTICAL
2. ## Tooling (25 tools)                  ← DIFFERENT (subagent 只有 18 tools)
3. ## Tool Call Style                     ← IDENTICAL
4. ## Safety                              ← IDENTICAL
5. ## CLI Quick Reference                 ← IDENTICAL
6. ## Skills (mandatory)                  ← IDENTICAL (same skillsPrompt)
7. ## Memory Recall                       ← FULL ONLY (skipped in minimal)
8. ## Self-Update                         ← FULL ONLY
9. ## Model Aliases                       ← FULL ONLY
10. ## Workspace                          ← IDENTICAL
11. ## Documentation                      ← FULL ONLY
12-27. (more full-only + shared sections)
```

**Minimal mode (subagent):**
```
1. Identity line                          ← IDENTICAL
2. ## Tooling (18 tools)                  ← DIFFERENT
3. ## Tool Call Style                     ← IDENTICAL
4. ## Safety                              ← IDENTICAL
5. ## CLI Quick Reference                 ← IDENTICAL
6. ## Skills (mandatory)                  ← IDENTICAL
7. ## Workspace                           ← IDENTICAL
8-15. (subagent-specific sections)
```

### SGLang 看到的 prefix match

```
Identity line (1 行, ~20 tokens) → MATCH
## Tooling (header line) → MATCH  
"Tool availability (filtered by policy):" → MATCH
"Tool names are case-sensitive..." → MATCH
"- read: Read a file..." → MATCH (假设 read 在两个列表里都排第一)
...但很快 tool list 内容不同 → DIVERGE
```

**SGLang 有效 prefix: ~50-80 tokens (几乎为零)**

### ContextPilot reorder 后的 prefix match

ContextPilot 把 byte-identical sections 移到最前面:

**Reordered main agent:**
```
1. Identity line                          ← IDENTICAL
2. ## Safety                              ← IDENTICAL (~500 tokens)
3. ## CLI Quick Reference                 ← IDENTICAL (~800 tokens)
4. ## Skills (mandatory)                  ← IDENTICAL (~800 tokens)
5. ## Tool Call Style                     ← IDENTICAL (~300 tokens)
6. ## Workspace                           ← IDENTICAL (~150 tokens)
7. ## Current Date & Time                 ← IDENTICAL (~50 tokens)
8. ## Workspace Files                     ← IDENTICAL (~150 tokens)
--- DIVERGE POINT ---
9. ## Tooling (25 tools)                  ← DIFFERENT
10. ## Memory Recall                      ← FULL ONLY
...
```

**Reordered subagent:**
```
1. Identity line                          ← IDENTICAL
2. ## Safety                              ← IDENTICAL
3. ## CLI Quick Reference                 ← IDENTICAL
4. ## Skills (mandatory)                  ← IDENTICAL
5. ## Tool Call Style                     ← IDENTICAL
6. ## Workspace                           ← IDENTICAL
7. ## Current Date & Time                 ← IDENTICAL
8. ## Workspace Files                     ← IDENTICAL
--- DIVERGE POINT ---
9. ## Tooling (18 tools)                  ← DIFFERENT
10. ## Subagent Context                   ← MINIMAL ONLY
...
```

**ContextPilot 有效 prefix: ~2,770+ tokens**

### 每个 subagent LLM call 的收益

| Metric | 无 ContextPilot | 有 ContextPilot |
|--------|----------------|-----------------|
| 共享 prefix tokens | ~50 | ~2,770 |
| Subagent system prompt 总 tokens | ~5,000-8,000 | ~5,000-8,000 |
| Prefix hit 比例 | ~1% | ~35-55% |
| Prefill 节省时间 (50ms/1K tokens) | ~2.5ms | ~138ms |

---

## Subagent 会不会被用到: 验证

### OpenClaw System Prompt 中的指令

```
"If a task is more complex or takes longer, spawn a sub-agent.
 Completion is push-based: it will auto-announce when done."
```

Tool description:
```
"sessions_spawn: Spawn an isolated sub-agent session"
```

### 什么样的 task 会触发 subagent

**会触发:**
- 任务有 3+ 个 **独立可并行** 的 sub-task
- 任务明确说 "independently" / "in parallel" / "each ... separately"
- 任务复杂到单 agent 需要太久

**不会触发 (现有 ClawBench 的问题):**
- 纯顺序 pipeline: search → fetch → summarize → save
- 单一 deliverable
- 内置工具能直接完成的简单任务

### Default limits

```
maxSpawnDepth = 1          (subagent 不能再生 subagent)
maxChildrenPerAgent = 5    (最多 5 个并行 subagent)
maxConcurrent = 8          (全局最多 8 个 subagent run)
```

### 哪些 Skills 需要读 SKILL.md (非内置)

| Skill | 类型 | 为什么必须读 SKILL.md |
|-------|------|---------------------|
| summarize | CLI tool (`summarize "url" --model ...`) | OpenClaw 没有内置 URL summarization，必须知道 CLI 语法 |
| nano-pdf | CLI tool | OpenClaw 没有 PDF 生成能力 |
| markdown-converter | CLI tool (`uvx markitdown`) | OpenClaw 没有 document-to-markdown 转换 |
| openai-whisper | CLI tool | OpenClaw 没有 speech-to-text |
| humanizer | Prompting guide (24 anti-patterns) | 没有这个知识 agent 做不出高质量 humanization |
| superdesign | Prompting guide (oklch, fonts, etc.) | 没有这个知识 agent 做不出特定设计风格 |

**内置工具覆盖的 (读不读 SKILL.md 都行):**
- web_search → OpenClaw 内置 `web_search` tool
- web_fetch → OpenClaw 内置 `web_fetch` tool
- agent-browser → OpenClaw 内置 `browser` tool (可能有差异)

---

## 新 Task 设计原则

为了让 ContextPilot 的 end-to-end 效果可见:

1. **必须触发 subagent spawning** → 3+ 个独立并行的研究/处理任务
2. **必须用非内置 skill** → 每个 sub-task 需要 summarize / nano-pdf / markdown-converter 等 CLI tool
3. **Subagent 必须多轮对话** → 每个 sub-task 需要 5+ 步骤 (search → fetch → CLI tool → compile)
4. **跨 turn 有 overlap** → 不同 sub-task 搜索相关主题，结果有重叠
5. **Chain 结构** → 后续 task 在同一 session 中追加工作

### ContextPilot 在每种场景的收益

| 场景 | 每次调用节省 tokens | 调用次数 | 总节省 |
|------|---------------------|---------|--------|
| Main → Subagent prefix (section reorder) | ~2,770 | 3-5 subagent 首次调用 | ~8,310-13,850 |
| Subagent 多轮 prefix (自然 cache) | SGLang 处理 | N/A | SGLang 已覆盖 |
| Cross-turn tool result reorder | ~500-1,000 | 5-10 次/session | ~2,500-10,000 |
| SKILL.md 重复读取 dedup | ~2,000-5,000 | 2-4 次 | ~4,000-20,000 |
| EXTERNAL marker strip | ~50-200 per msg | 10-20 msgs | ~500-4,000 |
| **Per-task total** | | | **~15,000-48,000 tokens** |

以 Anthropic Claude Sonnet 3.5 ($3/M input) 计算: ~$0.05-0.15/task
以 SGLang self-hosted (prefill ~50ms/1K tokens) 计算: ~0.75-2.4s latency saved/task

---

## Token-Level Trace: `infra-cloud-k8s-comparison` Task

### LLM Call 流程 (预期)

```
Call #1: Main agent 收到 task
  → System prompt (full mode, ~10K tokens) + user message
  → SGLang: cold start, 无 cache
  → Agent 决定: "4 independent providers → spawn 4 subagents"
  → Tool call: sessions_spawn × 4

Call #2: Subagent A (AWS EKS) 启动
  → System prompt (minimal mode, ~6K tokens) + subagent task
  → SGLang 看到的 prefix:
    - "You are a personal assistant running inside OpenClaw.\n\n## Tooling\n"
    - 接下来是 tool list... 但 subagent tool list 比 main agent 少 7 个 tools
    - ❌ PREFIX BREAK at ~line 5 (第一个被删除的 tool)
  → SGLang prefix cache miss: 只命中 ~50 tokens
  → 需要 prefill 全部 ~6K tokens

Call #3-5: Subagent B/C/D 启动
  → System prompt 与 Subagent A 几乎一样 (同样 minimal mode, 同样 tools)
  → 唯一不同: ## Subagent Context (不同 task description)
  → SGLang: ✅ prefix cache HIT 直到 ## Subagent Context (~5K tokens)
  → 只需 prefill ~1K tokens (Subagent Context + Runtime)

Call #6-20: Subagent 各自多轮对话 (web_search, web_fetch, summarize, etc.)
  → 每个 subagent session 内: SGLang 天然 prefix cache hit (system prompt + 旧 messages)
  → ✅ SGLang 处理好

Call #21-22: Main agent 收到 4 个 subagent 结果, 合成
  → SGLang: ✅ prefix cache hit (main agent session 的旧 context)
```

### SGLang 无法优化的部分 (只有 ContextPilot 能做)

**Call #2: Main → Subagent A (首次 subagent 调用)**

```
Main agent system prompt (当前顺序):
Token  0-  20: "You are a personal assistant running inside OpenClaw.\n\n"
Token  20-  25: "## Tooling\n"
Token  25-  30: "Tool availability (filtered by policy):\n"
Token  30-  35: "Tool names are case-sensitive. Call tools exactly as listed.\n"
Token  35- 350: "- read: Read a file or ...\n- write: ...\n- edit: ...\n- grep: ...\n" (18 共同 tools)
Token 350- 550: "- gateway: ...\n- agents_list: ...\n- session_status: ...\n- cron: ...\n- memory_search: ...\n- memory_get: ...\n- sessions_send: ...\n" (7 个 subagent 没有的 tools)
Token 550- 600: "TOOLS.md does not control ...\nFor long waits ...\n"
Token 600- 620: "If a task is more complex ...\n\n"
Token 620- 820: "## Tool Call Style\n..."
Token 820-1300: "## Safety\n..."
Token 1300-2100: "## CLI Quick Reference\n..."
Token 2100-2900: "## Skills (mandatory)\n..."
...

Subagent system prompt (当前顺序):
Token  0-  20: "You are a personal assistant running inside OpenClaw.\n\n"   ← MATCH
Token  20-  25: "## Tooling\n"                                               ← MATCH
Token  25-  30: "Tool availability (filtered by policy):\n"                   ← MATCH
Token  30-  35: "Tool names are case-sensitive...\n"                          ← MATCH
Token  35- 350: "- read: ...\n- write: ...\n- edit: ...\n" (18 共同 tools)     ← MATCH
Token 350- 360: "TOOLS.md does not control..."                                ← ❌ MISMATCH!
                (main 在这里还有 gateway/agents_list/... 7 个额外 tools)
```

**SGLang prefix match 在 token ~350 处断裂。**
之后 Tool Call Style, Safety, CLI, Skills (共 ~2,500 tokens) 内容完全一样，但 offset 不同，SGLang 无法利用。

### ContextPilot Reorder 后的效果

```
ContextPilot reorder 后的 main agent:
Token  0-  20: "You are a personal assistant ..."
Token  20- 520: "## Safety\n..."                    ← IDENTICAL (500 tokens)
Token 520-1320: "## CLI Quick Reference\n..."       ← IDENTICAL (800 tokens)
Token 1320-2120: "## Skills (mandatory)\n..."       ← IDENTICAL (800 tokens)
Token 2120-2420: "## Tool Call Style\n..."           ← IDENTICAL (300 tokens)
Token 2420-2570: "## Workspace\n..."                 ← IDENTICAL (150 tokens)
Token 2570-2620: "## Current Date & Time\n..."       ← IDENTICAL (50 tokens)
Token 2620-2770: "## Workspace Files\n..."           ← IDENTICAL (150 tokens)
--- DIVERGE POINT at ~2,770 tokens ---
Token 2770-3300: "## Tooling\n..." (25 tools)        ← DIFFERENT
Token 3300+:     ## Memory Recall, ...               ← FULL ONLY

ContextPilot reorder 后的 subagent:
Token  0-  20: "You are a personal assistant ..."
Token  20- 520: "## Safety\n..."                    ← IDENTICAL ✅
Token 520-1320: "## CLI Quick Reference\n..."       ← IDENTICAL ✅
Token 1320-2120: "## Skills (mandatory)\n..."       ← IDENTICAL ✅
Token 2120-2420: "## Tool Call Style\n..."           ← IDENTICAL ✅
Token 2420-2570: "## Workspace\n..."                 ← IDENTICAL ✅
Token 2570-2620: "## Current Date & Time\n..."       ← IDENTICAL ✅
Token 2620-2770: "## Workspace Files\n..."           ← IDENTICAL ✅
--- DIVERGE POINT at ~2,770 tokens ---
Token 2770-3100: "## Tooling\n..." (18 tools)        ← DIFFERENT
Token 3100+:     ## Subagent Context, ...            ← MINIMAL ONLY
```

**SGLang prefix cache hit: 2,770 tokens (vs 50 tokens without ContextPilot)**

### 整个 task 的 ContextPilot 收益汇总

| Call | 类型 | SGLang 单独 | + ContextPilot | 节省 tokens |
|------|------|-----------|---------------|------------|
| #1 | Main agent (cold) | 0 | 0 | 0 |
| #2 | Main→SubA | ~50 hit | ~2,770 hit | **2,720** |
| #3 | SubA→SubB | ~5,000 hit | ~5,000 hit | 0 (SGLang 已处理) |
| #4 | SubA→SubC | ~5,000 hit | ~5,000 hit | 0 |
| #5 | SubA→SubD | ~5,000 hit | ~5,000 hit | 0 |
| #6-9 | SubA turns 2-5 | SGLang hit | SGLang hit | 0 |
| #10-13 | SubB turns 2-5 | SGLang hit | SGLang hit | 0 |
| #14-17 | SubC turns 2-5 | SGLang hit | SGLang hit | 0 |
| #18-21 | SubD turns 2-5 | SGLang hit | SGLang hit | 0 |
| #22-23 | Main synthesis | SGLang hit | SGLang hit | tool result dedup 额外节省 |
| **Total** | | | | **~2,720 tokens** |

**关键: 首次 main→subagent 转换时的一次性 ~2,720 tokens 前缀命中。**

但更重要的是: 对于一个 5-turn chain (tasks_subagent.json 的 topic chain), 每个 turn 都会 spawn 3-4 个 subagents。首次 subagent 调用总是 miss，但 ContextPilot 让它 hit。

整个 topic chain (5 turns × 3-4 subagents × ~2,720 tokens):
- 5 turns × 1 首次 subagent miss × 2,720 tokens = **~13,600 tokens saved**
- 加上 cross-turn tool result dedup 和 SKILL.md dedup: **~20,000-30,000 tokens total**

---

## 需要 ContextPilot 新增的能力

### 1. System Prompt Section Reorder (核心功能)

在 `intercept_parser.py` 中新增:
- 用 `## ` markdown header 解析 system prompt 为 sections
- 识别 "byte-identical" sections (通过内容 hash)
- 把 identical sections 移到 prompt 最前面
- 把 divergent sections (Tooling, mode-specific) 移到后面
- 缓存 reorder 顺序，对后续 subagent 调用应用同样的排列

### 2. Cross-Session Section Cache

- 维护 session family 级别的 section hash 缓存
- 当新 session (subagent) 的 system prompt 包含与 parent session 相同的 sections 时，重排到匹配 parent 的 prefix
- 检测 session 关系: 通过 session key pattern (`agent:X:subagent:UUID`) 或 header

### 3. Tool List Reorder (可选优化)

- 在 `## Tooling` section 内部，把 main 和 subagent 共有的 tools 排到最前面
- 这进一步延伸 prefix match 深入到 Tooling section 内部
- 共有 18 tools 排前面，main-only 7 tools 排后面

---

## 新 Task 设计概要

文件: `tasks_subagent.json` (15 tasks, 3 topic chains × 5)

| Topic Chain | Subagents/Turn | ContextPilot 目标 |
|-------------|---------------|------------------|
| parallel-research (lang comparison) | 3/turn | section reorder, cross-turn dedup |
| multi-skill-parallel (news + analysis) | 3-4/turn | section reorder, multi-skill dedup, cross-turn dedup |
| infra-parallel-compare (cloud K8s) | 3-4/turn | section reorder, URL overlap dedup |

每个 turn 预期:
- 3-4 个 subagent 被 spawn
- 每个 subagent 做 4-6 个 LLM 调用
- 每个 subagent 需要读 summarize/SKILL.md (cross-session dedup)
- 跨 turn 搜索结果有大量 URL overlap

运行: `python scripts/run_bench.py --task-file subagent --dry-run`
