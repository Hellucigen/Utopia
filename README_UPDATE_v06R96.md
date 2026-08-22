# Fascinator v0.6R.9.6 Self-name canonicalization + Edge selection + Auto layout save

这一版修三个问题。

## 1. 修复“你的名字是Haru”生成 User --name_is--> Name_Haru

你给出的结果里同时出现：

```text
User --name_is--> Name_Haru
Companion_Self --name_is--> Name_Haru
```

这是 LLM 把“你的名字是Haru”误读成“用户的名字是Haru”。  
规则解析已经正确识别出了：

```text
Companion_Self --name_is--> Name_Haru
```

所以本版在 canonicalizer 里加入：

```text
如果 rule_repair 识别为 self_name，
则丢弃 LLM 产生的其它 src --name_is--> 同一 Name_* 的事实。
```

现在输入：

```text
你的名字是Haru
```

应该只保留：

```text
Companion_Self --name_is--> Name_Haru
```

不应再出现：

```text
User --name_is--> Name_Haru
```

## 2. 图谱上可以直接选中边

现在主图上的边可以点击。

点击边后会自动填入：

```text
Source
Target
Relation
Weight
Edge Attributes JSON
```

并高亮该边。

新增按钮：

```text
删除选中边
```

## 3. 图谱布局自动保存

拖动节点后，前端会把布局保存到浏览器 localStorage：

```text
fascinator_graph_layout_v1
```

刷新页面后布局仍然保留。

新增按钮：

```text
清空布局
```

`重置视图` 现在只重置缩放/平移，不再清空节点位置。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R96.md
```

## 使用

覆盖到：

```text
E:\Utopia
```

重启后端：

```powershell
cd E:\Utopia
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端 Ctrl + F5。

## 验收

### 自我名字写入

输入：

```text
你的名字是Haru
```

Working JSON 里应只有：

```text
Companion_Self --name_is--> Name_Haru
```

### 边选择

在主图点任意边，右侧/左侧图谱编辑区应自动填入边信息。

### 布局保存

拖动几个节点，刷新页面，布局应保持。
