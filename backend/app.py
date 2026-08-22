
from __future__ import annotations

import json
import os
import re
import threading
import time
import difflib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from . import nlp
from . import semantic_matcher

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GRAPH_FILE = DATA_DIR / "knowledge_graph.json"
RUNTIME_FILE = DATA_DIR / "runtime.json"
SCHEMA_FILE = DATA_DIR / "schema.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_json(path, default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, obj: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return obj


def clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))


def norm_text(s: str) -> str:
    s = str(s or "").strip().lower()
    s = re.sub(r"[\s\-_\/\\:;，,。.!！？?【】\[\]{}()<>\'\"“”‘’`~]+", "", s)
    return s


def norm_id(s: str) -> str:
    raw = str(s or "").strip()
    if not raw:
        return "Unknown"
    raw = raw.replace("/", "_").replace("\\", "_").replace(":", "_").replace("+", "_")
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw or "Unknown"


def norm_relation(s: str) -> str:
    if s is None:
        return "related_to"
    raw = str(s).strip()
    mapping = {
        "属于": "is_a",
        "是": "is_a",
        "有": "has",
        "包含": "contains",
        "使用": "uses",
        "导致": "causes",
        "触发": "triggers",
        "生成": "generates",
        "执行": "executes",
        "关联": "related_to",
        "相关": "related_to",
    }
    if raw in mapping:
        return mapping[raw]
    rel = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "_", raw.lower())
    rel = re.sub(r"_+", "_", rel).strip("_")
    return rel or "related_to"


def default_schema() -> dict:
    return {
        "version": "1.0.0",
        "node_labels": ["declarative-semantic", "declarative-episodic", "procedural"],
        "node_fields": ["id", "weight", "activation", "last_access_time", "created_at", "label", "execution", "attributes"],
        "edge_fields": ["src", "dst", "relation", "last_access_time", "created_at", "weight", "activation", "attributes"],
        "hyperparameters": {
            "initial_match_activation": 1.2,
            "match_decay": 0.35,
            "spread_beta": 0.9,
            "decay_lambda": 0.15,
            "activation_threshold": 0.12,
            "max_activation": 2.0,
            "top_k": 6,
            "result_limit": 6,
            "action_threshold": 1.0,
            "activation_floor": 0.0,
            "realtime_interval_ms": 800,
            "max_spread_steps": 8,
            "natural_language_seed_id": "Natural_Language_Input_Processor",
        },
    }


def default_graph() -> dict:
    t = utc_now()
    return {
        "meta": {
            "name": "Unified Knowledge Graph",
            "version": default_schema()["version"],
            "created_at": t,
            "updated_at": t,
        },
        "nodes": [],  # 这里现在是空的，系统启动时是一张真正的白纸
        "edges": [],
        "logs": [],
    }


def default_runtime() -> dict:
    return {
        "params": default_schema()["hyperparameters"].copy(),
        "top_k": [],
        "focus": None,
        "last_parse": None,
        "last_action_result": None,
        "loop": {
            "running": False,
            "tick_count": 0,
            "last_tick_at": None,
            "auto_spread": True,
            "auto_execute_actions": True,
        },
        "logs": [],
    }


def ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEMA_FILE.exists():
        write_json(SCHEMA_FILE, default_schema())
    if not GRAPH_FILE.exists():
        write_json(GRAPH_FILE, default_graph())
    if not RUNTIME_FILE.exists():
        write_json(RUNTIME_FILE, default_runtime())


ensure_store()


def load_graph() -> dict:
    g = read_json(GRAPH_FILE, default_graph())
    g.setdefault("meta", {})
    g.setdefault("nodes", [])
    g.setdefault("edges", [])
    g.setdefault("logs", [])
    g["meta"].setdefault("updated_at", utc_now())
    return g


def load_runtime() -> dict:
    r = read_json(RUNTIME_FILE, default_runtime())
    r.setdefault("params", default_schema()["hyperparameters"].copy())
    r.setdefault("top_k", [])
    r.setdefault("focus", None)
    r.setdefault("last_parse", None)
    r.setdefault("last_action_result", None)
    r.setdefault("loop", {})
    r.setdefault("logs", [])
    for k, v in default_schema()["hyperparameters"].items():
        r["params"].setdefault(k, v)
    r["loop"].setdefault("running", False)
    r["loop"].setdefault("tick_count", 0)
    r["loop"].setdefault("last_tick_at", None)
    r["loop"].setdefault("auto_spread", True)
    r["loop"].setdefault("auto_execute_actions", True)
    return r


def save_graph(g: dict) -> dict:
    g.setdefault("meta", {})
    g["meta"]["updated_at"] = utc_now()
    return write_json(GRAPH_FILE, g)


def save_runtime(r: dict) -> dict:
    return write_json(RUNTIME_FILE, r)


def log_graph(g: dict, msg: str) -> None:
    g.setdefault("logs", [])
    g["logs"].insert(0, f"{utc_now()} | {msg}")
    g["logs"] = g["logs"][:500]


