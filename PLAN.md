# 🎯 PLAN.md — 10 周到日常实习简历 v1（唯一进度入口）

> **唯一入口原则**：日常学习只看本文件「当前聚焦周」的**今天那一条任务**。  
> **时间锚点**：2026-11-18 → 2027-01-31（工作日 3–5h，按 4h 标准日排，周日休息；M1 手写 GPT = `12/20`，M2 简历 v1 = `01/24`，开始投递 = `01/31`）。  
> **方向权重**：LLM + Agent 主线（85%）+ 每 3 周周六半天具身智能轻体验（15%）。  
> *历史 16 周完整路线已归档至 [archive/ROADMAP_16W.md](archive/ROADMAP_16W.md)。*

---

## ⏱️ 每日 ADHD 极简三件套（打开 `python3 workbench.py` 一眼看到）

1. **① 唤醒翻卡（10–15 min）**：在工作台首页直接翻今日到期复习卡（点「记住了 / 没记住」，自动按 1→3→7→14→30→60 天排期）。
2. **② 唯一主块（2–2.5 h）**：只推进下方当前周的 **1 条主线任务**（直觉 → 写核心代码 → 跑通验证，全天不换频道）。
3. **③ 每日力扣 1 题 + 1 句收尾（30 min，从今天直接开始！）**：在工作台点「一键生成刷题脚本」写 1 道 Hot100（20 分钟无思路直接看题解重写），收尾写下 **「明天第一件事」**（每次勾选/保存均自动同步至远程 GitHub）。

---

## 阶段零：系统切换与地基收尾（W00）

### W00 · 切换周与自动微分收尾（11/18–11/22）

- **本周唯一目标**：跑通 W02 盲写挑战，完成 W01 复习卡与 L1 验收，切入 v2 极简每日闭环。
- **已通关地基（原 W01 + ResNet 成果保留）**：
  - [x] **[环境]** 配好本机 Conda `test` 环境（RTX 4080 BF16）与远程 A800 / WandB
  - [x] **[原理]** 3Blue1Brown《神经网络》1–4 集 + PyTorch 60min Blitz + `w01-自动微分与P1` 5 节交互课
  - [x] **[盲写]** 独立默写通关 `concepts/w01_my_autograd.py`（标量链式法则 + ReLU/Exp + 逆拓扑序）
  - [x] **[项目 P1]** NumPy MLP（97.73%）与 PyTorch MLP（97.71%）跑通 MNIST 严格对齐
  - [x] **[论文]** 精读 *How to Read a Paper* (Keshav) + 略读 *ResNet* (`papers/resnet.md`)
- **本周待办（每天 1 条主块 + 每日 1 道力扣 Hot100）**：
  - [ ] **[Day 1 · L2 盲写]** 补完 `concepts/w02_micrograd.py` 的 3 处 `TODO(human)`（`tanh`、`__pow__`、`numerical_grad`）并跑通全部 `assert` + 力扣打卡 `LC 1. 两数之和`
  - [ ] **[Day 2 · 复习卡与检验]** 在工作台刷完 W01 的 10 张核心复习卡（不顺口的改成自己的话）+ 力扣打卡 `LC 49. 字母异位词分组`
  - [ ] **[Day 3 · L1/L3 验收]** 向 AI 口述通关 W01 三大核心问题（`backward` 三条铁律、`p - y` 梯度化简、`dW2 = A1.T @ dZ2` 维度推导）+ 力扣打卡 `LC 128. 最长连续序列`

---

## 阶段一：语言模型 → Attention → 手搓 GPT（W01–W04 → 里程碑 M1）

### W01 · 语言模型破冰：从 Bigram 到字符级 MLP LM（11/23–11/29）

- **核心产出**：`concepts/w01_char_mlp_lm.py`（汇报 train/val loss + 采样 10 条生成结果）
- **每日推进单**：
  - [ ] **[周一 · Bigram]** 跟敲 Karpathy *makemore* Part 1 前半：二元字符统计计数表与概率归一化
  - [ ] **[周二 · NLL Loss]** 完成 *makemore* Part 1 后半：负对数似然（NLL）与交叉熵等价性验证，盲写 bigram NLL 计算
  - [ ] **[周三 · Embedding]** 跟敲 *makemore* Part 2 前半：理解 Embedding 查表为何等价于 One-Hot 矩阵乘法，搭建 `C[X]` 输入层
  - [ ] **[周四 · MLP LM]** 完成 `concepts/w01_char_mlp_lm.py`：划分 train/val/test，训练字符级 MLP 语言模型并采样生成
  - [ ] **[周五 · 周验收]** 通过 W01 三级验收卡（L1 口述 + L2 盲写 NLL + L3 预测 Embedding 维数对 val loss 的影响）
