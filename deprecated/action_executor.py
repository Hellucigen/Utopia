# action_executor.py
# Unified imports.
import logging
import os
import importlib.util
from typing import Any, Dict, List
from Knowledge_Graph import KnowledgeGraph, Node
import time
from utils import normalize_concept, generate_node_id

logger = logging.getLogger(__name__)

class ActionExecutor:
    def __init__(self, graph: KnowledgeGraph, activation_manager, threshold: float = 0.1):  # 降低阈值
        self.graph = graph
        self.am = activation_manager
        self.threshold = threshold

    def _get_eligible_actions(self) -> List[Dict[str, Any]]:
        eligible = []
        for node_id, node in self.graph.nodes.items():
            if node.type == "Action":
                activation = self.am.get_activation(node_id)
                if activation >= self.threshold:
                    eligible.append({"id": node_id, "node": node, "activation": activation})
        return eligible

    def execute_pending_actions(self, current_focus: str = None, current_text: str = ""):
        actions = self._get_eligible_actions()
        if not actions:
            return
        logger.info(f"▶️ Executing {len(actions)} action(s)...")

        executor_dir = os.path.dirname(os.path.abspath(__file__))

        for act in actions:
            node_id = act["id"]
            node = act["node"]
            code = node.attributes.get("code", "").strip()
            if not code:
                logger.warning(f"Action node {node_id} has no executable code.")
                continue

            # ===== 判断是否为外部 .py 脚本 =====
            is_external_script = (
                code.endswith('.py')
                and '\n' not in code
                and ';' not in code
                and not code.startswith('/')
                and not code.startswith('\\')
            )

            if is_external_script:
                script_path = os.path.join(executor_dir, code)
                if os.path.isfile(script_path):
                    try:
                        spec = importlib.util.spec_from_file_location("_ext_action", script_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'run'):
                            module.run(self.graph, self.am, current_text)
                        else:
                            logger.warning(f"Script {code} has no 'run' function. Skipping execution.")
                        # 新增：执行后deactivate
                        self.am.activations[node_id] = 0.05  # 低于阈值，避免重复
                        continue
                    except Exception as e:
                        logger.error(f"External script execution failed for {node_id} ({code}): {e}")
                        continue

            # ===== 内联代码执行 =====
            exec_context = {
                "graph": self.graph,
                "am": self.am,
                "focus_of_attention": current_focus,
                "text": current_text,
                # 注意：已移除 extract_keywords
                "print": print,
                "time": time,
                "Node": Node,
                "__builtins__": {
                    'max': max, 'min': min, 'len': len,
                    'int': int, 'float': float, 'str': str,
                    'dict': dict, 'list': list, 'set': set
                }
            }

            try:
                exec(code, exec_context)
                # 新增：执行后deactivate
                self.am.activations[node_id] = 0.05  # 低于阈值，避免重复
            except Exception as e:
                logger.error(f"Action execution failed for {node_id}: {e}")