def log_runtime(r: dict, msg: str) -> None:
    r.setdefault("logs", [])
    r["logs"].insert(0, f"{utc_now()} | {msg}")
    r["logs"] = r["logs"][:500]


def find_node(g: dict, node_id: str) -> Optional[dict]:
    nid = norm_id(node_id)
    for n in g["nodes"]:
        if n.get("id") == nid:
            return n
    return None


def ensure_node_shape(node: dict) -> dict:
    return {
        "id": norm_id(node.get("id")),
        "weight": clamp(float(node.get("weight", 0.0)), -2.0, 2.0),
        "activation": max(0.0, float(node.get("activation", 0.0))),
        "last_access_time": node.get("last_access_time") or utc_now(),
        "created_at": node.get("created_at") or utc_now(),
        "label": str(node.get("label", "declarative-semantic")).strip().lower(),
        "execution": str(node.get("execution", "") or ""),
        "attributes": dict(node.get("attributes") or {}),
    }


def ensure_edge_shape(edge: dict) -> dict:
    return {
        "id": str(edge.get("id") or f"e_{norm_id(edge.get('src'))}_{norm_relation(edge.get('relation'))}_{norm_id(edge.get('dst'))}_{int(time.time()*1000)}"),
        "src": norm_id(edge.get("src")),
        "dst": norm_id(edge.get("dst")),
        "relation": norm_relation(edge.get("relation", "related_to")),
        "weight": clamp(float(edge.get("weight", 0.0)), -2.0, 2.0),
        "activation": max(0.0, float(edge.get("activation", 0.0))),
        "last_access_time": edge.get("last_access_time") or utc_now(),
        "created_at": edge.get("created_at") or utc_now(),
        "attributes": dict(edge.get("attributes") or {}),
    }


def upsert_node(g: dict, node: dict) -> dict:
    shaped = ensure_node_shape(node)
    for existing in g["nodes"]:
        if existing["id"] == shaped["id"]:
            shaped["created_at"] = existing.get("created_at", shaped["created_at"])
            existing.update(shaped)
            existing["last_access_time"] = utc_now()
            log_graph(g, f"node_updated {shaped['id']}")
            return existing
    g["nodes"].append(shaped)
    log_graph(g, f"node_created {shaped['id']}")
    return shaped


def upsert_edge(g: dict, edge: dict) -> dict:
    shaped = ensure_edge_shape(edge)
    if not find_node(g, shaped["src"]):
        raise HTTPException(status_code=400, detail=f"source node not found: {shaped['src']}")
    if not find_node(g, shaped["dst"]):
        raise HTTPException(status_code=400, detail=f"target node not found: {shaped['dst']}")
    for existing in g["edges"]:
        if existing.get("id") == shaped["id"]:
            shaped["created_at"] = existing.get("created_at", shaped["created_at"])
            existing.update(shaped)
            existing["last_access_time"] = utc_now()
            log_graph(g, f"edge_updated {shaped['id']}")
            return existing
    g["edges"].append(shaped)
    log_graph(g, f"edge_created {shaped['src']} -[{shaped['relation']}]-> {shaped['dst']}")
    return shaped


def aliases_for_node(node: dict) -> List[str]:
    out = [node.get("id", "")]
    attrs = node.get("attributes") or {}
    for key in ("alias", "aliases", "name", "value", "text"):
        val = attrs.get(key)
        if isinstance(val, str):
            out.append(val)
        elif isinstance(val, list):
            out.extend([str(x) for x in val if x])
    if node.get("execution"):
        out.append(node["execution"])
    return [x for x in out if x]


