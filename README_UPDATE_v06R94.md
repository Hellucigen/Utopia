# Fascinator v0.6R.9.4 Assertion Routing Fix

修复你截图里的问题：

```text
你的名字是Haru
```

这句话是“教学/断言/写入记忆”，不是询问。  
上一版被 LLM 意图路由误判成回答，所以输出了“我还没……”之类的回答。

## 修复方式

在 LLM 意图路由前增加 deterministic assertion override：

```text
你的名字是Haru
你叫Haru
我是Hellucigen
我叫Hellucigen
你是我的AGI研究伙伴
我对X感兴趣
我最近在学X
A is B
A has B
```

这些会优先走：

```text
Intent_Assertion / Intent_Knowledge_Teaching / Intent_Preference
→ Action_Write_Working_Memory
→ 生成 Working 记忆
```

不会走回答节点。

## 预期结果

输入：

```text
你的名字是Haru
```

应该输出：

```text
已生成 Working 记忆
```

然后 Working JSON 中应包含类似：

```text
Companion_Self --name_is--> Name_Haru
```

你再手动提升到 Pending，审核后 Commit。

而输入：

```text
Haru现在知道自己叫什么吗？
```

才应该走回答：

```text
我叫 Haru。
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R94.md
```