- **✂️ 落后可砍项**：*makemore* Part 3（BatchNorm 细节）不放本周。

### W02 · Attention 核心算子：SDPA、因果掩码与 MHA（11/30–12/06）

- **核心产出**：`concepts/w02_attention.py`（手写 SDPA + Causal Mask + MHA，与 `F.scaled_dot_product_attention` 误差 `< 1e-6`）
- **每日推进单**：
  - [ ] **[周一 · SDPA 直觉与推导]** 看 3B1B 第 5–6 集 + `学习/w03` 第 1 课，手算 $T=3, d_k=2$ 注意力输出并理解 $\sqrt{d_k}$ 方差缩放
  - [ ] **[周二 · Causal Mask 与 MHA]** 学 `学习/w03` 第 2 课，掌握上三角 $-\infty$ 掩码位置与 `(B,T,C) -> (B,H,T,d_k)` 分头重排
  - [ ] **[周三 · 代码对齐]** 编写 `concepts/w02_attention.py` 并与 PyTorch 官方 `scaled_dot_product_attention` 数值严格对齐
  - [ ] **[周四 · 论文精读]** 🔴 精读 *Attention Is All You Need* 第 3 节（`papers/attention.md`）+ 本周 4 道 Hot100（哈希/双指针）
  - [ ] **[周五 · 周验收]** 20 分钟限时盲写 MHA forward（L2）+ 预测题：去掉 $\sqrt{d_k}$ 且 $d_k=512$ 时 Softmax 熵与梯度变化（L3）
- **✂️ 落后可砍项**：Dropout 与 KV 异源 Cross-Attention 留到后续按需看。

### W03 · 从零搭建 Decoder-Only GPT（12/07–12/13）

- **核心产出**：`projects/p1-tiny-llm/src/gpt.py` 在中文古诗/小说小语料（字符级）跑通 RTX 4080 BF16 训练并生成连贯文本
- **每日推进单**：
  - [ ] **[周一 · 残差与 Norm]** 学 `学习/w03` 第 4 课（Pre-Norm vs Post-Norm + 残差梯度高速公路），搭好 `TransformerBlock`
  - [ ] **[周二 · GPT 组装]** 结合 Karpathy *Let's build GPT* 组装完整 `GPT`（Token/Pos Embedding + Blocks + LM Head + `generate`）
  - [ ] **[周三 · 4080 训练实跑]** 在中文古诗/小说语料上开启 BF16 训练，记录 train/val loss 曲线与生成样例
  - [ ] **[周四 · 参数量账本 + 刷题]** 手算模型各层参数量并与 `sum(p.numel())` 核对 + 本周 4 道 Hot100（双指针/滑动窗口）
  - [ ] **[周五 · 周验收]** 盲写 `TransformerBlock`（L2）+ 追问 Pre-Norm 优势 + **周六半天具身轻体验 #1**：跑通 `projects/p4-robot-learning/src/ik_2d_toy.py`
- **✂️ 落后可砍项**：中文语料清洗繁琐时直接先用现成古诗集或 tiny-shakespeare。

### W04 · BPE 分词器与里程碑 M1 收官（12/14–12/20）

- **核心产出（🎯 里程碑 M1）**：手写 BPE 分词器 + `projects/p1-tiny-llm/README.md` Stage A 量化对比表（字符级 vs BPE）
- **每日推进单**：
  - [ ] **[周一 · BPE 核心循环]** 结合 *Let's build the GPT Tokenizer* 扩展 `projects/p1-tiny-llm/src/bpe_starter.py`（字节对统计与 merge）
  - [ ] **[周二 · 词表训练与编解码]** 在中文语料上训练 BPE 词表，验证 `decode(encode(text)) == text` 零损还原与压缩率
  - [ ] **[周三 · BPE-GPT 对照实验]** 将 W03 的 GPT 切换为 BPE Tokenizer 重训，记录压缩率、吞吐 `tok/s` 与生成质量对比表
  - [ ] **[周四 · 论文略读 + 刷题]** 🟢 略读 *GPT-2*（`papers/gpt2.md`）+ 本周 4 道 Hot100（链表）
  - [ ] **[周五 · M1 里程碑模拟面]** 60 分钟 Stage A 综合验收：白板画 GPT 全流程 Shape + 盲写 Attention + 讲清 BPE Merge + 3 层追问
- **✂️ 落后可砍项**：对比表优先保证压缩率与 val loss，正则预分词细节从简。

---

## 阶段二：现代 LLM 全栈 ∥ 零框架 Agent & RAG（W05–W09 → 里程碑 M2 简历 v1）