def tokenise(text: str) -> List[str]:
    words: List[str] = []
    try:
        import jieba  # type: ignore
        words.extend([w.strip() for w in jieba.lcut(text) if w.strip()])
    except Exception:
        pass
    words.extend(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{1,6}", text))
    seen = set()
    out = []
    for w in words:
        nw = norm_text(w)
        if nw and nw not in seen:
            seen.add(nw)
            out.append(w)
    return out

def ensure_activation_bounds(g: dict, r: dict) -> None:
    max_act = float(r["params"].get("max_activation", 2.0))
    for n in g["nodes"]:
        n["activation"] = clamp(float(n.get("activation", 0.0)), 0.0, max_act)
    for e in g["edges"]:
        e["activation"] = max(0.0, float(e.get("activation", 0.0)))


def inject_activation(g: dict, node_ids: List[str], value: float, reason: str, r: dict) -> List[str]:
    max_act = float(r["params"].get("max_activation", 2.0))
    hits = []
    for nid in node_ids:
        node = find_node(g, nid)
        if not node:
            continue
        node["activation"] = clamp(float(node.get("activation", 0.0)) + float(value), 0.0, max_act)
        node["last_access_time"] = utc_now()
        hits.append(node["id"])
    if hits:
        log_graph(g, f"activation_injected {hits} ({reason})")
    return hits


def parse_natural_language(text: str, g: dict) -> dict:
    original = str(text or "").strip()
    compact = re.sub(r"\s+", "", original)
    question_like = any(x in compact for x in ["?", "？", "什么", "多少", "为什么", "如何", "怎么", "谁", "哪"])

    nodes = [{"id": "Natural_Language_Input_Processor"}]
    edges = []
    notes = []

    patterns = [
        (r"(.+?)是(.+)", "is_a"),
        (r"(.+?)属于(.+)", "is_a"),
        (r"(.+?)有(.+)", "has"),
        (r"(.+?)包含(.+)", "contains"),
        (r"(.+?)使用(.+)", "uses"),
        (r"(.+?)导致(.+)", "causes"),
        (r"(.+?)触发(.+)", "triggers"),
        (r"(.+?)生成(.+)", "generates"),
    ]

    if not question_like:
        for pat, rel in patterns:
            m = re.search(pat, original)
            if m:
                src = norm_id(m.group(1).strip())
                dst = norm_id(m.group(2).strip())
                if src and dst:
                    nodes.extend([{"id": src}, {"id": dst}])
                    edges.append({"src": src, "dst": dst, "relation": rel})
                    notes.append(f"rule_extracted:{src}-{rel}->{dst}")
                    break

    for tok in tokenise(original)[:12]:
        nid = norm_id(tok)
        if nid:
            nodes.append({"id": nid})

    uniq_nodes = []
    seen = set()
    for n in nodes:
        nid = n["id"]
        if nid not in seen:
            seen.add(nid)
            uniq_nodes.append({"id": nid})

    uniq_edges = []
    seen_e = set()
    for e in edges:
        key = (e["src"], e["dst"], e["relation"])
        if key not in seen_e:
            seen_e.add(key)
            uniq_edges.append(e)

    return {
        "input": original,
        "question_like": question_like,
        "nodes": uniq_nodes,
        "edges": uniq_edges,
        "notes": notes,
        "parser": "rule_fallback",
    }

def spread_once(g: dict, r: dict) -> dict:
    params = r["params"]
    beta = float(params.get("spread_beta", 0.9))
    lam = float(params.get("decay_lambda", 0.15))
    threshold = float(params.get("activation_threshold", 0.12))
    max_act = float(params.get("max_activation", 2.0))
    contributions = defaultdict(float)
    contribution_log: List[dict] = []

    out_map: Dict[str, List[dict]] = defaultdict(list)
    for e in g["edges"]:
        out_map[e["src"]].append(e)

    active_sources = [n for n in g["nodes"] if float(n.get("activation", 0.0)) >= threshold]
    active_sources.sort(key=lambda x: float(x.get("activation", 0.0)), reverse=True)

    for src in active_sources:
        a = float(src.get("activation", 0.0))
        if a < threshold:
            continue
        outs = out_map.get(src["id"], [])
        if not outs:
            continue
        norm = max(1, len(outs))
        for e in outs:
            eff_weight = float(e.get("weight", 0.0)) + float(e.get("activation", 0.0))
            delta = a * eff_weight * beta / norm
            if delta <= 0:
                continue
            contributions[e["dst"]] += delta
            contribution_log.append({
                "src": src["id"],
                "dst": e["dst"],
                "relation": e["relation"],
                "delta": round(delta, 6),
            })

    for n in g["nodes"]:
        current = float(n.get("activation", 0.0))
        new_value = (1.0 - lam) * current + contributions.get(n["id"], 0.0)
        n["activation"] = clamp(new_value, 0.0, max_act)
        if contributions.get(n["id"], 0.0) > 0:
            n["last_access_time"] = utc_now()

    for e in g["edges"]:
        e["activation"] = max(0.0, float(e.get("activation", 0.0)) * (1.0 - lam * 0.5))

    active_after = [n["id"] for n in g["nodes"] if float(n.get("activation", 0.0)) >= threshold]
    return {
        "contribution_log": contribution_log,
        "active_after": active_after,
        "stopped": len(active_after) == 0,
    }


def spread_round(g: dict, r: dict, steps: int = 1) -> dict:
    trace = []
    for i in range(max(1, steps)):
        step_info = spread_once(g, r)
        trace.append({"step": i + 1, **step_info})
        if step_info["stopped"]:
            break
    ensure_activation_bounds(g, r)
    return {"trace": trace}


def compute_top_k(g: dict, r: dict) -> dict:
    top_k = int(r["params"].get("top_k", 6))
    result_limit = int(r["params"].get("result_limit", 6))
    nodes_sorted = sorted(g["nodes"], key=lambda n: (float(n.get("activation", 0.0)), float(n.get("weight", 0.0))), reverse=True)
    picked = nodes_sorted[:top_k]
    picked_ids = {n["id"] for n in picked}
    related_edges = [e for e in g["edges"] if e["src"] in picked_ids or e["dst"] in picked_ids]
    related_edges.sort(key=lambda e: (float(e.get("activation", 0.0)), float(e.get("weight", 0.0))), reverse=True)
    return {"top_k_nodes": picked[:result_limit], "related_edges": related_edges[: max(result_limit * 4, len(related_edges))]}


def execute_procedural_nodes(g: dict, r: dict, selected_nodes: List[dict]) -> List[dict]:
    threshold = float(r["params"].get("action_threshold", 1.0))
    results: List[dict] = []

    def run_builtin(node: dict) -> dict:
        code = str(node.get("execution") or "")
        if code == "builtin:natural_language_input":
            return {"status": "ok", "message": "自然语言感知器节点已激活"}
        return {"status": "skipped", "message": f"未知内建执行器: {code}"}

    for n in sorted(selected_nodes, key=lambda x: float(x.get("activation", 0.0)), reverse=True):
        if n.get("label") != "procedural":
            continue
        if float(n.get("activation", 0.0)) < threshold:
            continue
        exec_spec = str(n.get("execution") or "").strip()
        try:
            if exec_spec.startswith("builtin:"):
                out = run_builtin(n)
            else:
                local_ctx = {"graph": g, "node": n, "runtime": r, "result": None}
                exec(exec_spec, {}, local_ctx)
                out = {"status": "ok", "result": local_ctx.get("result")}
            results.append({"node_id": n["id"], "execution": exec_spec, "output": out})
            result_node_id = f"Result_{n['id']}_{int(time.time()*1000)}"
            result_node = {
                "id": result_node_id,
                "weight": 0.3,
                "activation": 0.0,
                "last_access_time": utc_now(),
                "created_at": utc_now(),
                "label": "declarative-episodic",
                "execution": "",
                "attributes": {"source_action": n["id"], "execution_output": out},
            }
            upsert_node(g, result_node)
            upsert_edge(g, {
                "src": n["id"],
                "dst": result_node_id,
                "relation": "produced",
                "weight": 0.7,
                "activation": 0.2,
                "attributes": {"write_back": True},
            })
            n["activation"] = max(0.0, float(n.get("activation", 0.0)) * 0.25)
            n["last_access_time"] = utc_now()
        except Exception as exc:
            results.append({"node_id": n["id"], "execution": exec_spec, "error": str(exc)})
    if results:
        log_graph(g, f"procedural_execution {len(results)}")
    return results


def graph_view(g: dict, r: dict) -> dict:
    topk = compute_top_k(g, r)
    return {
        "meta": g.get("meta", {}),
        "nodes": g.get("nodes", []),
        "edges": g.get("edges", []),
        "top_k": topk["top_k_nodes"],
        "related_edges": topk["related_edges"],
        "logs": g.get("logs", [])[:200],
    }


class NodeIn(BaseModel):
    id: str
    weight: float = 0.0
    activation: float = 0.0
    label: str = "declarative-semantic"
    execution: str = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)


