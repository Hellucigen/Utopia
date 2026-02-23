# attention_framework.py (完整修改版，假设原代码结构)
from nl_driven_activation import extract_triples_from_text
import time
import random
from typing import Dict, Optional
from collections import defaultdict
from Knowledge_Graph import KnowledgeGraph, Node, Edge
from action_executor import ActionExecutor  # 导入executor
from actions.wiki_enricher import enrich_node_from_wikipedia  # 假设wiki_enricher.py已导入或整合
from utils import normalize_concept, generate_node_id  # 新导入共享函数

class ActivationManager:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.activations: Dict[str, float] = {}
        self.activation_sources: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 0.0 (纯 DMN, 发散) <---> 1.0 (纯 CEN, 聚焦)
        self.lambda_mode = 0.0

        # 动力学参数 (基于论文 2.2.3 DMN vs CEN)
        # DMN: 衰减慢，扩散广 (适合联想)
        # CEN: 衰减快，扩散窄 (适合任务)
        self.decay_rate_dmn = 0.1  # 提高到0.1，加速DMN衰减
        self.decay_rate_cen = 0.2  # 略提高CEN衰减，快速聚焦
        self.spread_factor_dmn = 0.8  # 略降低扩散，防止异常累积
        self.spread_factor_cen = 0.4

        self.decay_rate = self.decay_rate_dmn
        self.spread_factor = self.spread_factor_dmn
        self._update_params()

    def _update_params(self):
        lm = self.lambda_mode
        self.decay_rate = max(0.08, self.decay_rate_dmn + (self.decay_rate_cen - self.decay_rate_dmn) * lm)  # 最小衰减0.08，防止太慢
        self.spread_factor = self.spread_factor_dmn - (self.spread_factor_dmn - self.spread_factor_cen) * lm

    def update_lambda_mode(self, delta: float = 0.0):
        """调整模式，并限制在 0~1 之间"""
        self.lambda_mode = max(0.0, min(1.0, self.lambda_mode + delta))
        self._update_params()

    def activate(self, node_id: str, strength: float, source: str = "input"):
        """注入能量"""
        if node_id in self.graph.nodes:
            self.activations[node_id] = self.activations.get(node_id, 0.0) + strength
            self.activation_sources[node_id][source] = self.activation_sources[node_id].get(source, 0.0) + strength

    def clear_old_activations(self, threshold=0.1):
        """清除低激活残留，防止DMN干扰新输入"""
        for nid in list(self.activations.keys()):
            if self.activations[nid] < threshold:
                del self.activations[nid]
                self.activation_sources.pop(nid, None)

    def drift(self):
        """
        [DMN 核心]: 当系统闲置时，基于概率进行随机联想。
        """
        # 如果当前非常专注 (CEN > 0.4)，则不游荡
        if self.lambda_mode > 0.4:
            return None

        # 1. 获取当前最活跃的想法 (如果有)
        top_node_id = self.get_top_node()

        # 2. 策略A: 联想扩散 (从当前想法跳到邻居)
        if top_node_id:
            neighbors = self.graph.out_edges.get(top_node_id, [])
            if neighbors:
                # 随机选一个邻居，给予微弱刺激
                edge = random.choice(neighbors)
                drift_energy = 0.2 * (1.0 - self.lambda_mode)  # 越放松，能量越容易流动，降低以防累积
                self.activate(edge.dst, drift_energy, source="dmn_assoc")
                return f"💭 联想: {top_node_id} -> {edge.dst}"

        # 3. 策略B: 随机闪念 (如果没有焦点，或者概率触发)
        if not top_node_id or random.random() < 0.1:
            all_nodes = list(self.graph.nodes.keys())
            if all_nodes:
                random_node = random.choice(all_nodes)
                self.activate(random_node, 0.4, source="dmn_random")
                return f"✨ 闪念: {random_node}"

        return None

    def decay(self):
        """能量自然衰减"""
        for nid in list(self.activations.keys()):
            self.activations[nid] -= self.decay_rate
            if self.activations[nid] <= 0:
                del self.activations[nid]
                self.activation_sources.pop(nid, None)

    def spread(self):
        """能量在图谱中传播"""
        new_contribs = defaultdict(float)

        # 简单的单步传播
        for nid, act in self.activations.items():
            neighbors = self.graph.out_edges.get(nid, [])
            if not neighbors:
                continue
            norm_factor = 1.0 / len(neighbors) if len(neighbors) > 0 else 0  # 规范化，防止多边累积
            for edge in neighbors:
                flow = act * edge.weight * self.spread_factor * norm_factor
                if flow > 0.01:
                    new_contribs[edge.dst] += flow

        # 应用传播结果
        for dst, flow in new_contribs.items():
            self.activations[dst] = min(2.0, self.activations.get(dst, 0.0) + flow)  # Cap at 2.0，防止异常高

    def get_top_node(self) -> Optional[str]:
        if not self.activations:
            return None
        return max(self.activations, key=self.activations.get)

    def get_activation(self, node_id: str) -> float:
        return self.activations.get(node_id, 0.0)