### W05 · 现代 LLM 四大标准积木（12/21–12/27 · 圣诞周 70% 容量）

- **核心产出**：为自写 GPT 升级 `RoPE + RMSNorm + SwiGLU + GQA/KV Cache`，产出一张消融与推理测速表
- **每日推进单**：
  - [ ] **[周一 · RoPE 旋转位置编码]** 学 `学习/w03` 第 3 课，推导 2D 旋转相对位置内积不变性，手写 `apply_rope`
  - [ ] **[周二 · RMSNorm 与 SwiGLU]** 学 `学习/w03` 第 5 课前半，手写 `RMSNorm` 与 $\frac{8}{3}d$ `SwiGLU` 并替换进自写 GPT
  - [ ] **[周三 · GQA 与 KV Cache]** 学第 5 课后半，实现推理 `KV Cache`，测试开启前后生成 256 tokens 的延迟对比
  - [ ] **[周四 · 论文略读 + 刷题]** 🟢 略读 *LLaMA*（`papers/llama.md`）+ 本周 3 道 Hot100（栈与队列，含 **LC 146 LRU 缓存**）
  - [ ] **[周五 · 周验收]** 盲写 `RMSNorm` + `apply_rope`（L2）+ 口算 7B 模型 MHA vs GQA (group=8) 的 KV Cache 显存账（L3）
- **✂️ 落后可砍项**：KV Cache 测速脚本可简化为单 batch 计时。

### W06 · MiniMind 预训练 / SFT 与手写 LoRA（12/28–01/03 · 元旦周 70% 容量）

- **核心产出**：MiniMind Pretrain → SFT 训练曲线与前后回答对比 + 手写 `LoRALinear` 单测
- **每日推进单**：
  - [ ] **[周一 · MiniMind 跑通]** 对照源码拆解 MiniMind，先 `max_steps=5` 冒烟，再在本机 4080 跑通小规模 Pretrain
  - [ ] **[周二 · Full SFT 与 Loss Mask]** 跑通 MiniMind SFT，搞透为什么只对 `<assistant>` 回复区间计算 Cross-Entropy（Loss Mask = `-100`）
  - [ ] **[周三 · 手写 LoRA + 论文精读]** 手写 `LoRALinear`（验证 $B=0$ 初始化零扰动与参数冻结）+ 🔴 精读 *LoRA*（`papers/lora.md`）
  - [ ] **[周四 · 刷题]** 本周 3 道 Hot100（二叉树遍历与递归）
  - [ ] **[周五 · 周验收]** 盲写 `LoRALinear` 与 SFT Loss Mask（L2）+ **周六半天具身轻体验 #2**：MuJoCo 载入 Franka 机械臂体验关节控制
- **✂️ 落后可砍项**：Pretrain 控制在 1 小时内小规模收敛即可，重点放在 SFT 与 LoRA 机制。

### W07 · P1 收官核心数字：Qwen 4-bit QLoRA 结构化微调（01/04–01/10）

- **核心产出**：`projects/p1-tiny-llm/README.md` 填入「指令→严格工具调用 JSON」Zero-shot 基线 vs QLoRA 量化评测表
- **每日推进单**：
  - [ ] **[周一 · 数据集与评测基准]** 构造 1,500 条「复杂自然语言指令 → 工具调用 JSON」训练集与 200 条独立测试集，写好自动评测脚本（JSON 合法率 + 槽位准确率）
  - [ ] **[周二 · 4080 QLoRA 训练]** 用 Unsloth 在本机 4080 对 Qwen2.5（3B/7B）跑 4-bit QLoRA 微调，记录显存峰值与训练曲线
  - [ ] **[周三 · 评测对比表产出]** 跑完 Zero-shot 基线 vs QLoRA 微调后的 JSON 合法率、槽位准确率与 TTFT 延迟，写入 P1 `README.md`
  - [ ] **[周四 · 论文略读 + 刷题]** 🟢 略读 *QLoRA*（NF4 分位数量化与双重量化）+ 本周 4 道 Hot100（二叉树进阶/二分）
  - [ ] **[周五 · 周验收]** 口算 7B 模型 4-bit QLoRA 显存组成（权重 + LoRA 参数 + 优化器 + 激活）并与 `nvidia-smi` 实测对账（L3）
- **✂️ 落后可砍项**：若 7B 显存紧张直接用 `Qwen2.5-3B` 跑通完整对比表。

### W08 · 项目 P2 上半场：零框架手写 ReAct Agent（01/11–01/17）

