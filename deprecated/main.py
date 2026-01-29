# main.py
# Updated with unified classes.
# Uses am.get_source_path_with_relations.

from attention_framework import AttentionFramework
from action_executor import ActionExecutor
from nl_driven_activation import extract_keywords
import logging

logging.basicConfig(level=logging.INFO)

def format_node_name(graph, node_id):
    if node_id in ("input", "natural_language"):
        return "User Input"
    node = graph.get_node(node_id)
    if node is None:
        return f"[Unknown]{node_id}"
    name = node.attributes.get("name", node_id)
    return f"[{node.type}] {name}"

def format_chain_with_relations(graph, path_with_rels):
    parts = []
    for i, (node_id, rel) in enumerate(path_with_rels):
        node_str = format_node_name(graph, node_id)
        if i == 0:
            parts.append(node_str)
        else:
            parts.append(f" --[{rel}]→ {node_str}")
    return "".join(parts)

def main():
    af = AttentionFramework()
    executor = ActionExecutor(af.graph, af.am)

    while True:
        user_input = input("\n🗣️ > ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if not user_input:
            continue

        af.inject_text(user_input, keyword_extractor_func=extract_keywords)

        prev_foa = None
        stable_count = 0
        max_stable = 2
        max_rounds = 6

        for round_num in range(max_rounds):
            foa = af.step()
            if foa == prev_foa:
                stable_count += 1
            else:
                stable_count = 0
            prev_foa = foa

            if stable_count >= max_stable:
                executor.execute_pending_actions(current_focus=foa, current_text=user_input)
                break

            if round_num == max_rounds - 1:
                executor.execute_pending_actions(current_focus=foa, current_text=user_input)

        # Build chains
        chains = []

        # FoA chain
        if foa and af.graph.get_node(foa).type != "Action":
            foa_path = af.am.get_source_path_with_relations(foa)
            foa_chain = format_chain_with_relations(af.graph, foa_path)
            chains.append(f"🎯 FoA: {foa_chain}")

        # Action chains
        action_entries = []
        for node_id, node in af.graph.nodes.items():
            if node.type == "Action":
                act_val = af.am.get_activation(node_id)
                if act_val >= executor.threshold:
                    path = af.am.get_source_path_with_relations(node_id)
                    chain_str = format_chain_with_relations(af.graph, path)
                    action_entries.append((act_val, chain_str))

        action_entries.sort(key=lambda x: x[0], reverse=True)
        for act_val, chain_str in action_entries:
            chains.append(f"✅ Action ({act_val:.4f}): {chain_str}")

        # Output
        print("\n🔗 推理链条:")
        if chains:
            for i, desc in enumerate(chains, 1):
                print(f"  {i}. {desc}")
        else:
            print("无显著推理链条")

    print("\n👋 认知引擎已关闭。")

if __name__ == "__main__":
    main()