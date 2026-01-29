# Knowledge_Graph.py
# Unified KnowledgeGraph class with Node and Edge.
# Supports load/save in consistent JSON format: nodes as list of dicts, edges as list of dicts.

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt

class Node:
    def __init__(self, node_id: str, node_type: str = "Concept", base_weight: float = 1.0, memory_type: str = "semantic"):
        valid_types = ["Concept", "Event", "Action", "Rule", "Emotion", "Personality"]
        if node_type not in valid_types:
            raise ValueError(f"Invalid node_type: {node_type}. Must be one of: {valid_types}")
        self.id = node_id
        self.type = node_type
        self.base_weight = base_weight
        self.memory_type = memory_type
        self.attributes: Dict[str, any] = {}

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "base_weight": self.base_weight,
            "memory_type": self.memory_type,
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: Dict):
        node = cls(
            node_id=data["id"],
            node_type=data["type"],
            base_weight=data["base_weight"],
            memory_type=data["memory_type"]
        )
        node.attributes = data.get("attributes", {})
        return node

class Edge:
    def __init__(self, src: str, dst: str, relation: str = "RELATED_TO", weight: float = 1.0):
        self.src = src
        self.dst = dst
        self.relation = relation.upper()
        self.weight = weight

    def to_dict(self):
        return {
            "src": self.src,
            "dst": self.dst,
            "relation": self.relation,
            "weight": self.weight
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            src=data["src"],
            dst=data["dst"],
            relation=data["relation"],
            weight=data["weight"]
        )

class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.out_edges: Dict[str, List[Edge]] = defaultdict(list)
        self.in_edges: Dict[str, List[Edge]] = defaultdict(list)

    def add_node(self, node: Node):
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists.")
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def add_edge(self, edge: Edge):
        if edge.src not in self.nodes or edge.dst not in self.nodes:
            raise ValueError("Both src and dst nodes must exist before adding an edge")
        self.out_edges[edge.src].append(edge)
        self.in_edges[edge.dst].append(edge)

    def neighbors(self, node_id: str) -> List[str]:
        return [e.dst for e in self.out_edges.get(node_id, [])]

    def get_edge_weight(self, src: str, dst: str) -> float:
        for edge in self.out_edges.get(src, []):
            if edge.dst == dst:
                return edge.weight
        return 0.0

    def save_to_json(self, filename: str):
        data = {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edges in self.out_edges.values() for edge in edges]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @classmethod
    def load_from_json(cls, filename: str) -> 'KnowledgeGraph':
        if not os.path.exists(filename):
            print(f"⚠️ File '{filename}' not found. Creating empty graph.")
            return cls()
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        kg = cls()
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            kg.add_node(node)
        for edge_data in data.get("edges", []):
            edge = Edge.from_dict(edge_data)
            kg.add_edge(edge)
        return kg

    def visualize(self, max_nodes=50, figsize=(12, 8)):
        """ 可视化知识图谱（限制节点数以防卡顿）。 Args: max_nodes (int): 最多显示的节点数（按激活度或创建顺序） figsize (tuple): 图像尺寸 """
        if not self.nodes:
            print("⚠️ Knowledge graph is empty.")
            return

        # 如果节点太多，只取前 max_nodes 个（可按需改为按激活度排序）
        node_items = list(self.nodes.items())
        if len(node_items) > max_nodes:
            print(f"ℹ️ Graph has {len(node_items)} nodes. Showing first {max_nodes}.")
            node_items = node_items[:max_nodes]

        G = nx.DiGraph()  # 有向图

        # 添加节点
        for node_id, node in node_items:
            label = node.attributes.get("name", node_id)
            G.add_node(node_id, label=label, type=node.type)

        # 👇 关键修复：从 out_edges 提取所有边（而不是 self.edges）
        all_edges = [edge for edges in self.out_edges.values() for edge in edges]

        # 添加边（只添加两端都在 G 中的边）
        for edge in all_edges:
            if edge.src in G and edge.dst in G:
                G.add_edge(edge.src, edge.dst, relation=edge.relation)

        # 布局
        pos = nx.spring_layout(G, k=1.5, iterations=50)

        # 绘图
        plt.figure(figsize=figsize)
        nx.draw_networkx_nodes(
            G, pos,
            node_color=["lightblue" if G.nodes[n]["type"] == "Concept" else "lightgreen" for n in G.nodes],
            node_size=800,
            alpha=0.9
        )
        nx.draw_networkx_labels(
            G, pos,
            labels={n: G.nodes[n]["label"] for n in G.nodes},
            font_size=9,
            font_weight="bold"
        )
        nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=15, edge_color='gray')

        # 可选：绘制边标签（关系）
        if len(G.edges) <= 20:  # 节点少时才显示关系名，避免混乱
            edge_labels = {(u, v): d["relation"] for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

        plt.title("🧠 Haru Knowledge Graph", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.show()