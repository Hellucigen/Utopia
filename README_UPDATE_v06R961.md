# Fascinator v0.6R.9.6.1 hotfix

修复前端报错：

```text
selectedEdgeId is not defined
```

原因：v0.6R.9.6 添加边选中功能时，部分前端文件里的全局变量声明没有成功写入，导致按钮/预置节点流程触发 `renderAll()` 时找不到 `selectedEdgeId`。

## 覆盖文件

```text
backend/main.py
backend/data/schema_registry.json
frontend/index.html
README_UPDATE_v06R961.md
```

## 使用

覆盖到：

```text
E:\Utopia
```

重启后端，前端 Ctrl + F5。  
如果浏览器仍报同样错误，按 F12 → Application/应用 → Clear site data，或换 5175 端口重新开前端。
