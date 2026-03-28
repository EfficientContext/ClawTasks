# Tasks

70 multi-turn tasks across 5 categories. Document analysis tasks (60) have 3-5 turns where a user asks an OpenClaw agent to read and analyze documents from `data/workspace/`. Coding tasks (10) have 4 turns where the agent iteratively modifies `codebase/user_service.py`, outputting the complete file each turn.

## [`commercial/`](commercial/) — 10 tasks

| Task | Turns | What the user asks |
|------|-------|--------------------|
| s01_commercial_terms | 5 | Read contracts/contract_delta_data.txt. Create a comparison table of all four contracts: value, dura... |
| s06_sla_comparison | 4 | Read contracts/contract_delta_data.txt. Compare SLA targets across all four and identify which vendo... |
| s13_payment_risk | 4 | Read contracts/contract_delta_data.txt. Compare financial risk across all four contracts. Do not sea... |
| s18_renewal_analysis | 4 | Read contracts/contract_delta_data.txt. Create a renewal timeline for all four with key dates. Do no... |
| s21_cost_analysis | 4 | What is our total vendor spend across all four contracts? Provide a cost breakdown. Do not search th... |
| s31_proposal_pricing | 4 | Which vendor offers the best value for money? Rank all four with reasoning. |
| s32_proposal_vs_contract | 4 | Across both vendors, what changed between proposal and contract? Any red flags? |
| s33_total_vendor_cost | 4 | Calculate total vendor spend across all four contracts including amendments. |
| s51_proposal_scope_compare | 4 | Are there any overlapping or redundant services across the four proposals? |
| s52_contract_amendment_cost | 4 | Read contracts/contract_delta_data.txt and contracts/amendment_delta_data_a1.txt. Complete the pictu... |

## [`legal/`](legal/) — 12 tasks

| Task | Turns | What the user asks |
|------|-------|--------------------|
| s02_liability_review | 4 | Write a risk assessment memo on liability gaps and recommended amendments. Do not search the web — o... |
| s04_ip_ownership | 4 | Are there any gaps in IP protection that could expose our company? Write recommendations. Do not sea... |
| s05_termination_rights | 4 | Read contracts/contract_delta_data.txt. Create a summary of termination rights across all four contr... |
| s08_dispute_resolution | 4 | Write a memo summarizing the dispute resolution framework across all four contracts. Do not search t... |
| s11_warranty_terms | 4 | Read contracts/contract_delta_data.txt. Compare warranty coverage across all four and identify weak ... |
| s12_confidentiality | 4 | Are there any gaps in confidentiality protection? Write a recommendation. Do not search the web — on... |
| s14_force_majeure | 4 | Write a summary of force majeure coverage across all four and recommend improvements. Do not search ... |
| s34_contract_nda_alignment | 4 | Write a recommendation on aligning NDAs with contracts across all vendors. |
| s35_proposal_vs_contract_legal | 4 | Which legal protections were strengthened from proposal to contract? Which were weakened? |
| s36_cross_contract_liability | 4 | Calculate our total maximum liability exposure across all four contracts. |
| s53_ip_across_proposals | 4 | Write a recommendation on standardizing IP terms across all vendor agreements. |
| s54_dispute_across_all | 5 | Write a memo on harmonizing dispute resolution across all vendor agreements and NDAs. |

## [`compliance/`](compliance/) — 18 tasks

| Task | Turns | What the user asks |
|------|-------|--------------------|
| s03_data_protection | 5 | Produce a data protection compliance scorecard for all four contracts. Do not search the web — only ... |
| s07_insurance_audit | 4 | Read contracts/contract_delta_data.txt. Summarize insurance requirements across all four and flag an... |
| s10_subcontracting | 4 | Summarize subcontracting risks across all four vendors. Do not search the web — only analyze the con... |
| s15_bcp_dr | 4 | Read contracts/contract_delta_data.txt. Compare BCP/DR across all four. Do not search the web — only... |
| s16_personnel_reqs | 4 | Read contracts/contract_delta_data.txt. Compare personnel requirements across all four. Do not searc... |
| s17_acceptance_testing | 4 | Are the acceptance testing timelines reasonable? Recommend improvements. Do not search the web — onl... |
| s19_compliance_scorecard | 5 | Produce a compliance scorecard rating each contract on 5 dimensions. Do not search the web — only an... |
| s22_audit_rights | 4 | Read contracts/contract_delta_data.txt. Compare audit rights across all four. Are they adequate? Do ... |
| s26_open_source | 4 | Summarize open-source risk across all four vendors. Do not search the web — only analyze the contrac... |
| s27_cross_border | 4 | Are we compliant with Singapore PDPA cross-border requirements across all four contracts? Do not sea... |
| s28_breach_response | 4 | Read contracts/contract_delta_data.txt. Compare breach response across all four and identify gaps. D... |
| s37_proposal_security_audit | 4 | Read contracts/proposal_deepmind_ai.txt and contracts/proposal_datastream_data.txt. Rate all four pr... |
| s38_contract_policy_gap | 4 | Produce a compliance gap matrix: contract vs policy requirement for each vendor. |
| s39_proposal_methodology | 4 | Which vendor's methodology is most rigorous? Rank all four. |
| s40_assessment_vs_proposal | 4 | Are vendors delivering what they proposed? Summarize gaps. |
| s41_cross_doc_security | 4 | Read contracts/master_service_agreement.txt. Does the MSA's security framework cover what the indivi... |
| s55_proposal_compliance_check | 4 | Produce a proposal compliance matrix covering all four vendors. |
| s56_contract_vs_proposal_security | 4 | Identify any security commitments that were in the proposals but dropped from the contracts. |

