# Mission: 27 届 LLM · Agent 算法实习 10 周通关（2026-11-18 → 2027-01-31）

## Why
从零构建一条贯通「语言模型与 Attention → 从零手搓 GPT & BPE（M1, 12/20）→ 现代 LLM 微调（MiniMind SFT + Qwen QLoRA）→ 零框架 ReAct Agent 与混合检索 RAG（M2 简历 v1, 01/24）」的可复现技术栈与作品集，在 2027 年 1 月底正式启动日常实习投递，并每 3 周用周六半天轻量接触具身智能（MuJoCo / LeRobot）。

## Success looks like
- 对简历上的每一个核心算子（反向传播、SDPA/MHA、BPE、RoPE、RMSNorm、SwiGLU、KV Cache、LoRA/QLoRA、DPO/GRPO、ReAct、BM25+Dense RRF），全部通过 **三级验收（L1 合上资料讲得出 → L2 限时盲写核心代码 → L3 扛住 3 层追问与实验预测题）**。
- 12/20 交付 M1（手写 BPE + GPT），01/24 交付 M2（P1 + P2 完整量化对比表与简历 v1），01/31 启动日常实习投递。
- 自写 200 张以内的精炼复习卡（`学习/cards/`），通过 `python3 study.py review` 间隔复习（1→3→7→14→30→60 天）解决「学过就忘」。

## Constraints
- **时间与节奏**：工作日 3–5 小时（按 4h 标准日排：15min 复习卡 → 2.5h 单一主块 → 20min 写卡与 3 行日志「明天第一件事」→ 30min Hot100），周五集中验收，周日休息。
- **算力分工**：主力本机 RTX 4080 Laptop 12GB（BF16 + SDPA/FA2，Conda Python 3.11 环境）跑日常实验与 QLoRA；Colab T4 16GB 仅用 FP16；远程 A800 80GB 按需用于重型任务。
- **单一进度源**：全局唯一入口为 `PLAN.md`（每天只看当前周的那 1 条未完成任务）；课题分课只认 `学习/<topic>/计划.md`。

## Out of scope (Before Resume v1)
- 2027-01-31 投递前不提前铺开重型 Agentic RL 训练或大规模 VLA 微调（留作 W10 投递后的阶段三分支）；传统搜广推、时间序列、语音、大数据数仓等一律屏蔽。
