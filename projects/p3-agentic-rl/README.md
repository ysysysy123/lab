# Project 3：Agentic RL —— 从 GRPO 到多轮工具调用

> 2026-11-03 加入主教材：[Datawhale Agentic-RL Lab](https://github.com/datawhalechina/agentic-rl-lab)。
> 启动条件：完成 P1 的小模型训练／验证流程，以及 P2 的工具调用循环、基础 RAG 与固定评估集。作为后续专项展开；看板 W09–W10 保留为任务编号，具体周期按掌握情况安排。任务勾选统一放在 [ROADMAP_16W.md](../../ROADMAP_16W.md)。

## 学习顺序与阶段成果

| 顺序 | 内容 | 阶段成果 |
|---|---|---|
| 1 | 补策略梯度、优势估计、重要性采样，读 [Loss Functions](https://github.com/datawhalechina/agentic-rl-lab/blob/main/experiments/loss-functions/readme.md) | 解释 reward、advantage、采样／当前策略 logprob，以及 IS、PPO、CISPO 的梯度差别 |
| 2 | [GRPO](https://github.com/datawhalechina/agentic-rl-lab/tree/main/experiments/grpo) 的 GSM8K 小实验 | 理解组相对优势，记录奖励、生成长度、成本和独立评估结果 |
| 3 | [Search-R1](https://github.com/datawhalechina/agentic-rl-lab/tree/main/experiments/search-r1) 或 [ReTool](https://github.com/datawhalechina/agentic-rl-lab/tree/main/experiments/retool) 二选一 | 完成采样轨迹 → 执行工具 → 计算奖励 → 更新策略的闭环，与未训练模型比较 |
| 4 | DAPO／GSPO 按需选读 | 围绕基础实验中的一个问题，解释方法改动并决定是否做对照实验 |

检索助手优先选择 Search-R1，代码执行助手选择 ReTool。OPD、OPSD、AgentOPSD、ALFWorld 等留作后续选修。

## 运行方式

- **教材默认路线**：PyTRIO 远程训练，独立 Python ≥3.13 环境；开始实验前确认账号、额度与费用。GRPO 按 [启动指南](https://github.com/datawhalechina/agentic-rl-lab/blob/main/experiments/grpo/start.md) 使用同步入口，指南注明异步示例仍有旧参数需更新。
- **本机／A800 路线**：如需复用现有算力，再选 TRL、Unsloth 或 veRL 适配；模型规模和配置在进入实验时确定。PyTRIO 示例的训练调用需要对应改写。
- GRPO 快速示例目前没有独立评估脚本，需补充未参与训练的题集评估。Search-R1 已有 Base 与训练后模型的 [评估入口](https://github.com/datawhalechina/agentic-rl-lab/blob/main/experiments/search-r1/start.md)。

## 核心实验设计

**Search-R1 路线**：模型提出搜索请求 → 执行检索 → 把结果放回上下文 → 继续生成答案。先跑教材最小实验，再考虑接入 P2 检索代码；使用 HotpotQA 等任务时，知识库需覆盖对应问题的证据文档。

**ReTool 路线**：模型生成代码调用 → 环境执行并返回输出 → 模型继续推理。使用所选任务的答案判定或测试结果计算奖励。

先建立未训练模型的固定评估基线，再做小规模 RL。Base／Prompting 与 RL 使用相同的基础模型、评估数据、工具后端和调用预算；按需加入 SFT 对照。记录任务成功率、工具调用次数、延迟与训练／推理成本，并分析失败轨迹。

| 方法 | 任务成功率／QA EM (%) | 平均工具调用次数 | 平均延迟 (s) | 成本（注明口径） |
|---|---|---|---|---|
| Base／Prompting | 待实验 | 待实验 | 待实验 | 待实验 |
| SFT（选做） | 待实验 | 待实验 | 待实验 | 待实验 |
| GRPO Agentic RL | 待实验 | 待实验 | 待实验 | 待实验 |

最终产出：实验配置与数据说明、结果对比表、成功／失败轨迹，以及解释核心训练过程的项目 README。
