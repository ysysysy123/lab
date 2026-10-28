# 📄 27 届实习简历三大核心项目 STAR 模板（边做项目边填数字！）

> **使用方式**：不要等第 16 周再写简历！每跑出一组 Loss、准确率、吞吐量或抓取成功率，立刻把括号里的 `[TODO: 填数字]` 替换掉。  
> **两个投递节点**：
> - **W08（简历 v1 · 投日常实习）**：已完成经历一 + 经历二上半部分，直接开始海投大模型应用/Agent/算法日常实习。
> - **W16（简历 v2 · 冲刺 2027 春招/暑期）**：补齐 Agentic RL 与经历三具身 VLA 闭环，形成极具辨识度的「LLM 底座 + Agent 决策 + 具身物理执行」全栈简历。

---

## 经历一：轻量级大语言模型从零构建、对齐与高并发量化部署（对应 P1）
**技术栈**：PyTorch, Transformers, FlashAttention-2, Unsloth/PEFT (QLoRA), TRL (DPO), vLLM, AWQ

- **架构与预训练**：从零实现 BPE 分词器与现代 Decoder-only 架构（RoPE 旋转位置编码、GQA 分组查询注意力、RMSNorm、SwiGLU），在单张 12GB 显卡（BF16 + FlashAttention-2）完成 `[TODO: 参数量，如 26M/104M]` 模型在 `[TODO: 语料规模]` tokens 上的预训练，Perplexity 从 `[TODO]` 降至 `[TODO]`。
- **领域微调与偏好对齐**：针对工具/机器人结构化指令解析场景构造 `[TODO: N]` 条指令及偏好对数据；先通过 SFT + Loss Masking 建立指令遵循能力，再引入 DPO 直接偏好优化抑制格式幻觉；同步基于 QLoRA 微调 `Qwen2.5-7B`，JSON Schema 严格解析准确率由基线的 `[TODO]%` 提升至 `[TODO]%`。
- **推理加速与量化**：基于 `vLLM`（PagedAttention + Continuous Batching）部署推理服务，对比 FP16 与 AWQ 4-bit 量化方案，显存占用降低 `[TODO]%`，并发吞吐提升 `[TODO]x`，精度损失控制在 `[TODO]%` 以内。

---

## 经历二：自主工具调用智能体系统与 Agentic RL 强化学习训练（对应 P2 + P3）
**技术栈**：ReAct, MCP 协议, Hybrid RAG (BM25 + Dense + RRF + Reranker), GRPO, veRL / TRL

- **零框架智能体与混合检索**：脱离黑盒框架从零构建支持上下文预算压缩、长短期记忆与标准 **MCP 工具协议** 的智能体运行时；针对技术文档与代码库设计保留代码块/公式边界的分块策略，结合 BM25 + 稠密向量检索 + RRF 融合及 BGE-Reranker 重排，Recall@5 较单一向量检索提升 `[TODO]%`。
- **自纠错评估闭环**：构建「规划—编码—沙盒单测—报错归因重试」闭环 Coding Agent，在 HumanEval/MBPP 子集上系统评测多轮反思机制，Pass@1 由 `[TODO]%` 提升至 `[TODO]%`。
- **Agentic RL 训练（W10 亮点）**：参考 Search-R1 范式，在 A800 上采用 **GRPO**（组内相对策略优化）训练 `Qwen2.5-3B` 在多跳问答中自主决策何时发起检索与总结；通过设计格式与结果双重规则奖励，多跳问答 EM 准确率超越纯 Prompting 基线 `[TODO]%`。

---

## 经历三：分层具身智能操作智能体与视觉-语言-动作模型（VLA）微调（对应 P4 + P5）
**技术栈**：MuJoCo, HuggingFace LeRobot, ACT, Diffusion Policy, SmolVLA / OpenVLA / $\pi_0$, VLM

- **运动学控制与模仿学习策略**：在 MuJoCo 仿真环境中基于阻尼最小二乘雅可比伪逆实现 7-DoF Franka Panda 机械臂逆运动学（IK）控制原语；基于 LeRobot 训练 **ACT**（Action Chunking）与 **Diffusion Policy**，解决多模态动作轨迹平均化退化问题，在 PushT / ALOHA 双臂任务上成功率较单步行为克隆（BC）从 `[TODO]%` 提升至 `[TODO]%`。
- **VLA 微调与分层闭环系统**：在 A800 上对 `[OpenVLA / π0]` 在 LIBERO 多任务基准进行 LoRA 微调，平均任务成功率达 `[TODO]%`；进一步搭建「VLM 高层任务拆解与视觉异常检测 + 底层技能/VLA 策略执行」分层具身框架，引入抓空/碰撞后的闭环重规划机制，长程多步操作成功率由开环执行的 `[TODO]%` 提升至 `[TODO]%`。

