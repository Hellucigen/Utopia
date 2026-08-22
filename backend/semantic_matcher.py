"""
文件名：semantic_matcher.py
功能：语义匹配器（向量检索为主 + 规则逻辑兜底）
流程：输入文本 -> 向量检索(第一层) -> 若无结果 -> 原生规则匹配(第二层)
"""

import json
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, util  # type: ignore

from app import load_graph, norm_text, node_match_score, DATA_DIR, read_json, write_json

# --- 配置区 ---
# 模型名称：推荐使用中文优化的 BGE 模型
MODEL_NAME = "BAAI/bge-m3"
# 如果离线使用，请替换为本地模型文件夹路径，例如： "./models/bge-m3"
VECTOR_CACHE_FILE = DATA_DIR / "node_vector_cache.json"

# 全局变量与锁
embedding_model = None
_model_lock = threading.Lock()
_cache_lock = threading.RLock()

def get_model():
    """单例模式加载模型，线程安全"""
    global embedding_model
    with _model_lock:
        if embedding_model is None:
            print("正在加载 Embedding 模型，请稍候...")
            try:
                embedding_model = SentenceTransformer(MODEL_NAME)
                print(f"模型 {MODEL_NAME} 加载成功！")
            except Exception as e:
                print(f"模型加载失败: {e}。将仅使用规则模式运行。")
                embedding_model = None
        return embedding_model

def _build_and_cache_vectors() -> Optional[Dict[str, List[float]]]:
    """
    遍历图谱构建节点向量，并缓存到文件。
    返回: {node_id: embedding_vector}
    """
    g = load_graph()
    model = get_model()
    if model is None:
        return None

    embeddings: Dict[str, List[float]] = {}
    print("正在为知识图谱节点构建向量缓存...")

    for node in g.get("nodes", []):
        nid = node["id"]
        # 构造节点的文本表示（ID + 属性）
        text_parts = [nid]
        attrs = node.get("attributes", {})
        for k, v in attrs.items():
            if isinstance(v, str):
                text_parts.append(v)
            elif isinstance(v, list):
                text_parts.extend([str(x) for x in v])
        full_text = " ".join(text_parts)

        # 生成向量
        emb = model.encode(full_text, convert_to_numpy=True)
        # 转为列表以便 JSON 序列化
        embeddings[nid] = emb.tolist()

    # 缓存写入
    try:
        with _cache_lock:
            write_json(VECTOR_CACHE_FILE, embeddings)
        print(f"向量缓存构建完成，共处理 {len(embeddings)} 个节点。")
    except Exception as e:
        print(f"警告：缓存写入失败 {e}")

    return embeddings

def _load_cached_vectors() -> Optional[Dict[str, List[float]]]:
    """从文件加载向量缓存"""
    if not VECTOR_CACHE_FILE.exists():
        return None
    try:
        with _cache_lock:
            data = read_json(VECTOR_CACHE_FILE, {})
        # 验证数据结构
        if isinstance(data, dict) and data:
            # 简单验证：检查第一个值是否为列表
            for v in data.values():
                if isinstance(v, list):
                    return data
    except Exception as e:
        print(f"加载缓存失败: {e}")
    return None

def vector_search(text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    第一层匹配：向量语义检索
    """
    model = get_model()
    if model is None:
        print("【调试】模型未加载，跳过向量检索。")
        return []

    # 尝试加载缓存，如果没有则构建
    node_embeddings = _load_cached_vectors()
    if not node_embeddings:
        node_embeddings = _build_and_cache_vectors()
    if not node_embeddings:
        return []

    # 1. 将输入文本转为向量
    try:
        input_emb = model.encode(text, convert_to_numpy=True)
        input_emb = input_emb.reshape(1, -1) # 转为 2D 数组
    except Exception as e:
        print(f"编码输入失败: {e}")
        return []

    # 2. 计算余弦相似度
    results = []
    for node_id, vec_list in node_embeddings.items():
        node_vec = np.array(vec_list).reshape(1, -1)
        # 计算相似度
        cos_sim = util.cos_sim(input_emb, node_vec).item()

        # 设定阈值（BGE 模型通常 0.4-0.6 为相关）
        if cos_sim > 0.4:
            results.append({
                "id": node_id,
                "score": float(cos_sim),
                "method": "vector_semantic"
            })

    # 3. 排序取 Top-K
    results.sort(key=lambda x: x["score"], reverse=True)

    # --- 调试输出 ---
    print(f"\n【调试-向量检索】输入: '{text}'")
    print(f"【调试-向量检索】找到 {len(results)} 个语义匹配项:")
    for res in results[:3]: # 仅打印前3个
        print(f"   - 节点: {res['id']} | 相似度: {res['score']:.3f} (语义)")
    # --- 调试结束 ---

    return results[:top_k]

def rule_based_fallback(text: str, g: Dict, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    第二层匹配：原有的规则逻辑兜底
    """
    hits = []
    for node in g.get("nodes", []):
        score = node_match_score(text, node)
        if score >= 0.2: # 原有阈值
            hits.append({
                "id": node["id"],
                "score": score,
                "method": "rule_exact"
            })

    hits.sort(key=lambda x: x["score"], reverse=True)

    # --- 调试输出 ---
    print(f"\n【调试-规则兜底】输入: '{text}'")
    print(f"【调试-规则兜底】找到 {len(hits)} 个规则匹配项:")
    for res in hits[:3]:
        print(f"   - 节点: {res['id']} | 相似度: {res['score']:.3f} (规则)")
    # --- 调试结束 ---

    return hits[:top_k]

def unified_match(text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    统一匹配接口
    逻辑：先向量 -> 无结果则规则
    """
    g = load_graph()
    text = norm_text(text)

    # 1. 尝试向量检索
    vector_results = vector_search(text, top_k)

    if vector_results:
        print(f"【结果】向量检索命中，返回 {len(vector_results)} 个结果。")
        return vector_results

    # 2. 向量无果，使用规则兜底
    print(f"【结果】向量检索无匹配，触发规则兜底。")
    fallback_results = rule_based_fallback(text, g, top_k)

    print(f"【结果】规则兜底返回 {len(fallback_results)} 个结果。")
    return fallback_results