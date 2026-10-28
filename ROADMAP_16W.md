# 🗺️ 16 周项目驱动执行看板（串行阶段 × 多线并行）

> 说明：把已完成项的 `- [ ]` 改为 `- [x]` 后，运行 `python3 study.py status` 会自动计算各阶段完成率。  
> 节奏基准：每天 5–6 小时 × 每周 6 天（若每天 3 小时，按 1.5 倍拉长周次即可，顺序不变）。

---

## 阶段一：串行打地基（W01–W04）→ 里程碑 M1：从零手搓 GPT

### W01 · 环境点火与神经元直觉
- **算力**：本机 RTX 4080 12GB + 提交远程 A800 申请
- [ ] **[环境]** 运行 `bash env/setup_local_conda.sh` 配好 `ai-lab` 环境，并通过 `python env/check_gpu.py`
- [ ] **[环境]** 提交远程 80GB A800 算力申请，配好免密 SSH 与 WandB 账号
- [ ] **[原理]** 看完 3Blue1Brown《神经网络》第 1–4 集 + PyTorch 60min Blitz
- [ ] **[盲写]** 阅读并独立默写一遍 `concepts/w01_micro_autograd.py`（理解标量链式法则）
- [ ] **[项目 P1]** 用 NumPy 与 PyTorch 分别实现逻辑回归/MLP 跑通 MNIST（准确率 ≥ 97%）
- [ ] **[论文]** 精读方法论 *How to Read a Paper* (Keshav)

### W02 · 自动微分与反向传播破冰
- **算力**：本机 RTX 4080 12GB
- [ ] **[原理]** 跟敲 Karpathy *Zero to Hero*：`micrograd` + `makemore` Part 1–2
- [ ] **[盲写]** 在 `concepts/` 独立手写支持 `tanh/relu/exp` 的微型计算图并做数值梯度检验
- [ ] **[论文]** 略读 *ResNet* (2015) —— 搞懂残差连接 $y = F(x) + x$ 为何是深层网络的梯度高速公路

### W03 · 归一化、训练动态与 Attention 直觉
- **算力**：本机 RTX 4080 12GB | **开启每日 1 题 Hot100**
- [ ] **[原理]** Karpathy `makemore` Part 3（激活/梯度/BatchNorm）+ 3B1B 第 5–7 集（Attention & Transformer）
- [ ] **[盲写]** 在 `concepts/` 盲写 `scaled_dot_product_attention`（含 Causal Mask）并验证输出维度
- [ ] **[论文]** 🔴 精读 *Attention Is All You Need* 第 3 节（建立笔记 `python3 study.py paper attention --deep`）
- [ ] **[刷题]** 完成 `leetcode/` Hot100 数组哈希与双指针前 6 题

### W04 · 里程碑 M1：从零手写 GPT 与 BPE 分词器
- **算力**：本机 RTX 4080 12GB（开启 BF16 秒跑）
- [ ] **[原理]** 跟敲 Karpathy *Let's build GPT* + *Let's build the GPT Tokenizer*
- [ ] **[项目 P1]** 完成 `projects/p1-tiny-llm` 阶段 A：手写 BPE 分词器 + 在中文古诗/小说语料训练 nanoGPT 生成连贯文本
- [ ] **[论文]** 略读 *GPT-2* 与 *GPT-3*（理解 In-Context Learning 涌现）
- [ ] **[刷题]** 完成 Hot100 滑动窗口与链表 6 题

---

## 阶段二：双线并行（W05–W10）→ M2 简历 v1 投日常实习 & M3 Agentic RL

> **并行心法**：🅰 线挂在 GPU 跑训练时，切到 🅱 线用 API + CPU 写 Agent 架构。

### W05 · 现代 LLM 架构（🅰） ∥ 零框架手写 ReAct Agent（🅱）
- **算力**：🅰 本机 4080 跑 MiniMind Pretrain | 🅱 CPU + DeepSeek/Qwen API
- [ ] **[🅰 LLM]** 拆解 `MiniMind` 源码（RoPE / RMSNorm / SwiGLU / GQA），在本机跑通 Pretrain 并记录 WandB 曲线
- [ ] **[🅱 Agent]** 精读 Anthropic *Building Effective Agents* + 跑通并扩展 `projects/p2-scratch-agent/src/react_loop_starter.py`
- [ ] **[论文]** 🔴 精读 *ReAct*；略读 *LLaMA*、*Chain-of-Thought*
- [ ] **[刷题]** 完成 Hot100 栈与二叉树前 6 题