## [`strategic/`](strategic/) — 20 tasks

| Task | Turns | What the user asks |
|------|-------|--------------------|
| s09_change_management | 4 | Read contracts/contract_delta_data.txt. Compare change management across all four. Do not search the... |
| s20_vendor_comparison | 4 | Which vendor poses the highest risk? Explain with specific clause references. Do not search the web ... |
| s23_knowledge_transfer | 4 | Write a transition readiness assessment for all four vendors. Do not search the web — only analyze t... |
| s24_security_assessment | 4 | Read contracts/contract_delta_data.txt. Compare security posture across all four vendors. Do not sea... |
| s25_exit_strategy | 4 | Develop an exit strategy plan covering all four vendors with timeline and cost estimates. Do not sea... |
| s29_board_summary | 3 | Write a one-page executive summary of all four vendor contracts suitable for the board of directors.... |
| s30_negotiation_prep | 4 | Prepare a negotiation strategy document covering all four contracts with specific amendment proposal... |
| s42_proposal_team_comparison | 4 | Which vendor has the strongest team? Create a team comparison matrix. |
| s43_proposal_timeline | 4 | Are the proposed timelines realistic? Identify risks for each vendor. |
| s44_proposal_references | 3 | Which vendor has the most relevant references for our industry? Rank all four. |
| s45_vendor_selection_memo | 4 | Write a vendor selection recommendation memo for the CTO based on all proposals and contracts review... |
| s46_full_procurement_review | 4 | Write a comprehensive procurement review covering proposal → contract → delivery for both vendors. |
| s47_board_vendor_brief | 4 | Prepare an updated board briefing on vendor status incorporating proposals, contracts, and board fee... |
| s48_contract_consolidation | 4 | Write a recommendation for contract consolidation — which clauses should move to the MSA and which s... |
| s49_renewal_negotiation | 5 | Prepare a negotiation strategy for renewing both the cloud and AI vendor contracts. |
| s50_annual_portfolio | 5 | Write a complete annual vendor portfolio review covering all four vendors: contracts, performance, a... |
| s57_proposal_risk_assessment | 4 | Write a consolidated risk assessment comparing vendor-proposed mitigations with board-identified ris... |
| s58_full_vendor_lifecycle | 5 | Write a full vendor lifecycle report for Security Firm D: proposal → contract → amendment → performance. |
| s59_vendor_capability_map | 4 | Write a vendor capability matrix and identify areas where we need additional vendor coverage. |
| s60_executive_dashboard | 4 | Create an executive dashboard showing: contract status, spend, SLA compliance, and overall health fo... |

## [`coding/`](coding/) — 10 tasks

Multi-turn coding tasks where the agent reads `codebase/user_service.py` (290 lines) and iteratively adds features, outputting the complete updated file each turn. Designed to benchmark assistant code block deduplication — each turn's output is ~90% identical to the previous turn.

| Task | Turns | What the user asks |
|------|-------|--------------------|
| s61_add_validation | 4 | Read user_service.py. Add email validation, password strength check, and rate limiting to authenticate. |
| s62_add_logging | 4 | Add structured logging, error logging with stack traces, and audit logging with actor_id. |
| s63_add_pagination | 4 | Change list_users to cursor-based pagination, add sorting, and date range filtering. |
| s64_add_batch_ops | 4 | Add bulk_create_users, bulk_deactivate, and export_users (CSV) methods. |
| s65_refactor_cache | 4 | Refactor to LRU cache (max 1000), add hit/miss metrics, add cache_warm method. |
| s66_add_permissions | 4 | Add permission system with roles, require_permission decorator, and enforce on delete/update. |
| s67_add_hooks | 4 | Add pre/post hooks for CRUD, welcome email hook, and admin notification hook. |
| s68_add_soft_delete | 4 | Change to soft delete, add restore_user, and purge_deleted (30-day retention). |
| s69_add_sessions | 4 | Add session management: create_session, validate/revoke_session, revoke_all_sessions. |
| s70_add_api_keys | 4 | Add API key management: generate, validate, revoke, and list API keys with scopes. |

### Benchmark results (SGLang, Qwen3-4B-Instruct-2507, 1x RTX PRO 6000 Blackwell)

Turn 3 (last turn), 8 valid scenarios:

| Metric | Direct | ContextPilot | Avg Improvement |
|--------|--------|-------------|-----------------|
| Prompt tokens | ~41K | ~34K | **-16.2%** |
| Wall time | ~143s | ~126s | **-12.4%** |
| Accuracy | 8/8 OK | 8/8 OK | — |
