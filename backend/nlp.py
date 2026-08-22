import json
import jieba
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List


# ==========================================
# 1. 定义输出的数据结构 (严格按Prompt要求)
# ==========================================
class Node(BaseModel):
    id: str = Field(description="实体或节点的名称")


class Edge(BaseModel):
    起点: str = Field(description="边的起始节点名称")
    终点: str = Field(description="边的目标节点名称")
    关系描述: str = Field(description="两个节点之间的关系描述")


class NLPResult(BaseModel):
    nodes: List[Node] = Field(description="从文本中提取的实体列表")
    edges: List[Edge] = Field(description="从文本中提取的关系三元组列表")
    言外行为: str = Field(
        description="文本的言外行为分类",
        enum=["断言类", "指令类", "承诺类", "表达类", "宣告类"]  # 严格按Prompt要求的三个字
    )


# ==========================================
# 2. 初始化 LLM 组件
# ==========================================
llm = ChatOllama(
    model="qwen2.5",  # 确保你已 ollama pull qwen2.5
    temperature=0,
    format="json"  # 强制JSON输出
)

parser = JsonOutputParser(pydantic_object=NLPResult)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的自然语言处理助手。任务是提取实体和关系，并分类言外行为。"),
    ("user", """分析以下文本：
**原始文本**: {text}
**分词结果**: {tokens}

请遵循规则：
1. 提取关键实体作为节点 (Nodes)。
2. 识别关系形成边 (Edges)。
3. 将文本分类为以下五大言外行为之一：
   - 断言类: 陈述事实、描述状态。
   - 指令类: 试图让听话人做某事。
   - 承诺类: 对自己未来的某种行为做出承诺。
   - 表达类: 表达心理状态或情感态度。
   - 宣告类: 通过话语直接改变现实状态。

输出格式要求：
- 严格按照JSON Schema输出，不要包含任何Markdown标记（如 ```json）。""")
])

chain = prompt_template | llm | parser


# ==========================================
# 3. 主处理函数
# ==========================================
def process_text(text: str) -> dict:
    if not text.strip():
        return {"nodes": [], "edges": [], "言外行为": "未知"}

    # 分词
    tokens = list(jieba.cut(text, cut_all=True))
    clean_tokens = list(set([t.strip() for t in tokens if t.strip()]))

    try:
        result = chain.invoke({
            "text": text,
            "tokens": ", ".join(clean_tokens)
        })
        return result
    except Exception as e:
        print(f"NLP解析失败: {e}")
        return {"nodes": [], "edges": [], "言外行为": "错误"}