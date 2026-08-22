# Fascinator v0.6R.9.6.6 stabilization

这版停止扩大功能，只修你指出的两个核心错误。

## 1. 查询激活修复

`你的名字是什么` 现在会：

```text
你/your -> Companion_Self
名字/name -> name_is 边
Companion_Self --name_is--> Name_Haru 同时激活边和两端节点
```

这是一版轻量的“边参与激活”。

如果图谱里存在：

```text
Companion_Self --name_is--> Name_Haru
```

回答会直接用图谱 hint：

```text
我叫 Haru。
```

避免 LLM 又说 `Companion_Self`。

## 2. 中文属性事实修复

`苹果是红色的` 现在确定性解析为：

```text
Apple --color_is--> Color_红色
```

不再生成：

```text
User --believes--> Apple_Color_Is_>_Red
```

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R966.md
```

## 验收

先确保图谱中已经提交：

```text
Companion_Self --name_is--> Name_Haru
```

然后测：

```text
你的名字是什么
```

目标：

```text
我叫 Haru。
```

再强制 Working 测：

```text
苹果是红色的
```

目标：

```text
Apple --color_is--> Color_红色
```
