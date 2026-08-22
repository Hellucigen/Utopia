# Fascinator v0.6R Paper-Aligned Cognitive Cycle 更新包

这个包把系统从“伙伴聊天模块堆叠”收敛回论文主线：

```text
统一知识图谱
+ 事件框架 EventFrame
+ 激活扩散
+ Top-k 注意候选
+ Focus 子图
+ Action 节点
+ 结果回写
```

## 覆盖 / 新增文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
CLEANUP_OBSOLETE_FILES.ps1
README_UPDATE_v06R.md
```

不会覆盖：

```text
backend/data/knowledge_graph.json
backend/data/pending_writes.json
backend/data/runtime_state.json
backend/data/llm_runs.json
backend/data/snapshots/
```

## 可删除的旧文件

这些是之前“模块化伙伴层”的残留，不再作为主线使用，可以删除：

```text
backend/data/companion_profile.json
backend/data/self_state.json
backend/data/self_graph_seed.json
backend/data/interaction_history.json
backend/data/feedback_log.json
README_UPDATE_v06.md
README_UPDATE_v061.md
README_UPDATE_v062.md
backend/__pycache__/
```

可以手动删除，也可以在 `E:\Utopia` 运行：

```powershell
.\CLEANUP_OBSOLETE_FILES.ps1
```

## 新主线

### 1. Stimulus / EventFrame

输入不是“聊天消息”，而是 stimulus：

```text
你的名字是Haru
```

系统生成 Pending：

```text
EventFrame
Slot_Agent -> User
Slot_Action -> Assign_Name
Slot_Patient -> Companion_Self
Slot_Attribute -> Name_Haru
Companion_Self --hasAttribute--> Name_Haru
```

注意：仍然必须 Pending 审核后才写入长期图谱。

### 2. 自认知不是 profile JSON

自认知来自正式图谱：

```text
memory=self 或 type=Self 的节点及其邻接子图
```

Haru 不来自 profile 文件，而来自你教给系统、审核后写入的图谱结构。

### 3. “伙伴”不是模块

伙伴能力的培养路线是：

```text
你慢慢教知识
→ 知识和事件框架进入统一图谱
→ 激活扩散形成注意焦点
→ Action 节点逐渐触发
→ 结果回写形成经验
→ 交互能力从图谱结构和运行时循环中涌现
```

## 使用

解压到：

```text
E:\Utopia
```

覆盖同名文件后重启：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```text
Ctrl + F5
```

## 推荐验收

1. 打开“刺激 / 事件框架”
2. 输入：`你的名字是Haru`
3. 点“构建事件框架 Pending”
4. 在 Pending 审核 JSON
5. 确认写入
6. 打开“自认知子图”，确认出现 `Companion_Self`、`Name_Haru`
7. Runtime 输入 `Companion_Self`，注入，单步 Tick
8. 创建快照：`v0.6R_event_frame_self_memory_success`
