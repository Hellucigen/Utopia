# utils.py
import hashlib

def normalize_concept(name: str) -> str:
    name = name.strip().lower()
    # 简单单数化（可扩展用inflect库，如果安装）
    if name.endswith('s') and not name.endswith('ss'):
        name = name[:-1]
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def generate_node_id(name: str, node_type: str = "Concept") -> str:
    norm_name = normalize_concept(name).replace(' ', '_')
    hash_suffix = hashlib.md5(norm_name.encode()).hexdigest()[:8]
    return f"{node_type}_{norm_name}_{hash_suffix}"