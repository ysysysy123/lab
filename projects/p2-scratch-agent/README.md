# 🛠️ Project 2: 零框架手写智能体运行时 + 混合检索 RAG + 自纠错 Coding Agent（W05–W08）

> **简历定位**：面试官最反感「调了三行 LangChain API」。本项目**纯 Python 从零手写** ReAct 调度台、标准 MCP Server、把上层 `autumn-recruitment` 全库做成混合检索知识库，并在代码评测集上跑出真实的 **Pass@1 提升数据**。  
> **算力需求**：纯 CPU + API（DeepSeek / Qwen API 或你在 A800 自建的 vLLM 接口），可与 P1 训练完全并行推进！

---

## 四周渐进里程碑

1. **W05 · 极简 ReAct 与工具安全护栏**：阅读并扩展 `src/react_loop_starter.py`，接入真实 OpenAI 兼容接口（Function Calling），加上最大步数熔断与参数 JSON 校验。
2. **W06 · 混合检索 RAG（数据源直接用 `../../../` 上层仓库！）**：
   - 解析上层仓库 `.md` 与 `.ipynb`，保留代码块和 `$$...$$` 公式不切断；
   - 实现 `BM25` + 稠密向量检索 + **RRF（倒数秩融合）** + `BGE-Reranker`，对比单一向量检索的 Recall@5。
3. **W07 · MCP 标准协议与上下文压缩**：用官方 `mcp` Python SDK 把 W06 的混合检索器与本地 Python 沙盒封装成标准 MCP Server；为 Agent 增加滑动窗口摘要压缩。
4. **W08 · 自纠错 Coding Agent 与科学评估**：实现 `Planner → Coder → Pytest 沙盒执行 → 捕获 Traceback 重试` 循环，在 MBPP / HumanEval 50 题子集上测出 **单次生成 vs 最多 3 轮自修** 的无偏 Pass@1 对比表。

## 📊 待填实验结果表

| 模块 / 实验设置 | 核心指标 | 基线结果 | 改进后结果 | 相对提升 |
|---|---|---|---|---|
| 本地仓库 RAG：纯向量检索 vs BM25+Dense+RRF+Rerank | Recall@5 | | | |
| Coding Agent：Zero-shot 单次生成 vs 3轮沙盒报错自修 | MBPP Pass@1 | | | |

