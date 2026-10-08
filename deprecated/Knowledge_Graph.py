# Knowledge_Graph.py (完整代码，整合所有修改)
from typing import Dict, List, Optional
from collections import defaultdict
import json
from utils import normalize_concept  # 导入共享函数（假设utils.py存在）


class Node:
    def __init__(self, node_id: str, node_type: str, base_weight: float, memory_type: str):
        self.id = node_id
        self.type = node_type
        self.base_weight = base_weight
        self.memory_type = memory_type
        self.attributes: Dict = {}


class Edge:
    def __init__(self, src: str, dst: str, relation: str, weight: float):
        self.src = src
        self.dst = dst
        self.relation = relation
        self.weight = weight


class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.out_edges: Dict[str, List[Edge]] = defaultdict(list)
        self.in_edges: Dict[str, List[Edge]] = defaultdict(list)

    def add_node(self, node: Node):
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        # Check for duplicate edges
        for existing in self.out_edges[edge.src]:
            if existing.dst == edge.dst and existing.relation == edge.relation:
                return  # or raise ValueError("Duplicate edge")
        self.out_edges[edge.src].append(edge)
        self.in_edges[edge.dst].append(edge)

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    @classmethod
    def load_from_json(cls, path: str) -> 'KnowledgeGraph':
        with open(path, 'r') as f:
            data = json.load(f)
        kg = cls()
        for node_data in data['nodes']:
            node = Node(
                node_data['id'],
                node_data['type'],
                node_data['base_weight'],
                node_data['memory_type']
            )
            node.attributes = node_data['attributes']
            kg.add_node(node)
        for edge_data in data['edges']:
            edge = Edge(
                edge_data['src'],
                edge_data['dst'],
                edge_data['relation'],
                edge_data['weight']
            )
            kg.add_edge(edge)
        return kg

    def save_to_json(self, path: str):
        data = {
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type,
                    'base_weight': node.base_weight,
                    'memory_type': node.memory_type,
                    'attributes': node.attributes
                } for node in self.nodes.values()
            ],
            'edges': [
                {
                    'src': edge.src,
                    'dst': edge.dst,
                    'relation': edge.relation,
                    'weight': edge.weight
                } for edges in self.out_edges.values() for edge in edges
            ]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_node_by_name(self, name: str) -> Optional[str]:
        norm_name = normalize_concept(name).lower()
        for nid, node in self.nodes.items():
            if normalize_concept(node.attributes.get("name", "")).lower() == norm_name:
                return nid
        return None

    def merge_nodes_by_name(self):
        from collections import defaultdict
        name_to_ids = defaultdict(list)
        for nid, node in self.nodes.items():
            norm_name = normalize_concept(node.attributes.get("name", ""))
            if norm_name:
                name_to_ids[norm_name.lower()].append(nid)

        for norm_name, ids in name_to_ids.items():
            if len(ids) > 1:
                primary_id = ids[0]  # 保留第一个
                for duplicate_id in ids[1:]:
                    # 合并边：将duplicate的边迁移到primary
                    for edge in self.out_edges.get(duplicate_id, []):
                        new_edge = Edge(primary_id, edge.dst, edge.relation, edge.weight)
                        self.add_edge(new_edge)
                    for src, edges in list(self.in_edges.items()):
                        for i, edge in enumerate(edges):
                            if edge.dst == duplicate_id:
                                edges[i] = Edge(edge.src, primary_id, edge.relation, edge.weight)
                    # 删除duplicate
                    del self.nodes[duplicate_id]
                    self.out_edges.pop(duplicate_id, None)
                    self.in_edges.pop(duplicate_id, None)
                print(f"Merged {len(ids) - 1} duplicates for '{norm_name}' into {primary_id}")