### W06 · SFT & 7B QLoRA（🅰） ∥ 混合检索本地知识库 RAG（🅱）
- **算力**：🅰 本机 4080 跑 MiniMind SFT + Unsloth Qwen2.5-7B 4bit QLoRA（约占 9–10GB 显存）
- [ ] **[🅰 LLM]** 完成 MiniMind SFT；用 Unsloth 在本机微调 `Qwen2.5-7B`（指令→结构化工具/动作 JSON）
- [ ] **[🅱 Agent]** 在 `p2-scratch-agent` 把上层 `../` 仓库做成 **BM25 + 向量检索 + RRF 融合 + Reranker** 问答库
- [ ] **[论文]** 🔴 精读 *LoRA*；略读 *QLoRA*、*RAG (Lewis 2020)*
- [ ] **[刷题]** 完成 Hot100 二叉树进阶与二分查找 6 题

### W07 · RLHF / DPO 偏好对齐（🅰） ∥ MCP 协议与分层记忆（🅱）
- **算力**：🅰 本机 4080 跑 MiniMind DPO / TRL DPO | 🅱 CPU
- [ ] **[原理]** 看李宏毅 RLHF 讲解 + HF Deep RL Course Unit 1（卡公式时 `python3 study.py dict DPO`）
- [ ] **[🅰 LLM]** 完成 `p1-tiny-llm` 收官：跑通 DPO 对齐，汇总 Pretrain→SFT→DPO 实验报告与 README
- [ ] **[🅱 Agent]** 为 `p2-scratch-agent` 手写一个标准 **MCP Server**（暴露本地字典检索与代码沙盒工具）+ 长短期记忆压缩
- [ ] **[论文]** 🔴 精读 *InstructGPT* 与 *DPO*；略读 *Toolformer*
- [ ] **[刷题]** 完成 Hot100 回溯算法 6 题

### W08 · 里程碑 M2：vLLM 部署量化（🅰） ∥ 自纠错 Coding Agent + 简历 v1（🅱）
- **算力**：🅰 A800 部署 vLLM Qwen2.5-7B/14B + 本机测 AWQ 量化 | 🅱 对接自部署 vLLM
- [ ] **[🅰 LLM]** 在 A800 用 `vLLM` 部署 OpenAI 兼容接口服务于自己的 Agent；对比 FP16 与 AWQ 4-bit 吞吐与显存
- [ ] **[🅱 Agent]** 完成 `p2-scratch-agent` 收官：实现「写代码→跑单测→读报错自修」Coding Agent，在 MBPP/HumanEval 子集测出 **Pass@1 / Pass@k** 提升表
- [ ] **[求职 M2]** 填写 `career/resume_bullets_template.md` 前两段项目，产出 **简历 v1**，开始投递**日常实习**！
- [ ] **[论文]** 略读 *Reflexion* 与 *vLLM (PagedAttention)*

### W09 · 强化学习核心与 GRPO 原型验证
- **算力**：本机 4080 或 Colab T4 跑 Unsloth 0.5B/1.5B GRPO
- [ ] **[原理]** 学习策略梯度 → Actor-Critic → PPO → GRPO（配合 `python3 study.py dict GRPO` 对照公式）
- [ ] **[项目 P3]** 在 GSM8K 数学推理子集上跑通 `Qwen2.5-0.5B/1.5B` 的 GRPO 训练，观察思维链长度与奖励爬升曲线
- [ ] **[论文]** 🔴 精读 *DeepSeekMath (GRPO)* 与 *DeepSeek-R1*；略读 *PPO*
- [ ] **[刷题]** 完成 Hot100 动态规划前 6 题

### W10 · 里程碑 M3：双线汇合 —— Agentic RL（自主工具调用强化学习）
- **算力**：远程 A800 80GB（主力训练 `Qwen2.5-3B`）
- [ ] **[项目 P3]** 完成 `projects/p3-agentic-rl`：参考 Search-R1，在 A800 用 veRL/TRL 训练 3B 模型在多跳问答中自主决定何时调用 W06 的本地检索器，产出 **RL vs 纯 Prompting vs SFT** 准确率对比表
- [ ] **[论文]** 🔴 精读 *Search-R1*；略读 *SWE-agent*
- [ ] **[刷题]** 完成 Hot100 动态规划进阶与贪心 6 题

---

## 阶段三：三线并行（W11–W16）→ 里程碑 M4：具身智能 Capstone + 春招冲刺

> **并行心法**：🅰 经典机器人控制（本地仿真） ∥ 🅱 多模态与模仿学习策略（本机 4080） ∥ 🅲 大参数 VLA 微调（A800 后台）。