class EdgeIn(BaseModel):
    src: str
    dst: str
    relation: str = "related_to"
    weight: float = 0.0
    activation: float = 0.0
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphImportIn(BaseModel):
    payload: Dict[str, Any]
    mode: str = "merge"


class ActivateIn(BaseModel):
    node_ids: List[str] = Field(default_factory=list)
    value: float = 1.0
    reason: str = "manual"


class SpreadIn(BaseModel):
    steps: int = Field(1, ge=1, le=32)


class NaturalInputIn(BaseModel):
    text: str = Field(..., min_length=1)
    seed_value: float = Field(1.0, ge=0.0, le=10.0)
    spread_steps: int = Field(3, ge=0, le=32)
    auto_execute: bool = True


class RuntimeParamIn(BaseModel):
    initial_match_activation: Optional[float] = None
    match_decay: Optional[float] = None
    spread_beta: Optional[float] = None
    decay_lambda: Optional[float] = None
    activation_threshold: Optional[float] = None
    max_activation: Optional[float] = None
    top_k: Optional[int] = None
    result_limit: Optional[int] = None
    action_threshold: Optional[float] = None
    activation_floor: Optional[float] = None
    realtime_interval_ms: Optional[int] = None
    max_spread_steps: Optional[int] = None
    natural_language_seed_id: Optional[str] = None

loop_thread: Optional[threading.Thread] = None
stop_event = threading.Event()


def _runtime_tick() -> dict:
    g = load_graph()
    r = load_runtime()
    if r["loop"].get("auto_spread", True):
        spread_round(g, r, steps=1)
    topk = compute_top_k(g, r)
    r["top_k"] = topk["top_k_nodes"]
    r["focus"] = topk["top_k_nodes"][0] if topk["top_k_nodes"] else None
    if r["loop"].get("auto_execute_actions", True):
        r["last_action_result"] = execute_procedural_nodes(g, r, topk["top_k_nodes"])
    r["loop"]["tick_count"] = int(r["loop"].get("tick_count", 0)) + 1
    r["loop"]["last_tick_at"] = utc_now()
    save_graph(g)
    save_runtime(r)
    return {"graph": graph_view(g, r), "runtime": r}


def _loop_worker() -> None:
    while not stop_event.is_set():
        try:
            _runtime_tick()
        except Exception:
            pass
        r = load_runtime()
        interval_ms = int(r["params"].get("realtime_interval_ms", 800))
        stop_event.wait(max(0.1, interval_ms / 1000.0))

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # 应用在此处运行
app = FastAPI(lifespan=lifespan)

