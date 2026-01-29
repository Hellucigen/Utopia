# wiki_enricher.py

import requests
import json
import time
from Knowledge_Graph import Node, Edge

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"


def fetch_wikipedia_summary(keyword: str) -> str:
    """Fetch English Wikipedia summary for a keyword with proper User-Agent."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    headers = {
        "User-Agent": "Haru-Cognitive-Engine/1.0 (contact: 892755828@qq.com)"
        # 👆 请将 your_email@example.com 替换为你的真实邮箱（可选但推荐）
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract", "")
        else:
            print(f"⚠️ Wikipedia returned {resp.status_code} for '{keyword}'")
            if resp.status_code == 403:
                print("   💡 Tip: Check if User-Agent is set in request headers.")
            return ""
    except Exception as e:
        print(f"❌ Error fetching Wikipedia: {e}")
        return ""


def extract_triples_with_ollama(text: str) -> list:
    """Use Ollama qwen3:8b to extract (head, relation, tail) triples from text."""
    prompt = (
        "You are a knowledge graph builder. Extract semantic triples from the text.\n"
        "Rules:\n"
        "- Each triple: [head, relation, tail]\n"
        "- head and tail MUST be short, atomic concepts (1-3 words max)\n"
        "- NO full sentences, clauses, or phrases like 'in...', 'for...', 'has been...'\n"
        "- Normalize to singular nouns where possible (e.g., 'Apples' → 'Apple')\n"
        "- Use simple, clear relations (e.g., 'ORIGINATES_FROM', 'IS_A', 'CULTIVATED_IN')\n"
        "- Output ONLY a JSON list of lists. No other text.\n\n"
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
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            # Try to parse as JSON
            try:
                triples = json.loads(result)
                if isinstance(triples, list):
                    return triples
            except json.JSONDecodeError:
                print("⚠️ LLM did not return valid JSON. Raw output:")
                print(result)
        else:
            print(f"⚠️ Ollama error: {resp.status_code}")
    except Exception as e:
        print(f"❌ Ollama request failed: {e}")
    return []


def run(graph, am, current_text):
    """
    External action entry point called by ActionExecutor.
    Enriches the in-memory knowledge graph with Wikipedia + LLM triples.

    Args:
        graph: KnowledgeGraph instance (your main KG)
        am: ActivationManager (not used here, but required by interface)
        current_text: str, the input utterance that triggered this action
    """
    # Extract keyword from current_text (simple strategy: last alphabetic word)
    words = [w for w in current_text.split() if w.isalpha()]
    keyword = words[-1] if words else ""

    if not keyword:
        print("[wiki_enricher] No valid keyword found in input.")
        return

    print(f"🌐 Enriching knowledge for: {keyword}")

    # Step 1: Fetch Wikipedia summary
    summary = fetch_wikipedia_summary(keyword)
    if not summary:
        print("❌ No Wikipedia summary found.")
        return

    print(f"📄 Summary length: {len(summary)} chars")

    # Step 2: Extract triples via Ollama
    triples = extract_triples_with_ollama(summary)
    if not triples:
        print("❌ No triples extracted by LLM.")
        return

    print(f"🔗 Extracted {len(triples)} triples.")

    # Step 3: Enrich the in-memory graph (no file I/O!)
    existing_names = {}
    for nid, node in graph.nodes.items():
        name = node.attributes.get("name", "")
        existing_names[name.lower()] = (nid, node)

    new_nodes = []
    new_edges = []
    current_ts = int(time.time())

    for triple in triples:
        if len(triple) != 3:
            continue
        head, rel, tail = [s.strip() for s in triple]
        if not head or not rel or not tail:
            continue

        head_name = head.capitalize()
        tail_name = tail.capitalize()

        # Get or create head node
        if head_name.lower() in existing_names:
            head_id = existing_names[head_name.lower()][0]
        else:
            head_id = f"Concept_{head_name.replace(' ', '_')}_{current_ts}_{len(new_nodes)}"
            head_node = Node(
                node_id=head_id,
                node_type="Concept",
                base_weight=0.5,
                memory_type="semantic"
            )
            head_node.attributes = {
                "name": head_name,
                "weight": 0.5,
                "memory_type": "semantic",
                "created_at": current_ts,
                "last_accessed": current_ts
            }
            graph.add_node(head_node)
            existing_names[head_name.lower()] = (head_id, head_node)

        # Get or create tail node
        if tail_name.lower() in existing_names:
            tail_id = existing_names[tail_name.lower()][0]
        else:
            tail_id = f"Concept_{tail_name.replace(' ', '_')}_{current_ts}_{len(new_nodes)}"
            tail_node = Node(
                node_id=tail_id,
                node_type="Concept",
                base_weight=0.5,
                memory_type="semantic"
            )
            tail_node.attributes = {
                "name": tail_name,
                "weight": 0.5,
                "memory_type": "semantic",
                "created_at": current_ts,
                "last_accessed": current_ts
            }
            graph.add_node(tail_node)
            existing_names[tail_name.lower()] = (tail_id, tail_node)

        # Create edge
        edge = Edge(src=head_id, dst=tail_id, relation=rel.upper(), weight=0.6)
        try:
            graph.add_edge(edge)
        except ValueError as e:
            print(f"⚠️ Skip edge: {e}")

    print(f"✅ Added nodes and edges to in-memory knowledge graph.")

    try:
        graph.save_to_json("knowledge_graph.json")
        print("💾 Knowledge graph saved to 'knowledge_graph.json'.")
    except Exception as e:
        print(f"⚠️ Failed to save graph: {e}")