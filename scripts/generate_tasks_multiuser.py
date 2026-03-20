#!/usr/bin/env python3
"""
Generate multi-user document search benchmark tasks.

4 users × 5 questions = 20 tasks. Each user focuses on a different
biology/zoology cluster, but queries overlap on hub documents
(thermoregulation, conservation, genus overviews), creating the
prefix overlap that ContextPilot optimizes for KV cache reuse.
"""

import json
import pathlib
import hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
DOCS_DIR = ROOT / "datasets" / "multiuser-docsearch" / "documents"

TASK_TEMPLATES = [

    # ══════════════════════════════════════════════════════════════════════
    # User A — Monitor Lizards
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "multiuser-docsearch-a1",
        "topic": "multiuser-docsearch",
        "user_id": "user-a",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use memory_search to find information about Komodo dragon hunting strategies and venom mechanisms. Summarize how Komodo dragons use venom during predation, including Bryan Fry's 2009 discovery and the shift from the bacterial infection hypothesis.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["komodo-dragon.md", "monitor-venom.md", "varanus-genus.md"],
    },
    {
        "name": "multiuser-docsearch-a2",
        "topic": "multiuser-docsearch",
        "user_id": "user-a",
        "chain_position": 2,
        "depends_on": "multiuser-docsearch-a1",
        "description": "Use memory_search to find information about water monitor lizards and their adaptation to urban environments. Describe how Varanus salvator thrives in cities like Bangkok and Singapore, and discuss what this reveals about monitor lizard intelligence.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["water-monitor.md", "varanus-genus.md", "reptile-intelligence.md"],
    },
    {
        "name": "multiuser-docsearch-a3",
        "topic": "multiuser-docsearch",
        "user_id": "user-a",
        "chain_position": 3,
        "depends_on": "multiuser-docsearch-a1",
        "description": "Use memory_search to find information about thermoregulation in monitor lizards. Compare how the perentie survives extreme desert heat in Australia versus how tropical monitors regulate their temperature.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["perentie.md", "varanus-genus.md", "reptile-thermoregulation.md"],
    },
    {
        "name": "multiuser-docsearch-a4",
        "topic": "multiuser-docsearch",
        "user_id": "user-a",
        "chain_position": 4,
        "depends_on": "multiuser-docsearch-a1",
        "description": "Use memory_search to find information about the Toxicofera hypothesis and how it relates to venom in monitor lizards. Explain what Toxicofera means for our understanding of venom evolution across squamate reptiles.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["monitor-venom.md", "toxicofera.md", "varanus-genus.md", "squamata-order.md"],
    },
    {
        "name": "multiuser-docsearch-a5",
        "topic": "multiuser-docsearch",
        "user_id": "user-a",
        "chain_position": 5,
        "depends_on": "multiuser-docsearch-a1",
        "description": "Use memory_search to find information about conservation challenges facing large monitor lizards. Discuss the conservation status of Komodo dragons and perenties, including threats and protection measures.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["komodo-dragon.md", "perentie.md", "reptile-conservation.md", "varanus-genus.md"],
    },

    # ══════════════════════════════════════════════════════════════════════
    # User B — Crocodilians
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "multiuser-docsearch-b1",
        "topic": "multiuser-docsearch",
        "user_id": "user-b",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use memory_search to find information about saltwater crocodile distribution and bite force. Summarize what makes C. porosus the largest living reptile and why it has the strongest bite force of any animal.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["saltwater-crocodile.md", "crocodilia-order.md"],
    },
    {
        "name": "multiuser-docsearch-b2",
        "topic": "multiuser-docsearch",
        "user_id": "user-b",
        "chain_position": 2,
        "depends_on": "multiuser-docsearch-b1",
        "description": "Use memory_search to find information about American alligator habitat engineering. Explain the concept of 'alligator holes' and how A. mississippiensis acts as a keystone species, including its Endangered Species Act recovery story.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["american-alligator.md", "crocodilia-order.md", "reptile-conservation.md"],
    },
    {
        "name": "multiuser-docsearch-b3",
        "topic": "multiuser-docsearch",
        "user_id": "user-b",
        "chain_position": 3,
        "depends_on": "multiuser-docsearch-b1",
        "description": "Use memory_search to find information about the gharial and why it is critically endangered. Discuss the threats facing Gavialis gangeticus in the Ganges basin and current conservation efforts.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["gharial.md", "crocodilia-order.md", "reptile-conservation.md"],
    },
    {
        "name": "multiuser-docsearch-b4",
        "topic": "multiuser-docsearch",
        "user_id": "user-b",
        "chain_position": 4,
        "depends_on": "multiuser-docsearch-b1",
        "description": "Use memory_search to find information about thermoregulation in crocodilians. Describe the behavioral strategies crocodilians use to regulate body temperature, including basking, gaping, and shuttling between water and land.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["crocodilia-order.md", "reptile-thermoregulation.md", "saltwater-crocodile.md"],
    },
    {
        "name": "multiuser-docsearch-b5",
        "topic": "multiuser-docsearch",
        "user_id": "user-b",
        "chain_position": 5,
        "depends_on": "multiuser-docsearch-b1",
        "description": "Use memory_search to find information about crocodilian intelligence and parental care. Discuss tool use, cooperative hunting, and the sophisticated parental care behaviors observed in crocodilians.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["crocodilia-order.md", "reptile-intelligence.md", "american-alligator.md"],
    },

    # ══════════════════════════════════════════════════════════════════════
    # User C — Sea Turtles / Marine Reptiles
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "multiuser-docsearch-c1",
        "topic": "multiuser-docsearch",
        "user_id": "user-c",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use memory_search to find information about leatherback sea turtle migration and deep diving abilities. Summarize the extraordinary physiology that allows D. coriacea to dive over 1,000 meters and migrate across entire ocean basins.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["leatherback-turtle.md", "sea-turtle-overview.md", "reptile-thermoregulation.md"],
    },
    {
        "name": "multiuser-docsearch-c2",
        "topic": "multiuser-docsearch",
        "user_id": "user-c",
        "chain_position": 2,
        "depends_on": "multiuser-docsearch-c1",
        "description": "Use memory_search to find information about green sea turtle herbivory and seagrass ecology. Explain how C. mydas is unique among sea turtles as an herbivore and its role in maintaining healthy seagrass ecosystems.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["green-sea-turtle.md", "sea-turtle-overview.md"],
    },
    {
        "name": "multiuser-docsearch-c3",
        "topic": "multiuser-docsearch",
        "user_id": "user-c",
        "chain_position": 3,
        "depends_on": "multiuser-docsearch-c1",
        "description": "Use memory_search to find information about threats facing sea turtles globally. Provide a comprehensive overview of conservation challenges including bycatch, plastic pollution, climate change impacts on sex ratios, and nesting habitat loss.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["sea-turtle-overview.md", "reptile-conservation.md", "green-sea-turtle.md", "leatherback-turtle.md"],
    },
    {
        "name": "multiuser-docsearch-c4",
        "topic": "multiuser-docsearch",
        "user_id": "user-c",
        "chain_position": 4,
        "depends_on": "multiuser-docsearch-c1",
        "description": "Use memory_search to find information about marine iguana adaptations. Describe how Amblyrhynchus cristatus evolved to be the only ocean-going lizard, including its salt glands, marine foraging behavior, and thermoregulation challenges.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["marine-iguana.md", "squamata-order.md", "reptile-thermoregulation.md"],
    },
    {
        "name": "multiuser-docsearch-c5",
        "topic": "multiuser-docsearch",
        "user_id": "user-c",
        "chain_position": 5,
        "depends_on": "multiuser-docsearch-c1",
        "description": "Use memory_search to find information about thermoregulation in marine reptiles. Compare how leatherback sea turtles use gigantothermy versus how marine iguanas cope with cold ocean temperatures through basking behavior.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["leatherback-turtle.md", "marine-iguana.md", "reptile-thermoregulation.md", "sea-turtle-overview.md"],
    },

    # ══════════════════════════════════════════════════════════════════════
    # User D — Comparative Biology
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "multiuser-docsearch-d1",
        "topic": "multiuser-docsearch",
        "user_id": "user-d",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use memory_search to find information about thermoregulation strategies across different reptile groups. Compare how monitors, crocodilians, and sea turtles approach the challenge of temperature regulation as ectotherms.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["reptile-thermoregulation.md", "crocodilia-order.md", "sea-turtle-overview.md", "varanus-genus.md"],
    },
    {
        "name": "multiuser-docsearch-d2",
        "topic": "multiuser-docsearch",
        "user_id": "user-d",
        "chain_position": 2,
        "depends_on": "multiuser-docsearch-d1",
        "description": "Use memory_search to find information about Squamata diversity and phylogeny. Explain the scale of squamate diversity with 11,000+ species and how modern molecular phylogenetics has reshaped our understanding of relationships within this order.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["squamata-order.md", "toxicofera.md", "varanus-genus.md"],
    },
    {
        "name": "multiuser-docsearch-d3",
        "topic": "multiuser-docsearch",
        "user_id": "user-d",
        "chain_position": 3,
        "depends_on": "multiuser-docsearch-d1",
        "description": "Use memory_search to find information about intelligence and cognition in reptiles. Compare cognitive abilities across monitor lizards and crocodilians, including evidence for counting, tool use, and social learning.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["reptile-intelligence.md", "varanus-genus.md", "crocodilia-order.md"],
    },
    {
        "name": "multiuser-docsearch-d4",
        "topic": "multiuser-docsearch",
        "user_id": "user-d",
        "chain_position": 4,
        "depends_on": "multiuser-docsearch-d1",
        "description": "Use memory_search to find information about global reptile conservation priorities. Identify the most critically endangered reptile species and discuss the major threats and conservation strategies across crocodilians, sea turtles, and monitor lizards.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["reptile-conservation.md", "gharial.md", "sea-turtle-overview.md", "komodo-dragon.md"],
    },
    {
        "name": "multiuser-docsearch-d5",
        "topic": "multiuser-docsearch",
        "user_id": "user-d",
        "chain_position": 5,
        "depends_on": "multiuser-docsearch-d1",
        "description": "Use memory_search to find information about venom evolution in the Toxicofera clade. Explain the evidence for a single origin of venom in squamate reptiles and how this hypothesis connects monitors, iguanians, and snakes.",
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 4,
        "skills_required": ["memory_search"],
        "skills_info": [{"slug": "memory_search", "displayName": "Memory Search", "category": "memory"}],
        "expected_documents": ["toxicofera.md", "monitor-venom.md", "squamata-order.md", "varanus-genus.md"],
    },
]