### W11 · 刚体运动学与 MuJoCo 逆运动学（🅰） ∥ 多模态 VLM 原理与训练（🅱）
- **算力**：本机 RTX 4080 12GB（安装 `robot-lab` 环境）
- [ ] **[🅰 机器人]** 学 HF Robotics Course Unit 2 空间变换；先跑通 `p4-robot-learning/src/ik_2d_toy.py`，再在 **MuJoCo** 中手写雅可比伪逆控制 Franka Panda 机械臂抓取方块
- [ ] **[🅱 多模态]** 看李宏毅多模态课（CLIP/ViT/LLaVA），在本机跑通 `minimind-v` 理解视觉 Projector 对齐机制
- [ ] **[论文]** 略读 *CLIP*、*ViT*、*LLaVA*
- [ ] **[刷题]** 完成 Hot100 图论（BFS/DFS/拓扑排序）6 题

### W12 · 模仿学习双子星：ACT 与 Diffusion Policy（🅱） ∥ VLA 数据管线准备（🅲）
- **算力**：🅱 本机 4080 跑 LeRobot 训练 | 🅲 A800 配置 LIBERO 环境与数据集
- [ ] **[原理]** 读 Lilian Weng *What are Diffusion Models* + HF *Robot Learning: A Tutorial* 模仿学习章节（搞懂多峰动作分布危机与 Action Chunking）
- [ ] **[🅱 策略]** 在 `p4-robot-learning` 基于 HuggingFace **LeRobot** 跑通 PushT（Diffusion Policy）与 ALOHA 仿真（ACT），对比单步 BC 基线成功率
- [ ] **[🅲 VLA]** 在 A800 配通 `LIBERO` 评测基准并下载预训练权重
- [ ] **[论文]** 🔴 精读 *Diffusion Policy*；略读 *ACT (Learning Fine-Grained Bimanual Manipulation)*

### W13 · 视觉-语言-动作大模型（VLA）微调与评测（🅱 + 🅲）
- **算力**：🅱 本机 4080 微调 SmolVLA | 🅲 A800 微调 OpenVLA-OFT 或 openpi ($\pi_0$ LoRA)
- [ ] **[🅱 轻量 VLA]** 在本机用 LeRobot 跑通 `SmolVLA` 推理与小样本微调
- [ ] **[🅲 重型 VLA]** 在 A800 上对 `OpenVLA` 或 $\pi_0$ (`openpi`) 在 LIBERO 任务子集上做 LoRA 微调，记录各任务集成功率
- [ ] **[论文]** 🔴 精读 *OpenVLA* 与 *$\pi_0$*；略读 *RT-2*
- [ ] **[刷题]** 完成 Hot100 堆/TopK 与技巧题 6 题

### W14 · Capstone 上半场：具身大脑（VLM + Agent）接入物理技能库
- **算力**：本机 MuJoCo 仿真 + A800 vLLM/VLM 服务
- [ ] **[项目 P5]** 启动 `projects/p5-embodied-capstone`：复用 P2 的 Agent 架构作为高层任务规划器，将 P4 的抓取/放置/推移策略封装为原语技能接口，实现自然语言长程桌面整理
- [ ] **[论文]** 略读 *SayCan*、*Code as Policies*、*VoxPoser*

### W15 · Capstone 下半场：闭环视觉反思与分层 vs 端到端消融实验
- **算力**：本机 + A800 联合评测
- [ ] **[项目 P5]** 加入执行后视觉状态检查（VLM 判断是否抓空/碰倒 → 触发重规划），在 20+ 条指令上跑完 **消融实验表**（无反思 vs 有反思、IK 技能 vs 学习策略/VLA）
- [ ] **[论文]** 略读 *Hi Robot*（分层具身架构对标）与 *GR00T N1 / $\pi_{0.5}$*

### W16 · 里程碑 M4：作品集封装、八股速刷与 2027 春招全面出击
- [ ] **[作品集]** 为 P1–P5 补齐架构图、实验表格与 30 秒仿真演示 GIF，推送到个人 GitHub 置顶（Pin）仓库
- [ ] **[求职 M4]** 更新 `career/resume_bullets_template.md` 合成最终版 **简历 v2**（LLM 全栈 + Agentic RL + 分层具身 VLA）
- [ ] **[面试冲刺]** 用上层仓库集中突击考前八股：`04/高频面试题.md`、`12` 各章面试考点、`14/教学/05-具身智能面试八股`、`20/教学/06-多模态面试八股`
- [ ] **[模拟面]** 对着简历每个项目自问自答 3 层追问（为什么选这个方案？掉点怎么排查？显存与延迟怎么算？）

