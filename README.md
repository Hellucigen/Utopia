
# Unified Knowledge Graph Prototype

这是按你的论文逻辑重写的清洁版工程，去掉了自认知子图、记忆回忆、图谱治理等冲突模块，只保留：

- 节点 / 边的统一知识图谱存储
- JSON 持久化
- 交互式图谱创建器
- 自然语言感知器
- 主扩散逻辑
- Top-k 输出
- 程序性节点执行与结果写回

## 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

## 打开前端

直接用浏览器打开 `frontend/index.html`，或使用任意静态服务器。

## 说明

- 节点 label 只使用：`declarative-semantic`、`declarative-episodic`、`procedural`
- 节点的 `execution` 字段用于程序性记忆节点
- 自然语言输入会先做规则抽取，再做扩散
- 如果你后续要接 LLM，把 `parse_natural_language()` 换成外部模型解析即可