app = FastAPI(title="Unified Knowledge Graph Prototype", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 👈 改为 False (或者直接删掉这行，默认就是 False)
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "time": utc_now()}

@app.post("/api/natural/process")
def api_natural_process(payload: NaturalInputIn) -> dict:
    g = load_graph()
    r = load_runtime()
    raw_text = payload.text
    parsed = nlp.process_text(raw_text)

    scoring = score_initial_activations(payload.text, parsed, g, r)

    for item in parsed.get("nodes", []):
        nid = norm_id(item.get("id"))

    for e in parsed.get("edges", []):
        src = norm_id(e["src"])
        dst = norm_id(e["dst"])

    for nid, val in scoring["activations"].items():
        node = find_node(g, nid)
        if node:
            node["activation"] = clamp(max(float(node.get("activation", 0.0)), float(val)), 0.0, float(r["params"]["max_activation"]))
            node["last_access_time"] = utc_now()

    trace = spread_round(g, r, steps=int(payload.spread_steps))
    topk = compute_top_k(g, r)
    r["top_k"] = topk["top_k_nodes"]
    r["focus"] = topk["top_k_nodes"][0] if topk["top_k_nodes"] else None
    r["last_parse"] = parsed

    action_results = []
    if payload.auto_execute:
        action_results = execute_procedural_nodes(g, r, topk["top_k_nodes"])
    r["last_action_result"] = action_results

    save_runtime(r)
    log_runtime(r, f"natural_process {payload.text[:48]}")
    save_runtime(r)
    seed_hits = parsed.get("nodes", [])

    return {
        "input": payload.text,
        "seed_nodes": seed_hits,
        "parsed": parsed,
        "initial_activation": scoring,
        "spread_trace": trace["trace"],
        "top_k": topk["top_k_nodes"],
        "related_edges": topk["related_edges"],
        "action_results": action_results,
        "graph": graph_view(g, r),
        "runtime": r,
    }

@app.get("/api/schema")
def api_schema() -> dict:
    return read_json(SCHEMA_FILE, default_schema())


@app.get("/api/runtime")
def api_runtime() -> dict:
    return load_runtime()


@app.post("/api/runtime/params")
def api_runtime_params(payload: RuntimeParamIn) -> dict:
    r = load_runtime()
    for k, v in payload.model_dump(exclude_none=True).items():
        if k in r["params"]:
            r["params"][k] = v
    save_runtime(r)
    return r


@app.post("/api/runtime/activate")
def api_activate(payload: ActivateIn) -> dict:
    g = load_graph()
    r = load_runtime()
    hits = inject_activation(g, payload.node_ids, payload.value, payload.reason, r)
    save_graph(g)
    topk = compute_top_k(g, r)
    r["top_k"] = topk["top_k_nodes"]
    r["focus"] = topk["top_k_nodes"][0] if topk["top_k_nodes"] else None
    save_runtime(r)
    return {"activated": hits, "graph": graph_view(g, r), "runtime": r}


@app.post("/api/runtime/spread")
def api_spread(payload: SpreadIn) -> dict:
    g = load_graph()
    r = load_runtime()
    trace = spread_round(g, r, payload.steps)
    topk = compute_top_k(g, r)
    r["top_k"] = topk["top_k_nodes"]
    r["focus"] = topk["top_k_nodes"][0] if topk["top_k_nodes"] else None
    save_graph(g)
    save_runtime(r)
    return {"trace": trace["trace"], "graph": graph_view(g, r), "runtime": r}


@app.post("/api/runtime/tick")
def api_tick() -> dict:
    return _runtime_tick()


@app.post("/api/runtime/start")
def api_start() -> dict:
    global loop_thread
    r = load_runtime()
    if r["loop"].get("running"):
        return {"running": True}
    stop_event.clear()
    r["loop"]["running"] = True
    save_runtime(r)
    loop_thread = threading.Thread(target=_loop_worker, daemon=True)
    loop_thread.start()
    return {"running": True}


@app.post("/api/runtime/stop")
def api_stop() -> dict:
    r = load_runtime()
    r["loop"]["running"] = False
    save_runtime(r)
    stop_event.set()
    return {"running": False}


@app.get("/api/graph")
def api_graph() -> dict:
    g = load_graph()
    r = load_runtime()
    topk = compute_top_k(g, r)
    r["top_k"] = topk["top_k_nodes"]
    r["focus"] = topk["top_k_nodes"][0] if topk["top_k_nodes"] else None
    save_runtime(r)
    return graph_view(g, r)


@app.post("/api/graph/reset")
def api_graph_reset() -> dict:
    g = default_graph()
    r = default_runtime()
    save_graph(g)
    save_runtime(r)
    return {"graph": graph_view(g, r), "runtime": r}


@app.post("/api/node")
def api_node(payload: NodeIn) -> dict:
    g = load_graph()
    node = upsert_node(g, payload.model_dump())
    save_graph(g)
    r = load_runtime()
    return {"node": node, "graph": graph_view(g, r)}


