from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
DATA = BASE / "backend" / "data"
GRAPH = DATA / "knowledge_graph.json"
RUNTIME = DATA / "runtime_state.json"

BAD_NODES = {
    "Input_Pragmatics_Layer",
    "Parse_Assertion_Input",
    "Parse_Directive_Inquiry",
    "Parse_Command_Input",
    "Parse_Feedback_Input",
    "Parse_Correction_Input",
    "Parse_Preference_Input",
    "Parse_Goal_Input",
    "Parse_Knowledge_Teaching_Input",
    "Parse_Self_Reference_Input",
    "Parse_User_State_Input",
    "Parse_Low_Value_Input",
    "Response_Generation_Layer",
    "Answer_Concise_First_Person",
    "Answer_With_Evidence_Edge",
    "Answer_Debug_Context",
    "Answer_Insufficient_Context",
    "Answer_Clarifying_Question",
    "Answer_Teaching_Mode",
    "Answer_Reflective_Companion",
    "Answer_Governance_Result",
    "Answer_Recall_Summary",
    "Answer_Action_Confirmation",
}

def now():
    return datetime.now(timezone.utc).isoformat().replace(":", "-")

def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    if not GRAPH.exists():
        print(f"[ERROR] Cannot find {GRAPH}")
        print("请把这个脚本放在 E:\\Utopia 目录下运行，也就是 backend 文件夹旁边。")
        raise SystemExit(1)

    backup = GRAPH.with_name(f"knowledge_graph.backup_before_v091_repair_{now()}.json")
    shutil.copy2(GRAPH, backup)

    g = load_json(GRAPH, {"nodes": [], "edges": []})
    before_nodes = len(g.get("nodes", []))
    before_edges = len(g.get("edges", []))

    existing = {n.get("id") for n in g.get("nodes", [])}
    removed = sorted(BAD_NODES & existing)

    g["nodes"] = [n for n in g.get("nodes", []) if n.get("id") not in BAD_NODES]
    g["edges"] = [
        e for e in g.get("edges", [])
        if e.get("src") not in BAD_NODES and e.get("dst") not in BAD_NODES
    ]

    save_json(GRAPH, g)

    if RUNTIME.exists():
        rt = load_json(RUNTIME, {})
        acts = rt.get("activations", {})
        if isinstance(acts, dict):
            for node_id in BAD_NODES:
                acts.pop(node_id, None)
        save_json(RUNTIME, rt)

    print("[OK] v0.6R.9.1 误加节点清理完成")
    print(f"Backup: {backup}")
    print(f"Removed nodes: {len(removed)}")
    for x in removed:
        print(f" - {x}")
    print(f"Nodes: {before_nodes} -> {len(g.get('nodes', []))}")
    print(f"Edges: {before_edges} -> {len(g.get('edges', []))}")

if __name__ == "__main__":
    main()
