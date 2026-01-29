# nl_driven_activation.py
# Simplified: only extract_keywords, no class since not used interactively.

import re
import jieba
from typing import List

def extract_keywords(text: str) -> List[str]:
    if re.search(r'[\u4e00-\u9fff]', text):
        words = jieba.lcut(text.lower())
    else:
        words = re.findall(r'\b\w{2,}\b', text.lower())
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "in", "on", "at", "to", "for", "of", "and", "or", "but", "的", "是", "在", "和", "或", "但", "我", "你", "他", "她"}
    keywords = [w for w in words if w not in stopwords and len(w) >= 2]
    return list(dict.fromkeys(keywords))