@app.post("/api/edge")
def api_edge(payload: EdgeIn) -> dict:
    g = load_graph()
    edge = upsert_edge(g, payload.model_dump())
    save_graph(g)
    r = load_runtime()
    return {"edge": edge, "graph": graph_view(g, r)}


@app.delete("/api/node/{node_id}")
def api_delete_node(node_id: str) -> dict:
    g = load_graph()
    nid = norm_id(node_id)
    before = len(g["nodes"])
    g["nodes"] = [n for n in g["nodes"] if n["id"] != nid]
    g["edges"] = [e for e in g["edges"] if e["src"] != nid and e["dst"] != nid]
    if len(g["nodes"]) == before:
        raise HTTPException(status_code=404, detail="node not found")
    log_graph(g, f"node_deleted {nid}")
    save_graph(g)
    r = load_runtime()
    return {"ok": True, "graph": graph_view(g, r)}


@app.delete("/api/edge/{edge_id}")
def api_delete_edge(edge_id: str) -> dict:
    g = load_graph()
    before = len(g["edges"])
    g["edges"] = [e for e in g["edges"] if e["id"] != edge_id]
    if len(g["edges"]) == before:
        raise HTTPException(status_code=404, detail="edge not found")
    log_graph(g, f"edge_deleted {edge_id}")
    save_graph(g)
    r = load_runtime()
    return {"ok": True, "graph": graph_view(g, r)}


@app.post("/api/graph/import")
def api_import_graph(payload: GraphImportIn) -> dict:
    g = load_graph()
    mode = payload.mode.lower().strip()
    data = payload.payload
    if mode == "replace":
        g = default_graph()
    if isinstance(data.get("nodes"), list):
        for n in data["nodes"]:
            upsert_node(g, n)
    if isinstance(data.get("edges"), list):
        for e in data["edges"]:
            try:
                upsert_edge(g, e)
            except HTTPException:
                upsert_node(g, {"id": e.get("src"), "label": "declarative-semantic"})
                upsert_node(g, {"id": e.get("dst"), "label": "declarative-semantic"})
                upsert_edge(g, e)
    save_graph(g)
    r = load_runtime()
    return {"graph": graph_view(g, r), "mode": mode}

@app.get("/api/export")
def api_export() -> dict:
    return {"graph": load_graph(), "runtime": load_runtime(), "schema": read_json(SCHEMA_FILE, default_schema())}


@app.get("/api/logs")from __future__ import annotations
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# --- 配置与工具函数 ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GRAPH_FILE = DATA_DIR / "knowledge_graph.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path, default: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_json(path, default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"读取JSON失败: {e}, 使用默认值")
        return default.copy()

def write_json(path: Path, obj: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return obj

def clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))

def norm_text(s: str) -> str:
    s = str(s or "").strip().lower()
    s = re.sub(r"[\s\-_\/\\:;，,。.!！？?【】\[\]{}()<>\'\"“”‘’`~]+", "", s)
    return s

def norm_id(s: str) -> str:
    raw = str(s or "").strip()
    if not raw:
        return "Unknown"
    raw = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw or "Unknown"

# --- 知识图谱定义 (根据论文修正) ---
def default_graph() -> dict:
    t = utc_now()
    return {
        "meta": {
            "name": "Unified Knowledge Graph",
            "version": "1.0",
            "created_at": t,
            "updated_at": t,
        },
        "nodes": [],
        "edges": [],
        "logs": [],
    }

def ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not GRAPH_FILE.exists():
        write_json(GRAPH_FILE, default_graph())

ensure_store()

def load_graph() -> dict:
    g = read_json(GRAPH_FILE, default_graph())
    g.setdefault("meta", {})
    g.setdefault("nodes", [])
    g.setdefault("edges", [])
    g.setdefault("logs", [])
    g["meta"]["updated_at"] = utc_now()
    return g

def save_graph(g: dict) -> dict:
    g["meta"]["updated_at"] = utc_now()
    return write_json(GRAPH_FILE, g)

def log_graph(g: dict, msg: str) -> None:
    log_entry = f"{utc_now()} | {msg}"
    g.setdefault("logs", [])
    g["logs"].insert(0, log_entry)
    g["logs"] = g["logs"][:500] # 保留最近500条

# --- 节点与边结构修正 (符合论文定义) ---
def ensure_node_shape(node: dict) -> dict:
    now = utc_now()
    # 移除了自认知相关的字段，严格按Prompt定义
    return {
        "id": norm_id(node.get("id", "Unknown")),
        "权重": float(node.get("权重", 1.0)), # [-2, 2]
        "运行时激活度": float(node.get("运行时激活度", 0.0)), # [0, +inf]
        "最后访问时间": node.get("最后访问时间") or now,
        "创建时间": node.get("创建时间") or now,
        "标签": str(node.get("标签", "declarative-semantic")),
        "执行": str(node.get("执行", "")),
        "附加属性": dict(node.get("附加属性") or {}),
    }

