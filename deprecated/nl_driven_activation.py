import requests
import json
import re
from utils import normalize_concept, generate_node_id

# === 配置 ===
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi4"  # 或你实际使用的模型名


def extract_triples_from_text(text: str) -> list:
    prompt = (
        "You are a cognitive interface that translates user utterances into semantic triples for an attention-based reasoning system.\n\n"
        "Rules:\n"
        "- Output ONLY a valid JSON list of lists: [[\"head\", \"relation\", \"tail\"]]\n"
        "- Extract the user's intent, action, or focus — even if subjective or emotional.\n"
        "- Prioritize 'User' as head for user inputs (e.g., if input is 'Water', use ['User', 'REFERS_TO', 'Water'])\n"
        "- For questions or asks, always include a triple linking to 'Ask' concept if relevant (e.g., ['User', 'PERFORMS', 'Ask'], ['Ask', 'ABOUT', 'Topic'])\n"
        "- head/tail must be atomic (1–3 words), normalized to Title Case (e.g., 'Ask', 'System Name'). Use singular nouns.\n"
        "- ALLOW first-person context when meaningful (e.g., \"User\" as head).\n"
        "- NEVER use raw pronouns like \"I\", \"her\", \"you\" — replace with roles:\n"
        "• \"I\" / \"me\" → \"User\"\n"
        "• \"you\" / \"your\" → \"System\"\n"
        "• \"she\"/\"he\"/\"her\"/\"him\" → \"Person\" (or specific name if known)\n"
        "- Relations must be clear, uppercase, underscored actions or states:\n"
        "  e.g., PERFORMS, USED_TO, ASKS_ABOUT, REFERS_TO, IS. Match existing relations like USED_TO if possible.\n"
        "- DO infer plausible relations from verbs/adjectives (e.g., \"ask\" → PERFORMS_ASK or USED_TO_ASK)\n"
        "- If query is about name or identity, link to 'Name' and 'Ask' (e.g., ['User', 'ASKS_ABOUT', 'System Name'], ['Ask', 'LEADS_TO', 'Answer'])\n"
        "- If no meaningful semantic content (e.g., \"um\", \"hello\"), output []\n\n"
        f"Text: {text}\n\nTriples:"
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3}
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=20)
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip()
            print(f"Raw LLM response for '{text}': {repr(result)}")  # 始终显示raw，便于debug

            # 🧼 清洗可能的 Markdown 代码块包裹（如 ```json ... ```）
            cleaned_result = re.sub(r'^```(?:json)?\s*', '', result, flags=re.IGNORECASE)
            cleaned_result = re.sub(r'\s*```$', '', cleaned_result)
            cleaned_result = cleaned_result.strip()

            # 尝试解析 JSON
            try:
                triples = json.loads(cleaned_result)
                # 确保是列表结构
                if isinstance(triples, list):
                    return triples
                else:
                    print("⚠️ Parsed JSON is not a list:", cleaned_result)
                    return []
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON after cleaning. Raw LLM output:")
                print(repr(result))
                return []
        else:
            print(f"⚠️ Ollama API error: {resp.status_code} - {resp.text}")
            return []
    except Exception as e:
        print(f"❌ Exception during Ollama request: {e}")
        return []


# === 示例用法 ===
if __name__ == "__main__":
    user_input = "I just eat a apple"
    triples = extract_triples_from_text(user_input)
    print("Extracted triples:", triples)