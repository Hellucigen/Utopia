# Fascinator v0.6R.1 Memory Gate + Collapsed Graph View

这个更新包继续沿着论文对齐路线做“收敛”，不是继续堆伙伴模块。

## 核心变化

### 1. Working EventFrame，不默认进入长期记忆

旧流程：

```text
输入一句话 → 直接生成 Pending → 审核写入长期图谱
```

新流程：

```text
输入刺激
→ Working EventFrame 预览
→ 觉得重要才 Promote to Pending
→ Pending 审核编辑
→ Confirm Commit 到长期图谱
```

这对应：

```text
Working Graph / Candidate Graph / Long-term Graph
```

它们不是三套认知模块，而是同一种图结构的不同稳定阶段。

### 2. EventFrame 默认折叠显示

主图默认不显示 Slot 节点，也不显示 `hasSlot / mapsTo` 边。

点击 EventFrame 节点后，右侧详情栏显示：

```text
Agent
Action
Patient
Attribute
Derived facts
```

### 3. 新增图谱视图模式

```text
核心图谱
事件折叠视图
自认知视图
Focus 视图
调试全图
```

调试全图才会显示 Slot 节点和完整内部边。

## 覆盖 / 新增文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R1.md
```

## 新增数据文件

首次运行后会自动创建：

```text
backend/data/working_memory.json
```

这个是工作记忆预览，不是长期图谱。

## 使用方式

解压到：

```text
E:\Utopia
```

覆盖同名文件，重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器：

```text
Ctrl + F5
```

## 推荐验收

1. 进入“工作事件框架”
2. 输入：`你的名字是Haru`
3. 点“解析为工作事件框架”
4. 看 Working JSON，但此时还没有进 Pending
5. 点“提升为 Pending”
6. 去 Pending 审核并确认写入
7. 图谱视图选择“事件折叠视图”
8. 点击 EventFrame，看右侧展开 slots
9. 选择“调试全图”，才会看到 Slot 节点