def ensure_edge_shape(edge: dict) -> dict:
    now = utc_now()
    return {
        "起点": norm_id(edge.get("起点")),
        "终点": norm_id(edge.get("终点")),
        "关系描述": str(edge.get("关系描述", "related_to")),
        "最后访问时间": edge.get("最后访问时间") or now,
        "创建时间": edge.get("创建时间") or now,
        "权重": float(edge.get("权重", 1.0)),
        "运行时激活度": float(edge.get("运行时激活度", 0.0)),
        "附加属性": dict(edge.get("附加属性") or {}),
    }

def upsert_node(g: dict, node_data: dict) -> dict:
    node = ensure_node_shape(node_data)
    node_id = node["id"]

    # 检查是否已存在
    for existing in g["nodes"]:
        if existing["id"] == node_id:
            # 保留创建时间，更新其他字段
            node["创建时间"] = existing["创建时间"]
            existing.update(node)
            existing["最后访问时间"] = utc_now()
            log_graph(g, f"节点更新: {node_id}")
            return existing

    g["nodes"].append(node)
    log_graph(g, f"节点创建: {node_id}")
    return node

def upsert_edge(g: dict, edge_data: dict) -> dict:
    edge = ensure_edge_shape(edge_data)

    # 确保起点和终点存在
    src_id = edge["起点"]
    dst_id = edge["终点"]
    if not any(n["id"] == src_id for n in g["nodes"]):
        upsert_node(g, {"id": src_id, "标签": "declarative-semantic"})
    if not any(n["id"] == dst_id for n in g["nodes"]):
        upsert_node(g, {"id": dst_id, "标签": "declarative-semantic"})

    # 检查是否已存在 (基于起点+终点+关系)
    edge_key = (edge["起点"], edge["终点"], edge["关系描述"])
    for existing in g["edges"]:
        ex_key = (existing["起点"], existing["终点"], existing["关系描述"])
        if ex_key == edge_key:
            edge["创建时间"] = existing["创建时间"]
            existing.update(edge)
            existing["最后访问时间"] = utc_now()
            log_graph(g, f"边更新: {edge_key}")
            return existing

    g["edges"].append(edge)
    log_graph(g, f"边创建: {edge_key}")
    return edge

# --- 主扩散逻辑 (核心重写) ---
class SpreadEngine:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        # 超参数 (可后续通过API调整)
        self.params = {
            "initial_match_activation": 1.0, # 初始激活度
            "spread_gain": 0.8,             # 扩散增益 Beta
            "decay_lambda": 0.15,          # 衰减系数 Lambda
            "activation_threshold": 0.1,     # 扩散停止阈值
            "top_k": 5,                    # 选取K个节点
            "cosine_threshold": 0.4,        # 语义匹配阈值 (虽然Prompt要求Embedding, 但原代码有本地缓存逻辑冲突, 此处先保留基础ID匹配, 见下方注释)
        }

    def inject_activation(self, g: dict, input_nodes: List[str]):
        """根据输入集合注入初始激活度"""
        activated = []
        for item in input_nodes:
            node = next((n for n in g["nodes"] if n["id"] == item), None)
            if node:
                base_act = self.params["initial_match_activation"]
                weight = node["权重"]
                node["运行时激活度"] = base_act * weight
                node["最后访问时间"] = utc_now()
                activated.append(node["id"])
            # Note: 根据Prompt要求，这里应该调用中文词义嵌入模型做余弦相似度匹配。
            # 但是原代码中的 semantic_matcher.py 包含了复杂的缓存和全局锁，且依赖未提供的模型文件。
            # 为了保持代码纯净且不引入外部依赖错误，此处暂只实现精确匹配逻辑。
            # 若需实现Embedding匹配，请单独提供或重构 semantic_matcher 逻辑。
        return activated

    def spread_once(self, g: dict) -> Dict[str, Any]:
        """执行一步扩散"""
        beta = self.params["spread_gain"]
        contributions = {}

        # 计算贡献
        for node in g["nodes"]:
            current_act = node["运行时激活度"]
            # 只有高于阈值的节点才扩散
            if current_act < self.params["activation_threshold"]:
                continue

            # 遍历该节点发出的边
            out_edges = [e for e in g["edges"] if e["起点"] == node["id"]]
            if not out_edges:
                continue

            # 归一化权重 (防止出度多的节点激活度过大)
            total_weight = sum(e["权重"] for e in out_edges)
            if total_weight == 0:
                continue

            for edge in out_edges:
                # 有效权重 = 边权重 * 节点当前激活度
                eff_weight = edge["权重"] * current_act
                # 传播增量 = 激活度 * 边权重 * 增益 / 总权重 (归一化)
                delta = (current_act * edge["权重"] * beta) / (total_weight + 1e-8)

                if edge["终点"] not in contributions:
                    contributions[edge["终点"]] = 0
                contributions[edge["终点"]] += delta

        # 应用贡献并衰减
        new_activations = 0
        for node in g["nodes"]:
            old_act = node["运行时激活度"]
            # 衰减: (1-lambda) * 当前激活度
            decayed = (1 - self.params["decay_lambda"]) * old_act
            # 加上新贡献
            new_act = decayed + contributions.get(node["id"], 0)

            node["运行时激活度"] = max(0.0, new_act) # 激活度不能为负
            node["最后访问时间"] = utc_now()

            if new_act > self.params["activation_threshold"]:
                new_activations += 1

        return {"new_activations": new_activations}

    def decay_only(self, g: dict):
        """仅执行衰减 (扩散结束后)"""
        for node in g["nodes"]:
            node["运行时激活度"] = (1 - self.params["decay_lambda"]) * node["运行时激活度"]
        log_graph(g, "执行衰减操作")

    def get_top_k_nodes(self, g: dict) -> List[Dict]:
        """选取K个激活度最高的节点"""
        sorted_nodes = sorted(
            g["nodes"],
            key=lambda x: x["运行时激活度"],
            reverse=True
        )
        return sorted_nodes[:self.params["top_k"]]

    def get_related_edges(self, g: dict, node_ids: List[str]) -> List[Dict]:
        """获取节点间相关的边"""
        node_set = set(node_ids)
        related = []
        for edge in g["edges"]:
            if edge["起点"] in node_set and edge["终点"] in node_set:
                related.append(edge)
        return related

    def execute_procedural(self, g: dict, top_k_nodes: List[Dict]) -> List[str]:
        """执行程序性记忆节点 (按激活度顺序)"""
        results = []
        # 按运行时激活度排序
        sorted_nodes = sorted(top_k_nodes, key=lambda x: x["运行时激活度"], reverse=True)

        for node in sorted_nodes:
            if node["标签"] != "procedural":
                continue
            if node["运行时激活度"] < self.params["activation_threshold"]:
                continue

            code = node.get("执行", "").strip()
            if not code:
                continue

            try:
                # 准备执行环境
                local_env = {"graph": g, "node": node, "print": print}
                # 注意：exec 是危险的，仅用于演示。实际生产中应使用沙箱。
                exec(code, local_env)
                results.append(f"执行成功: {node['id']}")
                # 执行后重置激活度或降低
                node["运行时激活度"] = 0.0
            except Exception as e:
                results.append(f"执行错误: {node['id']} - {str(e)}")

        return results

    def spread_loop(self):
        """实时扩散循环"""
        while self.running:
            g = load_graph()
            self.spread_once(g)
            save_graph(g)
            time.sleep(1) # 控制频率

    def start_loop(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.spread_loop, daemon=True)
            self.thread.start()

    def stop_loop(self):
        self.running = False

