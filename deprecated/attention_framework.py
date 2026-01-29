# attention_framework.py
# Adjusted decay_rate to 0.05 and spread_factor to 0.8 for better activation buildup and spreading,
# aligning with the paper's description of dynamic activation diffusion for attention migration.
# This should allow activations to propagate sufficiently to trigger actions like Answer for queries such as "What is your name".

import time
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from Knowledge_Graph import KnowledgeGraph, Node, Edge

class ActivationManager:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.activations: Dict[str, float] = {}
        self.activation_sources: Dict[str, Dict[str, float]] = defaultdict(dict)  # target -> {source_id: contrib}
        self.decay_rate = 0.05  # Reduced for slower decay, allowing buildup over steps
        self.spread_factor = 0.8  # Increased for stronger spreading, enabling deeper propagation

    def activate(self, node_id: str, strength: float, source: str = "input"):
        if node_id in self.graph.nodes:
            self.activations[node_id] = self.activations.get(node_id, 0.0) + strength
            self.activation_sources[node_id][source] = self.activation_sources[node_id].get(source, 0.0) + strength

    def decay(self):
        for nid in list(self.activations.keys()):
            self.activations[nid] -= self.decay_rate
            if self.activations[nid] <= 0:
                del self.activations[nid]
                self.activation_sources.pop(nid, None)

    def spread(self):
        new_contribs = defaultdict(dict)
        for nid, act in list(self.activations.items()):
            for edge in self.graph.out_edges.get(nid, []):
                dst = edge.dst
                prop = act * edge.weight * self.spread_factor
                new_contribs[dst][nid] = new_contribs[dst].get(nid, 0) + prop
        for dst, sources in new_contribs.items():
            for src, contrib in sources.items():
                self.activation_sources[dst][src] = self.activation_sources[dst].get(src, 0.0) + contrib
            self.activations[dst] = self.activations.get(dst, 0.0) + sum(sources.values())

    def get_top_node(self) -> Optional[str]:
        if not self.activations:
            return None
        return max(self.activations, key=self.activations.get)

    def get_activation(self, node_id: str) -> float:
        return self.activations.get(node_id, 0.0)

    def get_source_path_with_relations(self, node_id: str) -> List[Tuple[str, str]]:
        path = []
        current = node_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            sources = self.activation_sources.get(current, {})
            if not sources:
                break
            max_source = max(sources, key=sources.get)
            rel = "RELATED_TO"
            if max_source in self.graph.nodes:
                for edge in self.graph.out_edges.get(max_source, []):
                    if edge.dst == current:
                        rel = edge.relation
                        break
            path.insert(0, (current, rel))
            current = max_source if max_source in self.graph.nodes else None
        if path:
            path[0] = (path[0][0], "")  # No relation for the starting node in the path
        return path

class AttentionFramework:
    def __init__(self, kg_path: str = "knowledge_graph.json"):
        self.graph = KnowledgeGraph.load_from_json(kg_path)
        self.am = ActivationManager(self.graph)

    def inject_text(self, text: str, keyword_extractor_func):
        keywords = keyword_extractor_func(text)
        keyword_set = set(kw.lower() for kw in keywords)
        matched_node_ids = []
        for nid, node in self.graph.nodes.items():
            name = node.attributes.get("name", "").lower()
            if name in keyword_set:
                matched_node_ids.append(nid)
        if matched_node_ids:
            for nid in matched_node_ids:
                self.am.activate(nid, 1.0, "input")
        unknown_node_id = next((nid for nid, node in self.graph.nodes.items() if node.attributes.get("name") == "Unknown_Knowledge"), None)
        if unknown_node_id and keywords and not matched_node_ids:
            self.am.activate(unknown_node_id, len(keywords) * 0.5, "unknown")

    def step(self) -> Optional[str]:
        self.am.spread()
        self.am.decay()
        return self.am.get_top_node()