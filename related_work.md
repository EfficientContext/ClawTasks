# Multi-Agent Combination Benchmarks (2025 H2 - 2026)

Related work survey: benchmarks that evaluate how multiple LLM agents (or skills/tools) are combined, coordinated, and orchestrated together.

---

## 1. MultiAgentBench (ACL 2025, July)

- **Paper**: [MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents](https://arxiv.org/abs/2503.01935)
- **Code**: https://github.com/ulab-uiuc/MARBLE

**Motivation**: 现有benchmark大多评估单个agent的能力，缺乏对multi-agent系统中协作与竞争动态的系统性评估。需要一个能衡量不同coordination protocol和communication topology下multi-agent表现的benchmark。

**Metrics**:
- Task completion score (milestone-based KPIs)
- Milestone achievement rate
- Planning efficiency
- Token consumption

**Data**: 多种交互式场景（diverse interactive scenarios），涵盖collaboration和competition两类设置。

**Insights**:
- Graph-mesh topology在task score、planning efficiency上表现最优，优于hierarchical和chain结构
- GPT-4o-mini在平均task score上最高
- Cognitive planning提升milestone achievement rate约3%
- 不同coordination protocol（star, chain, tree, graph）对性能影响显著

---

## 2. MedAgentBoard (NeurIPS 2025, Dec)

- **Paper**: [MedAgentBoard: Benchmarking Multi-Agent Collaboration with Conventional Methods for Diverse Medical Tasks](https://arxiv.org/abs/2505.12371)
- **Code**: https://github.com/yhzhu99/MedAgentBoard

**Motivation**: 在医疗场景中，缺乏对multi-agent collaboration、single LLM、以及传统方法进行系统性公平对比的benchmark。需要回答"multi-agent是否真的优于single agent或传统方法"这一关键问题。

**Metrics**:
- 各任务类型的标准评估指标（accuracy, F1, BLEU等）
- Task completeness（尤其在clinical workflow automation中）

**Data**: 4类医疗任务：
1. Medical (visual) question answering
2. Lay summary generation
3. Structured EHR predictive modeling
4. Clinical workflow automation
- 数据类型涵盖text, medical images, structured EHR data

**Insights**:
- Multi-agent框架在clinical workflow automation的task completeness上有优势，但**不一致地优于**advanced single LLM
- 在textual medical QA上，advanced single LLM（配合好的prompting）可达SOTA，multi-agent并无明显优势
- 专门fine-tuned的传统VLM在medical VQA上仍然dominant
- **Multi-agent并非万能**：需要根据具体任务特点选择single vs. multi-agent方案

---

## 3. AgentArch (Sep 2025)

- **Paper**: [AgentArch: A Comprehensive Benchmark to Evaluate Agent Architectures in Enterprise](https://arxiv.org/abs/2509.10769)
- **Code**: https://github.com/ServiceNow/AgentArch

**Motivation**: 企业场景缺乏对不同agentic architecture configuration的系统性评估。现有方案普遍采用one-size-fits-all的架构，但不同model可能需要不同的最优配置。

**Metrics**:
- Task success rate
- 在两个企业场景下的表现（simple task vs. complex task）

**Data**: 2个企业场景（18种架构配置 × 6种模型）：
1. **Time-Off Request (TO)**: 结构化、规则驱动流程（8 tools, 3 agents）
2. **Customer Request Routing (CR)**: 复杂分诊场景（31 tools, 9 agents）

**Insights**:
- 最优架构**因model而异**（model-specific architectural preferences），否定了one-size-fits-all假设
- Function-calling配置通常优于ReAct
- Thinking tools在简单任务上有帮助，在复杂任务上不一定
- 最高成功率仅35.3%（复杂任务）和70.8%（简单任务），暴露了当前agent系统在企业场景的不足
- **No single architecture dominates** across models or tasks

---

## 4. Beyond the Strongest LLM (Sep 2025)

- **Paper**: [Beyond the Strongest LLM: Multi-Turn Multi-Agent Orchestration vs. Single LLMs on Benchmarks](https://arxiv.org/abs/2509.23537)

**Motivation**: 探究多个异构LLM通过multi-turn投票/讨论的orchestration方式，能否超越单一最强LLM。这直接回答了"组合多个agent是否有收益"这一核心问题。

**Metrics**:
- Accuracy on GPQA-Diamond, IFEval, MuSR
- Self-voting rate
- Convergence speed
- Herding effect

**Data**: 4个LLM（Gemini 2.5 Pro, GPT-5, Grok 4, Claude Sonnet 4）在3个benchmark上的orchestration实验：
1. GPQA-Diamond（科学推理）
2. IFEval（指令跟随）
3. MuSR（多步推理）

**Insights**:
- Orchestration **matches or exceeds** the strongest single model（87.4% on GPQA-Diamond, 88.0% on IFEval, 68.3% on MuSR）
- 显著优于较弱的individual model
- Revealing authorship increases self-voting和ties
- Showing ongoing votes amplifies **herding effect**：加速convergence但可能导致premature consensus
- 异构LLM组合通过多轮协商可以达到甚至超越最强单一模型

---

## 5. CLEAR Framework (Nov 2025)

- **Paper**: [Beyond Accuracy: A Multi-Dimensional Framework for Evaluating Enterprise Agentic AI Systems](https://arxiv.org/abs/2511.14136)

**Motivation**: 现有benchmark过度关注accuracy，忽视了企业部署中critical的其他维度（cost, latency, reliability等）。仅优化accuracy会导致suboptimal deployment。

**Metrics**: 5个维度
1. **Cost**: API token消耗、inference成本、infra开销（USD/task）
2. **Latency**: 端到端完成时间、SLA compliance rate（客服3s, 代码生成30s）
3. **Efficacy**: 任务完成质量
4. **Assurance**: 安全性与策略合规
5. **Reliability**: 多次运行一致性

**Data**: 6种leading agents × 300 enterprise tasks

**Insights**:
- Accuracy最高的agent **cost高4.4-10.8x**于Pareto-efficient alternatives
- 类似precision的agent之间cost差异可达**50x**
- Agent性能从单次60%降到8次一致性25%，暴露严重的**reliability问题**
- 缺少security, latency, policy compliance的评估是现有benchmark的三个fundamental limitations
- 需要Pareto-efficient多维评估而非单一accuracy排名

---

## 6. MAESTRO (Jan 2026)

- **Paper**: [MAESTRO: Multi-Agent Evaluation Suite for Testing, Reliability, and Observability](https://arxiv.org/abs/2601.00481)

**Motivation**: 现有MAS评估缺乏standardized配置、跨框架对比、以及execution-level的observability。不同框架的MAS在结构、cost、reliability上差异巨大但难以直接比较。

**Metrics**:
- Latency
- Cost (per-run)
- Failure rate
- Run-to-run variance
- Cost-latency-accuracy trade-off

**Data**: 12个representative MAS，跨多个agentic框架和interaction pattern，进行controlled experiments across repeated runs, backend models, tool configurations。

**Insights**:
- MAS执行可以**structurally stable yet temporally variable**，导致显著的run-to-run variance
- **MAS architecture是resource profiles、reproducibility、cost-latency-accuracy trade-off的dominant driver**，往往比更换backend model或tool settings影响更大
- 框架选择比模型选择更重要这一发现对实际部署有重大指导意义

---

## 7. SkillsBench (Feb 2026)

- **Paper**: [SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks](https://arxiv.org/abs/2602.12670)
- **Website**: https://www.skillsbench.ai/

**Motivation**: Agent skills（预定义的procedural knowledge/instructions）被广泛使用，但缺乏系统性benchmark评估skills augmentation的实际效果。核心问题：给agent提供skills是否真的有帮助？什么样的skill设计最有效？

**Metrics**:
- Pass rate（在3种条件下：no skills, curated skills, self-generated skills）
- Per-domain delta

**Data**: 86 tasks × 11 domains × 7 agent-model configurations = 7,308 trajectories。3种实验条件：
1. No Skills
2. Curated Skills
3. Self-generated Skills

**Insights**:
- Curated Skills平均提升pass rate **+16.2pp**，但效果差异巨大（SE仅+4.5pp，Healthcare +51.9pp）
- 16/84 tasks出现**negative delta**（skills反而有害）
- **Self-generated Skills平均无收益**：模型无法可靠地自己生成有用的procedural knowledge
- Focused skills（2-3 modules）优于comprehensive documentation
- **Smaller models + skills可以match larger models without skills**
- 与ClawBench高度相关：直接回答了multi-skill combination的价值问题

---

## 8. AgentSkillOS (Mar 2026)

- **Paper**: [Organizing, Orchestrating, and Benchmarking Agent Skills at Ecosystem Scale](https://arxiv.org/abs/2603.02176)
- **Code**: https://github.com/ynulihao/AgentSkillOS

**Motivation**: 随着open skill ecosystem规模增长（90,000+ skills），如何高效组织、发现、编排多个skills成为关键挑战。现有方法缺乏principled framework来处理大规模skill选择和multi-skill orchestration。

**Metrics**:
- Task output quality（LLM-based pairwise evaluation）
- Bradley-Terry model unified quality scores
- Skill retrieval precision

**Data**: 30 artifact-rich tasks × 5 categories：
1. Data computation
2. Document creation
3. Motion video
4. Visual design
5. Web interaction

**Insights**:
- Capability-tree-based organization实现高效hierarchical skill discovery
- DAG-based multi-skill orchestration优于flat skill selection
- 两阶段（Manage Skills → Solve Tasks）的pipeline设计有效
- 与ClawBench直接相关：同样关注multi-skill composition和orchestration

---

## 9. EmCoop (Mar 2026)

- **Paper**: [EmCoop: A Framework and Benchmark for Embodied Cooperation Among LLM Agents](https://arxiv.org/abs/2603.00349)
- **Website**: https://happyeureka.github.io/emcoop

**Motivation**: 现有embodied agent benchmark要么只关注single-agent，要么是simplified multi-agent设置，无法capture realistic cooperation dynamics。需要一个能诊断collaboration quality和failure modes的benchmark。

**Metrics**:
- Process-level metrics（不仅评估final task success，还诊断collaboration过程中的quality和failure modes）
- Generalizable across environments

**Data**: 2个embodied环境，支持：
- Arbitrary numbers of agents
- Diverse communication topologies

**Insights**:
- 将high-level cognitive layer（LLM symbolic reasoning, planning, communication）与low-level embodied layer（primitive actions under physical/temporal constraints）显式分离
- 整个cooperation过程transparent, interpretable, human-readable
- Process-level evaluation比final-outcome evaluation更能揭示collaboration问题

---

## 10. Silo-Bench (Mar 2026)

- **Paper**: [Silo-Bench: A Scalable Environment for Evaluating Distributed Coordination in Multi-Agent LLM Systems](https://arxiv.org/abs/2603.01045)

**Motivation**: 当多个LLM agent分布在不同系统中时，信息是siloed的，coordination和communication成为核心挑战。现有benchmark未充分评估这种distributed setting下的agent协调能力。

**Metrics**:
- 评估distributed coordination能力（具体metrics待确认）

**Data**: Scalable environment设计，支持多种distributed coordination场景

**Insights**:
- 关注information silo问题：agent间信息不对称时的协调挑战
- Scalable设计允许评估不同规模的multi-agent系统

---

---

# Performance-Focused Multi-Agent Benchmarks (2025 H2 - 2026)

---

## 11. Efficient Agents (Jul 2025)

- **Paper**: [Efficient Agents: Building Effective Agents While Reducing Cost](https://arxiv.org/abs/2508.02694)
- **Code**: https://github.com/OPPO-PersonalAI/OAgents

**Motivation**: 现有agent系统每个task需要数百次API调用，经济上不可持续，成为real-world adoption的根本瓶颈。需要系统性研究efficiency-effectiveness trade-off：多少复杂度是真正必要的？何时额外模块的收益开始递减？

**Metrics**:
- **Cost-of-pass**: 综合衡量性能与效率的核心指标（达到特定成功率所需的成本）
- Task accuracy
- API call count / token consumption

**Data**: 多个agentic benchmark上的系统性实验

**Insights**:
- 首个系统性研究agent系统中efficiency-effectiveness trade-off的工作
- 许多agentic tasks实际上**不需要复杂的multi-agent架构**
- 额外模块存在明显的**diminishing returns**
- 为"什么时候该用multi-agent、什么时候single-agent足够"提供了量化依据

---

## 12. Towards a Science of Scaling Agent Systems (Dec 2025)

- **Paper**: [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296)
- **Affiliation**: MIT Media Lab

**Motivation**: 业界普遍假设增加agent数量能单调提升性能，但缺乏量化的scaling principles。需要回答：multi-agent scaling何时有效、何时失效？

**Metrics**:
- Coordination efficiency
- Coordination overhead
- Error amplification
- Redundancy
- 预测模型 R² = 0.513（cross-validated）

**Data**: 4个benchmark × 5种架构 × 3个LLM families = **180种controlled configurations**
- Benchmarks: Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench
- Architectures: Single, Independent, Centralized, Decentralized, Hybrid
- 标准化tools和token budgets

**Insights**:
- **推翻了"增加agent数量必然提升性能"的普遍假设**
- Centralized和Hybrid coordination的scaling efficiency通常最优
- Collaborative agentic structures比individual scaling更能amplify capability gains
- 效果**强烈依赖domain**：parallelizable tasks有收益，sequential tasks反而有成本
- 提出了可预测MAS性能的量化scaling law

---

## 13. MAFBench (Feb 2026)

- **Paper**: [Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis](https://arxiv.org/abs/2602.03128)

**Motivation**: Multi-agent框架（如LangGraph, AutoGen, CrewAI等）的架构差异对系统性能的影响poorly understood。不同框架的选择可能导致数量级的性能差异，但缺乏统一的对比方法。

**Metrics**:
- Latency（端到端延迟）
- Throughput
- Planning accuracy
- Coordination success rate
- Scalability

**Data**: MAFBench统一评估套件，集成多个existing benchmarks于standardized execution pipeline，对多个widely-used frameworks进行controlled empirical study。

**Insights**:
- **框架选择可导致latency差异超过100x**
- Planning accuracy可因框架不同降低**最多30%**
- Coordination success rate可从**>90%降至<30%**
- 提出了concrete architectural design principles和framework selection guidance
- 结论与MAESTRO一致：**架构/框架选择比模型选择更重要**

---

## 14. General AgentBench - Test-Time Scaling (Feb 2026)

- **Paper**: [Benchmark Test-Time Scaling of General LLM Agents](https://arxiv.org/abs/2602.18998)

**Motivation**: Test-time scaling（推理时增加计算资源）在单一任务上效果显著，但在general-purpose multi-domain agent场景下是否同样有效？现有domain-specific评估可能高估了agent的泛化能力。

**Metrics**:
- Task success rate across domains
- Sequential scaling效果（延长interaction history）
- Parallel scaling效果（sampling K candidate trajectories）

**Data**: General AgentBench统一框架，跨search, coding, reasoning, tool-use四个domain评估10个leading LLM agents。两种scaling策略：
1. Sequential scaling: 延长交互历史以支持持续推理、反思、探索
2. Parallel scaling: 独立采样K条候选轨迹并选择最优

**Insights**:
- 从domain-specific到general-agent设置，性能出现**substantial degradation**
- Sequential scaling受限于**context ceiling**（上下文窗口饱和后收益消失）
- Parallel scaling受限于**verification gap**（缺乏可靠的trajectory选择机制）
- **两种scaling策略在实践中都未能有效提升性能**
- 对"通过增加compute来提升agent性能"的策略提出了根本性质疑

---

## Summary Table

| # | Benchmark | Date | Focus | Key Question |
|---|-----------|------|-------|-------------|
| 1 | MultiAgentBench | ACL'25 Jul | Coordination topology | Which topology (star/chain/tree/graph) works best? |
| 2 | MedAgentBoard | NeurIPS'25 Dec | Medical multi-agent vs single | Is multi-agent better than single-agent in medical tasks? |
| 3 | AgentArch | Sep 2025 | Enterprise architecture | Does one architecture fit all models? |
| 4 | Beyond Strongest LLM | Sep 2025 | Heterogeneous LLM voting | Can combining LLMs beat the best single one? |
| 5 | CLEAR | Nov 2025 | Multi-dimensional eval | Is accuracy enough for enterprise deployment? |
| 6 | MAESTRO | Jan 2026 | Observability & reliability | How stable are MAS across runs? |
| 7 | SkillsBench | Feb 2026 | Skills augmentation | Do agent skills actually help? |
| 8 | AgentSkillOS | Mar 2026 | Skill orchestration at scale | How to organize & orchestrate 90K+ skills? |
| 9 | EmCoop | Mar 2026 | Embodied cooperation | How to diagnose cooperation quality? |
| 10 | Silo-Bench | Mar 2026 | Distributed coordination | How to coordinate with siloed information? |
| 11 | Efficient Agents | Jul 2025 | Cost-effectiveness | How much agent complexity is actually needed? |
| 12 | Scaling Agent Systems | Dec 2025 | Scaling laws | Does more agents = better performance? |
| 13 | MAFBench | Feb 2026 | Framework-level perf | How much does framework choice affect performance? |
| 14 | General AgentBench | Feb 2026 | Test-time scaling | Does more compute help general agents? |

## Relevance to ClawBench

ClawBench的核心设计是multi-skill combination（每个task需要4-5个skills协同工作）。以上benchmark从不同角度回答了相关问题：

1. **Combination value**: SkillsBench证实curated skills有+16.2pp的提升，但self-generated skills无效；Beyond the Strongest LLM证实heterogeneous agent组合可match/exceed最强单一agent
2. **Topology/Architecture matters**: MultiAgentBench发现graph topology最优；AgentArch发现最优架构因model而异
3. **Beyond accuracy**: CLEAR和MAESTRO强调cost, latency, reliability等维度；MAESTRO发现架构选择比模型选择更重要
4. **Skill organization**: AgentSkillOS的capability-tree + DAG pipeline与ClawBench的skill overlap设计互补
5. **Cautionary findings**: MedAgentBoard发现multi-agent并非总是优于single-agent；SkillsBench发现skills可能有害（16/84 tasks negative delta）
6. **Performance/Scaling**: Efficient Agents发现许多task不需要复杂multi-agent架构（diminishing returns）；Scaling Agent Systems推翻了"more agents = better"的假设；MAFBench发现框架选择可导致100x latency差异；General AgentBench发现test-time scaling两种策略在通用场景均未能有效提升性能
