# 🎯 Project 3: Agentic RL —— 用 GRPO 训练大模型自主调用检索工具（W09–W10）

> **简历杀手锏**：27 届实习竞争中，做过普通 RAG/Agent 的人很多，但**亲手用强化学习（GRPO）训练模型自己学会多轮工具调用（Search-R1 范式）**的候选人凤毛麟角！  
> **算力分工**：
> - **W09（本机 RTX 4080 12GB 或 Colab T4）**：用 Unsloth 跑通 `Qwen2.5-0.5B/1.5B` 在 GSM8K 上的单轮 GRPO，摸透格式奖励 + 答案准确性奖励曲线。
> - **W10（远程 A800 80GB）**：基于 `veRL` 或 `TRL` + 本地混合检索服务（复用 P2 的检索器！），在多跳问答数据集（如 HotpotQA 子集）上训练 `Qwen2.5-3B` 输出 `<think>...</think><search>查询词</search><information>...</information><answer>...</answer>` 轨迹。

---

## 核心实验设计

1. **交互轨迹协议**：
   - 模型生成 `<search>...</search>` 时停止解码 → 环境调用 P2 的 BM25+向量检索器把 Top-3 段落塞进 `<information>...</information>` → 继续生成直至 `<answer>...</answer>`（最多 3 轮检索）。
2. **规则奖励函数（Rule-based Reward，无需训练 Reward Model！）**：
   - $R_{\text{format}} \in \{0, 0.2\}$：标签闭合且合法；
   - $R_{\text{answer}} \in \{0, 1.0\}$：最终 `<answer>` 与标准答案 Exact Match / F1。
3. **三组硬核对比实验（必填进简历）**：

| 方法 (`Qwen2.5-3B`) | 单跳 QA EM (%) | 多跳 QA (HotpotQA 子集) EM (%) | 平均检索调用次数 |
|---|---|---|---|
| 纯推理不检索 (Direct CoT) | | | 0 |
| 固定单次检索 (Naive RAG) | | | 1.0 |
| ReAct Prompting (未做 RL 训练) | | | |
| **GRPO Agentic RL (本项目)** | | | |