class AttentionFramework:
    def __init__(self, kg_path: str = "knowledge_graph.json"):
        self.graph = KnowledgeGraph.load_from_json(kg_path)
        self.am = ActivationManager(self.graph)

    def inject_text(self, text: str):
        """处理外部输入"""
        if not text.strip():
            return

        print(f"📥 感知输入: {text}")

        # 新增：清除旧低激活，焦点重置
        self.am.clear_old_activations()

        # 1. 瞬间拉高 CEN 模式 (进入专注状态)
        self.am.update_lambda_mode(delta=1.0)

        # 2. 提取语义并激活
        triples = extract_triples_from_text(text)
        print(f"Extracted triples: {triples}")  # 日志查看LLM返回

        if not triples:
            # 兜底：激活输入关键词并创建新节点
            keywords = text.split()[:2]  # 简化，实际用NLP
            for kw in keywords:
                kw_name = normalize_concept(kw)  # 规范化
                kw_id = self.graph.get_node_by_name(kw_name)  # 使用新方法
                if not kw_id:
                    kw_id = generate_node_id(kw_name)
                    node = Node(kw_id, "Concept", 0.5, "semantic")
                    current_ts = int(time.time())  # UTC秒级时间戳，仅属性
                    node.attributes = {"name": kw_name, "created_at": current_ts, "last_accessed": current_ts, "source": "user_input"}
                    self.graph.add_node(node)
                    print(f"Created new node for unknown concept: {kw_name}")
                    # Enrich from Wiki (假设summary需外部获取，这里模拟或调用browse_page获取)
                    summary = "Placeholder Wikipedia summary for " + kw_name  # 实际用工具获取
                    enrich_node_from_wikipedia(self.graph, kw_id, summary)
                self.am.activate(kw_id, 0.8, "unknown_input")
            self.am.spread()  # 立即传播
            self.am.spread()  # 多一次，确保焦点稳定
            return

        # 完整图谱更新与激活逻辑
        current_ts = int(time.time())
        existing_names = {normalize_concept(node.attributes.get("name", "")).lower(): nid for nid, node in self.graph.nodes.items()}

        for head, rel, tail in triples:
            head_name = normalize_concept(head)
            tail_name = normalize_concept(tail)
            # Head node
            head_id = existing_names.get(head_name.lower())
            if not head_id:
                head_id = generate_node_id(head_name)
                head_node = Node(head_id, "Concept", 0.5, "semantic")
                head_node.attributes = {"name": head_name, "created_at": current_ts, "last_accessed": current_ts, "source": "llm_triple"}
                self.graph.add_node(head_node)
                existing_names[head_name.lower()] = head_id
                print(f"Created new head node: {head_name}")
                # Enrich if unknown
                summary = "Placeholder Wikipedia summary for " + head_name  # 实际获取
                enrich_node_from_wikipedia(self.graph, head_id, summary)

            # Tail node
            tail_id = existing_names.get(tail_name.lower())
            if not tail_id:
                tail_id = generate_node_id(tail_name)
                tail_node = Node(tail_id, "Concept", 0.5, "semantic")
                tail_node.attributes = {"name": tail_name, "created_at": current_ts, "last_accessed": current_ts, "source": "llm_triple"}
                self.graph.add_node(tail_node)
                existing_names[tail_name.lower()] = tail_id
                print(f"Created new tail node: {tail_name}")
                # Enrich if unknown
                summary = "Placeholder Wikipedia summary for " + tail_name  # 实际获取
                enrich_node_from_wikipedia(self.graph, tail_id, summary)

            # Add edge
            edge = Edge(src=head_id, dst=tail_id, relation=rel.upper(), weight=0.7)
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass  # 已存在

            # Activate
            self.am.activate(head_id, 1.0, "input")
            self.am.activate(tail_id, 1.0, "input")

        # 立即传播，确保焦点切换
        self.am.spread()
        self.am.spread()  # 多一次

        # 保存更新图谱
        self.graph.save_to_json("knowledge_graph.json")

    def step(self):
        """单次认知循环"""
        # 1. 能量扩散
        self.am.spread()
        # 2. 能量衰减
        self.am.decay()
        # 3. 模式回归 (如果没有外部刺激，CEN 会自然衰退回 DMN)
        self.am.update_lambda_mode(delta=-0.02)  # 慢衰退，保持焦点 longer

        # 新增：只在CEN模式下执行动作（DMN不行动）
        if self.am.lambda_mode > 0.4:  # CEN阈值
            executor = ActionExecutor(self.graph, self.am, threshold=0.1)
            executor.execute_pending_actions(current_focus=self.am.get_top_node())