def generate_task_id(task: dict) -> str:
    raw = f"{task['name']}-{'-'.join(task['skills_required'])}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_task(template: dict) -> dict:
    task_id = generate_task_id(template)
    return {
        "id": task_id,
        "name": template["name"],
        "topic": template["topic"],
        "user_id": template["user_id"],
        "chain_position": template["chain_position"],
        "depends_on": template["depends_on"],
        "description": template["description"],
        "category": template["category"],
        "difficulty": template["difficulty"],
        "expected_steps": template["expected_steps"],
        "skills_required": template["skills_required"],
        "skills_info": template["skills_info"],
        "num_skills": len(template["skills_required"]),
        "expected_documents": template["expected_documents"],
    }


def main():
    # Ensure tasks dir exists
    TASKS_DIR.mkdir(exist_ok=True)

    # Remove old multiuser tasks only
    for f in TASKS_DIR.glob("multiuser-docsearch-*.json"):
        f.unlink()

    all_tasks = []
    for tmpl in TASK_TEMPLATES:
        task = build_task(tmpl)
        all_tasks.append(task)
        (TASKS_DIR / f"{task['name']}.json").write_text(
            json.dumps(task, indent=2, ensure_ascii=False))

    (ROOT / "tasks_multiuser.json").write_text(
        json.dumps(all_tasks, indent=2, ensure_ascii=False))

    # Summary
    users = {}
    for t in all_tasks:
        users.setdefault(t["user_id"], []).append(t)

    print(f"Generated {len(all_tasks)} tasks, {len(users)} users x 5 tasks\n")
    print("User task chains:")
    for user_id, tasks in sorted(users.items()):
        seed = [t for t in tasks if t["chain_position"] == 1][0]
        deps = [t for t in tasks if t["chain_position"] > 1]
        print(f"  {user_id}: {seed['name']} -> {len(deps)} follow-ups")

    # Document overlap analysis
    from collections import Counter
    doc_counter = Counter()
    doc_to_users = {}
    for t in all_tasks:
        for doc in t["expected_documents"]:
            doc_counter[doc] += 1
            doc_to_users.setdefault(doc, set()).add(t["user_id"])

    print("\nDocument retrieval frequency:")
    for doc, count in doc_counter.most_common():
        users_str = ", ".join(sorted(doc_to_users[doc]))
        print(f"  {doc:35s} {count:2d} queries  ({users_str})")

    hub_docs = [doc for doc, users in doc_to_users.items() if len(users) >= 2]
    print(f"\nHub documents (shared by 2+ users): {len(hub_docs)}")
    for doc in sorted(hub_docs):
        print(f"  {doc} -> {sorted(doc_to_users[doc])}")

    # Verify documents exist
    if DOCS_DIR.exists():
        existing = {f.name for f in DOCS_DIR.glob("*.md")}
        referenced = set(doc_counter.keys())
        missing = referenced - existing
        if missing:
            print(f"\nWARNING: Missing documents: {sorted(missing)}")
        else:
            print(f"\nAll {len(referenced)} referenced documents exist in {DOCS_DIR}")
    else:
        print(f"\nWARNING: Documents directory not found: {DOCS_DIR}")

    print(f"\nOutput: tasks_multiuser.json + {len(all_tasks)} files in tasks/")


if __name__ == "__main__":
    main()
