# 📚 30 篇精选论文追踪单（区分 🔴精读 与 🟢略读）

> **无痛读论文法则**：
> - **🔴 精读（仅 11 篇，约 2h/篇）**：先看摘要与架构图 → 手推核心公式 → 去开源仓库找对应 20 行代码实现 → 运行 `python3 study.py paper <简称> --deep` 填半页卡片。
> - **🟢 略读（19 篇，30m/篇）**：只读 Abstract + Figure 1 + 实验主表结论 → 运行 `python3 study.py paper <简称> --skim` 填 3 句话即可打勾！

---

## 阶段一：神经网络与 Transformer 地基（W01–W04）
- [ ] 🟢 **How to Read a Paper** (Keshav, 2007) — 三遍阅读法，第 1 周先读它
- [ ] 🟢 **ResNet** (*Deep Residual Learning*, 2015) — 残差连接为何能防退化
- [ ] 🔴 **Attention Is All You Need** (Vaswani et al., 2017) — 精读第 3 节，$QK^T/\sqrt{d_k}$ 与多头
- [ ] 🟢 **GPT-2** (*Language Models are Unsupervised Multitask Learners*, 2019) — Zero-shot 生成范式
- [ ] 🟢 **GPT-3** (*Language Models are Few-Shot Learners*, 2020) — In-Context Learning 涌现

## 阶段二 A：LLM 微调、对齐与推理模型（W05–W10）
- [ ] 🟢 **LLaMA** (Touvron et al., 2023) — 现代开源 LLM 标准配方（RMSNorm + SwiGLU + RoPE）
- [ ] 🔴 **LoRA** (Hu et al., 2021) — 低秩矩阵参数高效微调与初始化细节
- [ ] 🟢 **QLoRA** (Dettmers et al., 2023) — NF4 量化 + 双重量化省显存原理
- [ ] 🔴 **InstructGPT** (Ouyang et al., 2022) — SFT → RM → PPO 经典三步对齐流水线
- [ ] 🟢 **PPO** (Schulman et al., 2017) — Clipped Surrogate Objective 裁剪目标
- [ ] 🔴 **DPO** (*Direct Preference Optimization*, 2023) — 绕开显式奖励模型的闭式解推导
- [ ] 🟢 **vLLM / PagedAttention** (Kwon et al., 2023) — 操作系统分页思想解决 KV Cache 碎片
- [ ] 🔴 **DeepSeekMath** (Shao et al., 2024) — **GRPO** 组内相对优势替代 Critic 模型
- [ ] 🔴 **DeepSeek-R1** (2025) — 冷启动 + 规则奖励 RL 激发自我反思推理

## 阶段二 B：Agent 智能体与 Agentic RL（W05–W10）
- [ ] 🟢 **Chain-of-Thought** (Wei et al., 2022) — 思维链提示激发多步推理
- [ ] 🔴 **ReAct** (Yao et al., 2022) — Thought-Action-Observation 闭环抑制幻觉
- [ ] 🟢 **RAG** (Lewis et al., 2020) — 检索增强生成的经典架构范式
- [ ] 🟢 **Toolformer** (Schick et al., 2023) — 模型自监督学习何时调用外部工具
- [ ] 🟢 **Reflexion** (Shinn et al., 2023) — 语言反馈存入记忆实现无需改权重的试错进化
- [ ] 🟢 **SWE-agent** (Yang et al., 2024) — Agent-Computer Interface (ACI) 设计哲学
- [ ] 🔴 **Search-R1** (2025) — 用 GRPO/PPO 训练大模型在多轮推理中自主发起检索（对应项目 P3）

## 阶段三：多模态感知、模仿学习与具身 VLA（W11–W16）
- [ ] 🟢 **CLIP** (Radford et al., 2021) — InfoNCE 图文对比学习对齐底座
- [ ] 🟢 **LLaVA** (Liu et al., 2023) — 视觉编码器 + MLP Projector + LLM 极简配方
- [ ] 🟢 **ACT / Mobile ALOHA** (Zhao et al., 2023) — CVAE + Action Chunking 抑制模仿学习复合误差
- [ ] 🔴 **Diffusion Policy** (Chi et al., 2023) — 连续动作空间去噪生成，优雅破解多模态动作分布危机
- [ ] 🟢 **RT-2** (Brohan et al., 2023) — 互联网图文知识向离散机器人动作 Token 迁移（VLA 开山作）
- [ ] 🔴 **OpenVLA** (Kim et al., 2024) — 开源 7B VLA 架构（DINOv2+SigLIP + Llama2 + 256 bin 动作离散化）
- [ ] 🔴 **$\pi_0$: A Vision-Language-Action Flow Model** (Black et al., 2024) — 预训练 VLM + Flow Matching 连续高频动作专家
- [ ] 🟢 **SayCan** & **Code as Policies** (2022) — 大模型高层语义规划与底层物理可执行性解耦
- [ ] 🟢 **VoxPoser** (2023) / **Hi Robot** (2025) — 3D 价值场与「高层推理 + 底层高频执行」分层具身范式（对应项目 P5）

