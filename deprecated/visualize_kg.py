# visualize_kg.py
# No changes, already unified.
from utils import normalize_concept, generate_node_id
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional
from Knowledge_Graph import KnowledgeGraph, Node, Edge

class KnowledgeGraph(KnowledgeGraph):  # Extend if needed, but already good.
    pass

# Main unchanged.
if __name__ == "__main__":
    import sys
    filename = "knowledge_graph.json"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    print(f"🔍 Loading knowledge graph from: {filename}")
    kg = KnowledgeGraph.load_from_json(filename)
    kg.visualize()