# memory_graph_builder.py
# Unified with KnowledgeGraph.
# No changes needed beyond imports.

import os
import time
from Knowledge_Graph import KnowledgeGraph, Node, Edge
from utils import normalize_concept, generate_node_id

class MemoryGraphBuilder:
    def __init__(self, graph_file: str = "knowledge_graph.json"):
        self.graph_file = graph_file
        if os.path.exists(graph_file):
            self.graph = KnowledgeGraph.load_from_json(graph_file)
            print(f"✅ 已加载知识图谱: {graph_file}")
        else:
            self.graph = KnowledgeGraph()
            print(f"✅ 创建新知识图谱: {graph_file}")

    def save_graph(self):
        self.graph.save_to_json(self.graph_file)
        print(f"✅ 图谱已保存到 {self.graph_file}")

    def create_node_interactive(self):
        print("\n--- 创建记忆节点 ---")
        label = input("节点标签（Concept/Event/Action/Rule/Emotion/Personality，默认 Concept）: ").strip()
        if not label:
            label = "Concept"
        if label not in ["Concept", "Event", "Action", "Rule", "Emotion", "Personality"]:
            print("❌ 无效标签")
            return

        name = input("节点名字（name，必填）: ").strip()
        if not name:
            print("❌ 名字（name）不能为空")
            return

        current_ts = int(time.time())
        default_mem_type = "semantic" if label in ["Concept", "Rule"] else "episodic"
        properties = {
            "name": name,
            "weight": 0.0,
            "memory_type": default_mem_type,
            "created_at": current_ts,
            "last_accessed": current_ts
        }

        print("\n请输入额外属性（key=value，每行一个，空行结束）:")
        while True:
            line = input().strip()
            if not line:
                break
            if '=' in line:
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip()
                if k in ("name", "created_at", "last_accessed"):
                    print(f"⚠️ '{k}' 是系统字段，不能手动设置")
                    continue
                if v.lower() in ('true', 'false'):
                    properties[k] = v.lower() == 'true'
                elif v.isdigit():
                    properties[k] = int(v)
                elif v.replace('.', '', 1).isdigit():
                    properties[k] = float(v)
                else:
                    properties[k] = v

        mem_type_input = input(f"记忆类型（episodic/semantic，默认 {default_mem_type}）: ").strip().lower()
        if mem_type_input:
            if mem_type_input in ("episodic", "semantic"):
                properties["memory_type"] = mem_type_input
            else:
                print("⚠️ 无效记忆类型，保留默认")

        try:
            w_input = input("权重（默认 0.0）: ").strip()
            if w_input:
                properties["weight"] = float(w_input)
        except ValueError:
            print("⚠️ 无效数字，保留默认权重 0.0")

        node_id = f"{label}_{name}_{current_ts}"
        node = Node(
            node_id=node_id,
            node_type=label,
            base_weight=properties["weight"],
            memory_type=properties["memory_type"]
        )
        node.attributes = properties
        self.graph.add_node(node)
        self.save_graph()
        print(f"✅ 节点 [{label} {{name: '{name}'}}] 创建成功")
        print(f"   → memory_type: {properties['memory_type']}")
        print(f"   → weight: {properties['weight']}")

    def create_relationship_interactive(self):
        print("\n--- 创建记忆关系（边） ---")
        start_label = input("起始节点标签（留空默认为 Concept）: ").strip() or "Concept"
        start_name = input(f"起始节点名字（{start_label}.name）: ").strip()
        if not start_name:
            print("❌ 名字不能为空")
            return

        end_label = input("目标节点标签（留空默认为 Concept）: ").strip() or "Concept"
        end_name = input(f"目标节点名字（{end_label}.name）: ").strip()
        if not end_name:
            print("❌ 名字不能为空")
            return

        rel_type = input("关系类型（e.g., PART_OF, CAUSES）: ").strip().upper()
        if not rel_type:
            print("❌ 关系类型不能为空")
            return

        try:
            weight_input = input("关系权重（默认 0.0）: ").strip()
            weight = float(weight_input) if weight_input else 0.0
        except ValueError:
            print("⚠️ 无效权重，使用默认 0.0")
            weight = 0.0

        start_id = None
        end_id = None
        for nid, node in self.graph.nodes.items():
            if node.type == start_label and node.attributes.get("name") == start_name:
                start_id = nid
            if node.type == end_label and node.attributes.get("name") == end_name:
                end_id = nid

        if not start_id or not end_id:
            print("❌ 未找到起始或目标节点")
            return

        edge = Edge(src=start_id, dst=end_id, relation=rel_type, weight=weight)
        self.graph.add_edge(edge)
        self.save_graph()
        print(
            f"✅ 关系 [{start_label} {{name:'{start_name}'}}]-[:{rel_type}]->[{end_label} {{name:'{end_name}'}}] 创建成功")

    def delete_node_by_name(self):
        label = input("节点标签: ").strip()
        name = input("节点名字: ").strip()
        for nid, node in list(self.graph.nodes.items()):
            if node.type == label and node.attributes.get("name") == name:
                del self.graph.nodes[nid]
                self.graph.out_edges.pop(nid, None)
                self.graph.in_edges.pop(nid, None)
                self.graph.out_edges = {src: [e for e in edges if e.dst != nid] for src, edges in self.graph.out_edges.items()}
                self.graph.in_edges = {dst: [e for e in edges if e.src != nid] for dst, edges in self.graph.in_edges.items()}
                print(f"✅ 已删除节点 [{label} {{name: '{name}'}}]")
                self.save_graph()
                return
        print("❌ 未找到节点")

    def delete_node_interactive(self):
        print("⚠️ 功能暂未实现")

    def edit_node_weight_interactive(self):
        label = input("节点标签: ").strip()
        name = input("节点名字: ").strip()
        try:
            new_weight = float(input("新权重: ").strip())
        except ValueError:
            print("⚠️ 无效权重")
            return

        for nid, node in self.graph.nodes.items():
            if node.type == label and node.attributes.get("name") == name:
                node.base_weight = new_weight
                node.attributes["weight"] = new_weight
                print(f"✅ 已更新节点 [{label} {{name: '{name}'}}] 权重为 {new_weight}")
                self.save_graph()
                return
        print("❌ 未找到节点")


def main():
    builder = MemoryGraphBuilder()
    try:
        while True:
            print(f"\n=== 记忆图构建器 ===")
            print("1. 创建节点")
            print("2. 创建关系")
            print("3. 删除节点（按名字）")
            print("4. 删除节点（按属性）")
            print("5. 编辑节点权重")
            print("6. 退出")
            choice = input("请选择: ").strip()
            if choice == "1":
                builder.create_node_interactive()
            elif choice == "2":
                builder.create_relationship_interactive()
            elif choice == "3":
                builder.delete_node_by_name()
            elif choice == "4":
                builder.delete_node_interactive()
            elif choice == "5":
                builder.edit_node_weight_interactive()
            elif choice == "6":
                break
            else:
                print("无效选项")
    finally:
        print("👋 已断开连接")


if __name__ == "__main__":
    main()