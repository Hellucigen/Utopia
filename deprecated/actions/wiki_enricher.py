# wiki_enricher.py (完整修改版，假设原代码结构)
# wiki_enricher.py
# Enrich knowledge graph nodes with triples extracted from Wikipedia summaries via Ollama.

import requests
import json
import time
import re
import uuid
from typing import Dict
from Knowledge_Graph import Node, Edge, KnowledgeGraph
from utils import normalize_concept, generate_node_id  # 新导入共享函数

# === Configuration ===
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi4"
ENRICH_DELAY = 1.5
MAX_TRIPLES = 30
MAX_RETRIES = 2


# ==========================================================
# 1️⃣ Extract triples using Ollama
# ==========================================================
def extract_triples_with_ollama(text: str) -> list:
    """
    Extract semantic triples from text using Ollama.
    Returns a list of [head, relation, tail].
    """

    prompt = (
        "You are a knowledge graph builder. Extract semantic triples from the text.\n"
        "Rules:\n"
        "- Each triple: [head, relation, tail]\n"
        "- head and tail MUST be short, atomic concepts (1–3 words max)\n"
        "- NO full sentences\n"
        "- Normalize to singular nouns\n"
        "- Use uppercase relations with underscores\n"
        "- Output ONLY raw JSON list of lists\n\n"
        f"Text: {text}\n\nTriples:"
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3}
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=200)
        if resp.status_code != 200:
            print(f"⚠️ Ollama API error: {resp.status_code}")
            return []

        result = resp.json().get("response", "").strip()

        # Remove markdown fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', result, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned).strip()

        # Extract first JSON array
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        else:
            print("⚠️ No JSON array found in LLM output.")
            return []

        triples = json.loads(cleaned)

        if not isinstance(triples, list):
            return []

        return triples[:MAX_TRIPLES]

    except Exception as e:
        print(f"❌ Ollama request failed: {e}")
        return []


# ==========================================================
# 2️⃣ Enrich single node
# ==========================================================
def enrich_node_from_wikipedia(graph: KnowledgeGraph, node_id: str, summary: str):
    node = graph.get_node(node_id)
    if not node:
        return

    if node.attributes.get("enriched_from_wiki"):
        print(f"ℹ️ Node {node_id} already enriched. Skipping.")
        return

    print(f"📄 Processing node: {node_id}")
    print(f"📄 Summary length: {len(summary)} chars")

    # Retry mechanism
    triples = []
    for _ in range(MAX_RETRIES):
        triples = extract_triples_with_ollama(summary)
        if triples:
            break

    if not triples:
        print("❌ No valid triples extracted.")
        return

    print(f"✅ Extracted {len(triples)} triples.")

    current_ts = int(time.time())

    existing_names = {
        normalize_concept(n.attributes.get("name", "")).lower(): nid
        for nid, n in graph.nodes.items()
    }

    for triple in triples:
        if not isinstance(triple, list) or len(triple) != 3:
            continue

        if not all(isinstance(s, str) for s in triple):
            continue

        head, rel, tail = [s.strip() for s in triple]

        if not head or not rel or not tail:
            continue

        rel = rel.strip().upper()
        if not rel:
            continue

        # Normalize concept names
        head_name = normalize_concept(head)
        tail_name = normalize_concept(tail)

        # --- HEAD NODE ---
        head_id = existing_names.get(head_name.lower())
        if not head_id:
            head_id = generate_node_id(head_name)
            head_node = Node(
                node_id=head_id,
                node_type="Concept",
                base_weight=0.5,
                memory_type="semantic"
            )
            head_node.attributes.update({
                "name": head_name,
                "weight": 0.5,
                "memory_type": "semantic",
                "created_at": current_ts,
                "last_accessed": current_ts,
                "source": "wiki_enrichment"
            })
            graph.add_node(head_node)
            existing_names[head_name.lower()] = head_id

        # --- TAIL NODE ---
        tail_id = existing_names.get(tail_name.lower())
        if not tail_id:
            tail_id = generate_node_id(tail_name)
            tail_node = Node(
                node_id=tail_id,
                node_type="Concept",
                base_weight=0.5,
                memory_type="semantic"
            )
            tail_node.attributes.update({
                "name": tail_name,
                "weight": 0.5,
                "memory_type": "semantic",
                "created_at": current_ts,
                "last_accessed": current_ts,
                "source": "wiki_enrichment"
            })
            graph.add_node(tail_node)
            existing_names[tail_name.lower()] = tail_id

        # --- ADD EDGE ---
        edge = Edge(src=head_id, dst=tail_id, relation=rel, weight=0.7)
        try:
            graph.add_edge(edge)
        except Exception:
            pass

    node.attributes["enriched_from_wiki"] = True
    node.attributes["wiki_summary_length"] = len(summary)

    time.sleep(ENRICH_DELAY)


# ==========================================================
# 3️⃣ Batch runner
# ==========================================================
def run(graph: KnowledgeGraph, nodes_to_enrich: Dict[str, str], save_path: str = "knowledge_graph.json"):

    total = len(nodes_to_enrich)
    if total == 0:
        print("⏭️ No nodes to enrich.")
        return

    print(f"🚀 Starting enrichment of {total} nodes...")

    for i, (node_id, summary) in enumerate(nodes_to_enrich.items()):
        try:
            if not summary or len(summary.strip()) < 10:
                print(f"⚠️ Skipping node {node_id}: summary too short")
                continue

            print(f"\n[{i+1}/{total}] Enriching node: {node_id}")
            enrich_node_from_wikipedia(graph, node_id, summary)

        except Exception as e:
            print(f"❌ Error enriching node {node_id}: {e}")
            continue

    try:
        graph.save_to_json(save_path)
        print(f"💾 Graph saved to {save_path}")
    except Exception as e:
        print(f"❌ Failed to save graph: {e}")

    print("✅ Enrichment completed.")


# ==========================================================
# 4️⃣ Test block
# ==========================================================
if __name__ == "__main__":

    try:
        graph =KnowledgeGraph.load_from_json("../knowledge_graph.json")
        if graph is None:
            raise ValueError("Failed to load graph.")

        sample_nodes = {
            "Person_Albert_Einstein_1718229600":
                "Albert Einstein was a theoretical physicist known for developing the theory of relativity.",
            "Place_Tokyo_1718229600":
                "Tokyo is the capital city of Japan and one of the most populous metropolitan areas in the world."
        }

        run(graph, sample_nodes)

    except ImportError as e:
        print(f"❌ Module import error: {e}")
    except FileNotFoundError:
        print("❌ Graph file not found.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")