- **核心产出**：`projects/p2-scratch-agent` 完成支持 3 个工具的 ReAct Agent + 30 题任务集评测表（Prompting vs ReAct）
- **每日推进单**：
  - [ ] **[周一 · ReAct 原理与协议]** 读 Anthropic *Building Effective Agents* + 🔴 精读 *ReAct*（`papers/react.md`），跑通 `react_loop_starter.py`
  - [ ] **[周二 · 工具注册与容错循环]** 扩展 ReAct 主循环：接入 3 个工具（本地文档检索、Python 沙盒执行、计算/文件读取）+ JSON 解析失败自恢复与 `max_steps` 熔断
  - [ ] **[周三 · 30 题固定评估集实测]** 在 30 道多步推理/工具题上评测 Direct Prompting vs ReAct 的成功率、平均步数与 Token 消耗
  - [ ] **[周四 · 刷题]** 本周 4 道 Hot100（二分查找与回溯）
  - [ ] **[周五 · 周验收]** 限时盲写 40 行 ReAct 核心状态机（L2）+ **周六半天具身轻体验 #3**：用 LeRobot 预训练 Diffusion Policy 跑 PushT 推理可视化
- **✂️ 落后可砍项**：沙盒只支持安全数学/字符串脚本执行，不搞复杂容器隔离。

### W09 · 项目 P2 下半场：混合检索 RAG → 里程碑 M2 简历 v1（01/18–01/24）

- **核心产出（🎯 里程碑 M2）**：BM25 + Dense + RRF 混合检索对比表 + 产出 **简历 v1**（填好 `career/resume_bullets_template.md`）
- **每日推进单**：
  - [ ] **[周一 · 分块与双路检索]** 将知识库切块，实现 `BM25` 关键词检索与向量语义检索（Dense Retrieval）
  - [ ] **[周二 · RRF 融合与评测]** 手写倒数秩融合 `RRF`（`1 / (k + rank)`），在 50 题问答集上跑出 `BM25 / Dense / Hybrid` 的 Recall@5 对比表
  - [ ] **[周三 · 接入 Agent 闭环]** 将 Hybrid RAG 封装为 W08 ReAct Agent 的检索工具，跑通端到端检索问答
  - [ ] **[周四 · 论文略读 + 刷题]** 🟢 略读 *RAG* + 本周 4 道 Hot100（图论/拓扑排序，含 **LC 207 课程表**）
  - [ ] **[周五 · M2 验收与简历合成]** 盲写 RRF 融合函数（L2）+ **周六全天：汇总 P1/P2 实验表，写完 `career/resume_bullets_template.md` 产出简历 v1！**
- **✂️ 落后可砍项**：Reranker 重排与 MCP 协议封装放到投递期的加分迭代，不阻塞简历 v1。

---

## 阶段三：对齐八股冲刺、日常实习投递与专项分流（W10+）

### W10 · 对齐八股冲刺 + 模拟面 + 启动日常实习投递（01/25–01/31）

- **核心产出**：掌握 RLHF / DPO / GRPO 高频面试推导 + 完成 2 轮累积模拟面试 + **正式投出 10–20 家日常实习**
- **每日推进单**：
  - [ ] **[周一 · InstructGPT 与 PPO 直觉]** 🔴 精读 *InstructGPT*，吃透 `SFT → RM → PPO` 三阶段流水线与 PPO 四个模型显存痛点
  - [ ] **[周二 · DPO 与 GRPO 核心原理]** 🔴 精读 *DPO*（掌握闭式解推导与chosen/rejected margin）+ 理解 *DeepSeekMath* **GRPO** 组内相对优势如何省掉 Critic
  - [ ] **[周三 · 模拟面试 #1（项目深挖）]** 让 AI 面试官围绕简历 v1 的 P1（GPT/LoRA/QLoRA）与 P2（ReAct/Hybrid RAG）进行 3 层追问拷问，整理卡壳点进复习卡
  - [ ] **[周四 · 模拟面试 #2（八股+手撕）]** 限时手撕 Multi-Head Causal Attention + 2 道高频 Hot100（Top-K / DP）
  - [ ] **[周五 · 启动投递]** 投出第一批 10–20 家日常实习，建立 `career/interview_log.md` 追踪真实面试问题并反哺复习卡
- **📍 W10 之后的分支决策点（2027-02 起，边面试边推进）**：
  - **分支 A（LLM / Agent 岗面试多）**：P1 补跑 MiniMind DPO 实验 → 进入 `projects/p3-agentic-rl` 跑 GSM8K GRPO 与 Search-R1 / ReTool。
  - **分支 B（具身智能 / VLA 岗面试多）**：进入 `projects/p4-robot-learning` 训练 LeRobot ACT / Diffusion Policy → 微调 SmolVLA。
