# Fascinator v0.6R.9.3 Unified Natural-Language Input

这一版按你的意思改：

```text
意图路由不再作为用户可见页面
询问回答输出也不再单独作为页面
自然语言输入成为默认入口
```

## 新默认流程

用户只在“自然语言输入”页面输入一句话：

```text
Haru现在知道自己叫什么吗？
我最近在学强化学习
把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
```

后端自动：

```text
自然语言输入
→ 内部意图路由
→ 选择 Intent / Action / ResponseMode
→ 根据 Action 执行：
   1. 回答
   2. 生成 Working 记忆
   3. 图谱治理预览/执行
   4. Debug context
   5. 忽略低价值输入
```

## 前端变化

删除/隐藏这些用户可见页面：

```text
意图路由
询问回答输出
```

改良：

```text
工作事件框架
```

为：

```text
自然语言输入
```

里面有：

```text
自然语言输入框
处理输入
强制解析为 Working 记忆
内部处理结果 JSON
Working Memory 列表
```

## 新接口

```text
POST /natural/process
```

请求：

```json
{
  "text": "Haru现在知道自己叫什么吗？",
  "model": "qwen2.5",
  "timeout_seconds": 90,
  "execute_governance": false
}
```

返回根据输入类型不同：

```text
kind=answer
kind=working_memory
kind=governance_preview
kind=governance_executed
kind=ignored
kind=debug_context
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R93.md
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

前端重新启动/刷新：

```powershell
cd E:\Utopia\frontend
python -m http.server 5174 --bind 127.0.0.1
```

浏览器打开：

```text
http://127.0.0.1:5174
```

## 推荐测试

在“自然语言输入”里测：

```text
Haru现在知道自己叫什么吗？
```

应该直接输出类似：

```text
我叫 Haru。
```

再测：

```text
我最近在学强化学习
```

应该生成 Working 记忆。

再测：

```text
把 Topic_意大利黑帮 合并到 Topic_意大利黑手党
```

如果 `execute_governance=false`，应该只给治理预览，不直接执行。
