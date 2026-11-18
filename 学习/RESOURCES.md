# AI Lab 核心学习资源策展（Resources）

> 细粒度章节与公式定位请直接运行 `python3 study.py dict <关键词>` 或查阅 [REFERENCE_INDEX.md](../REFERENCE_INDEX.md)；本文件仅记录高可信一手主线资料及其调用时机。

## Knowledge（一手课程、教材与基准源码）

- **上层 AI Tutorial 原始课程库（`../00, 03, 04, 07, 08, 12, 14, 15, 20`）**
  本地零延迟中文推导与 NumPy 从零实现库。适用时机：每开一个新课题时，先用 `study.py learn nb` 提取符号体系、公式推导步骤与梯度检验基线。
- **Lab 本仓实战代码（`concepts/*.py` 与 `projects/p1..p5/src/*.py`）**
  个人亲手验证与简历项目源码。适用时机：代码讲解（`.code-walk`）第一优先来源，确保课程讲解与自己仓库里的变量名、行号完全一致。
- **Andrej Karpathy — _Neural Networks: Zero to Hero_ & `nanoGPT` / `minbpe`**
  从 `micrograd` 标量计算图一路手搓到 GPT-2 与 BPE 分词器的最高信噪比英文实战课。适用时机：W01–W04 打通自动微分、训练动态（BatchNorm/激活饱和）与因果自注意力直觉。
- **3Blue1Brown —《深度学习 / 神经网络与 Transformer》可视化系列**
  最佳几何与空间直觉建立材料。适用时机：进入新架构（MLP、反向传播、Attention Value/Key/Query 空间投影）前建立第一眼画面感。
- **MiniMind & Unsloth / HuggingFace TRL 官方文档与源码**
  现代 Decoder-only LLM（RoPE + GQA + RMSNorm + SwiGLU）最小全流程实现与单卡高效微调标准栈。适用时机：W05–W10 拆解现代架构、SFT Loss Mask、QLoRA、DPO 与 GRPO。
- **Anthropic — _Building Effective Agents_ & Model Context Protocol (MCP) 规范**
  工业界最克制的零臃肿 Agent 设计准则。适用时机：W05–W08 构建 `p2-scratch-agent` 的 ReAct 循环、上下文压缩与标准 MCP 工具服务。
- **[Datawhale — Agentic-RL Lab](https://github.com/datawhalechina/agentic-rl-lab)**（2026-11-03 加入）
  P3 Agentic RL 主教材与实验参考，在 P1 小模型训练和 P2 基础 Agent／评估完成后使用。学习顺序：Loss Functions → GRPO → Search-R1（检索）或 ReTool（代码执行）二选一；DAPO／GSPO 后续选读，其余专题按需展开。当前示例要求 Python ≥3.13，主要通过 PyTRIO 远程训练，实验前确认账号、额度与费用；使用独立环境。本机／A800 的 TRL 或 Unsloth 实现另行选配。任务与进度统一记录在 [ROADMAP_16W.md](../ROADMAP_16W.md)，细节见 [P3 项目计划](../projects/p3-agentic-rl/README.md)。
- **HuggingFace _Robot Learning: A Tutorial_ & `LeRobot` 源码**
  涵盖刚体空间变换、ACT、Diffusion Policy 与 SmolVLA/OpenVLA/$\pi_0$ 的统一开源具身栈。适用时机：W11–W16 具身控制与模仿学习/VLA 实验。

## Wisdom（真实反馈与开源社区）

- **GitHub Issues / Discussions（`karpathy/nanoGPT`、`jingyaogong/minimind`、`huggingface/lerobot`、`volcengine/verl`）**
  适用时机：排查真实训练 Loss 不降、显存溢出、GRPO 奖励坍缩或 MuJoCo 仿真奇异点等课本不写的工程经验。
- **真实面试反馈闭环（本仓 `career/interview_log.md`）**
  适用时机：W08 启动日常实习投递后，将真实面试官的追问反哺回对应课题的速查表与学习记录。

## Gaps（待后续按需补齐）

- P3 Agentic RL 已接入主教材；独立 GRPO 评估与本机／A800 训练适配，待进入该专项时按所选路线补充。
- W13 $\pi_0$ 流匹配微调的本地轻量化冒烟脚本，待推进到具身专项时补充。
