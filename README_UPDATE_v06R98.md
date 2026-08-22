# Fascinator v0.6R.9.8 Spread Formula + Hyperparameter Self Nodes

这一版修正你问的核心点：自然语言输入不只是“初始激活后直接选动作”，而是：

```text
自然语言输入
→ 语用学五大言外行为分类
→ 激活 Illocution_* 节点
→ jieba/正则分词
→ token 匹配节点与边，匹配度越高激活越高
→ 按 spread_once 公式进行多轮扩散
→ update_attention
→ 从激活后的动作节点中选择行动
```

## 1. 自然语言输入后的扩散

之前 v0.6R.9.7 已经有扩散，但写死为 2 轮。

现在改成超参数：

```json
{
  "naturalInputSpreadSteps": 4
}
```

在 `process_natural_input()` 中：

```text
初始激活完成后
→ for step in range(naturalInputSpreadSteps):
      spread_once()
      update_attention()
```

其中 `spread_once()` 仍然使用当前系统公式：

```text
delta[dst] += source_activation * effective_edge_weight * beta / out_degree(src)
new_activation = old_activation * (1 - lambda) + delta
```

并受这些参数影响：

```text
lambda
beta
maxActivation
relationRuntimeScale
```

## 2. 扩散过程记录

自然语言输入后，runtime 中会记录：

```json
natural_language_pipeline.diffusion_trace
```

返回结果中也有：

```json
runtime.diffusion_trace
runtime.spread_steps
```

方便你看每一轮 top-k 和 focus。

## 3. 新增超参数 self 节点

新增并可同步这些节点：

```text
Hyperparam_Lambda_Decay
Hyperparam_Beta_Spread
Hyperparam_TopK
Hyperparam_ActionThreshold
Hyperparam_MaxActivation
Hyperparam_RelationRuntimeScale
Hyperparam_SelfBaselineActivation
Hyperparam_IllocutionActivation
Hyperparam_TokenActivation
Hyperparam_EdgeTokenActivation
Hyperparam_NaturalInputSpreadSteps
```

这些节点都会带：

```json
{
  "is_self": true,
  "role": "runtime_hyperparameter",
  "param_key": "...",
  "value": ...
}
```

并通过边连接：

```text
Companion_Self --has_hyperparameter--> Hyperparam_*
```

所以它们属于自认知/自调节相关节点，并维持 self 基线激活。

## 4. 新增超参数 GUI

在“激活运行时”页面新增：

```text
超参数调节 GUI
```

可以调：

```text
lambda
beta
topK
actionThreshold
maxActivation
relationRuntimeScale
selfBaselineActivation
illocutionActivation
tokenActivation
edgeTokenActivation
naturalInputSpreadSteps
```

按钮：

```text
保存超参数
创建/同步超参数 self 节点
```

保存后会调用：

```text
POST /runtime/params
```

同步节点调用：

```text
POST /graph/seed-hyperparameters
```

## 5. 新接口

```text
POST /runtime/params
POST /graph/seed-hyperparameters
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
backend/data/core_seed_graph.json
frontend/index.html
README_UPDATE_v06R98.md
```

不包含：

```text
knowledge_graph.json
runtime_state.json
```

不会覆盖长期图谱和当前运行时状态。

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

前端建议换端口：

```powershell
cd E:\Utopia\frontend
py -m http.server 5179 --bind 127.0.0.1
```

打开：

```text
http://127.0.0.1:5179/index.html
```

## 建议操作顺序

```text
1. 备份 knowledge_graph.json 和 runtime_state.json
2. 覆盖本包
3. 重启后端
4. 打开前端 5179
5. 点“写入五大言外行为节点”
6. 到“激活运行时”
7. 点“创建/同步超参数 self 节点”
8. 调 naturalInputSpreadSteps，比如 4 或 6
9. 保存超参数
10. 测自然语言输入
```

## 验收

输入：

```text
你的名字是什么
```

看内部 JSON 中：

```json
"spread_steps": 4,
"diffusion_trace": [...]
```

输入：

```text
苹果是红色的
```

应该自动进入 Working + Pending，并且先经过多轮扩散后选择写入动作。