# 全局引擎实例
spread_engine = SpreadEngine()

# --- FastAPI 接口 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    spread_engine.stop_loop()

app = FastAPI(lifespan=lifespan)

class NodeIn(BaseModel):
    id: str
    权重: float = Field(1.0, ge=-2.0, le=2.0)
    标签: str = "declarative-semantic"
    执行: str = ""
    附加属性: Dict[str, Any] = Field(default_factory=dict)

class EdgeIn(BaseModel):
    起点: str
    终点: str
    关系描述: str
    权重: float = 1.0

class SpreadInput(BaseModel):
    nodes: List[str] # 输入的节点ID集合

@app.post("/api/node")
def api_node(payload: NodeIn):
    g = load_graph()
    upsert_node(g, payload.dict())
    save_graph(g)
    return {"status": "ok"}

@app.post("/api/edge")
def api_edge(payload: EdgeIn):
    g = load_graph()
    upsert_edge(g, payload.dict())
    save_graph(g)
    return {"status": "ok"}

@app.post("/api/spread")
def api_spread(payload: SpreadInput):
    g = load_graph()

    # 1. 注入初始激活
    spread_engine.inject_activation(g, payload.nodes)

    # 2. 执行扩散过程 (此处简化为多步扩散直到稳定或达到上限)
    for _ in range(10): # 最大步数限制
        result = spread_engine.spread_once(g)
        if result["new_activations"] == 0:
            break

    # 3. 扩散结束后执行衰减
    spread_engine.decay_only(g)

    # 4. 选取 Top-K
    top_k_nodes = spread_engine.get_top_k_nodes(g)
    related_edges = spread_engine.get_related_edges(g, [n["id"] for n in top_k_nodes])

    # 5. 执行程序性节点
    exec_results = spread_engine.execute_procedural(g, top_k_nodes)

    save_graph(g)

    return {
        "top_k": top_k_nodes,
        "edges": related_edges,
        "execution": exec_results,
        "graph_snapshot": g
    }

@app.get("/api/graph")
def api_graph():
    return load_graph()

@app.post("/api/control/start")
def api_control_start():
    spread_engine.start_loop()
    return {"status": "running"}

@app.post("/api/control/stop")
def api_control_stop():
    spread_engine.stop_loop()
    return {"status": "stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
def api_logs() -> dict:
    return {"graph_logs": load_graph().get("logs", [])[:200], "runtime_logs": load_runtime().get("logs", [])[:200]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
