# Fascinator v0.6R.6 Recall + Activation Hygiene

这一版不是做聊天，而是做“能稳定回忆事实”。

## 修复 / 新增

### 1. Activation Hygiene

- 激活值强制 clamp 到 `[0, maxActivation]`
- Top-k 不再显示 `activation <= 0` 的节点
- 清理旧的未知节点激活
- edge runtime 也不再出现负值

### 2. Top-k filter

激活运行时新增：

```text
Top-k filter:
all
declarative
semantic
episodic
procedural
```

自认知回忆时建议用：

```text
semantic
```

或：

```text
declarative
```

这样 procedural handler 不会把语义事实挤掉。

### 3. Recall API

新增：

```text
GET /recall/{node_id}?depth=1
GET /focus/explain
GET /recall/presets
```

例如：

```text
/recall/Companion_Self
```

返回：

```text
Companion_Self --name_is--> Name_Haru
Companion_Self --relationship_is--> Relationship_...
```

### 4. 前端新增“记忆回忆”页面

可以输入节点 ID：

```text
Companion_Self
User
Robot
```

点击“查询回忆”，会显示：

```text
结构化事实列表
小图谱
Focus 解释
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R6.md
```

## 使用

解压覆盖到：

```text
E:\Utopia
```

重启：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端 Ctrl + F5。

## 推荐测试

1. 清空激活
2. Seed IDs: `Companion_Self`
3. 注入
4. Tick 3 次
5. Top-k filter 选 `semantic`
6. 打开“记忆回忆”
7. 查询 `Companion_Self`

理想看到：

```text
Companion_Self --name_is--> Name_Haru
Companion_Self --relationship_is--> Relationship_AGI研究伙伴
```
