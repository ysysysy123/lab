# 🚀 AI Lab：LLM → Agent → 具身智能 个人实战工作台

> **定位**：这是面向 **27 届实习（日常实习 + 2027 春招）** 搭建的本地个人学习与作品集仓库（Monorepo）。  
> 上层目录 `../`（`autumn-recruitment`）已降级为**只读字典与面试题库**（通过 `.git/info/exclude` 隔离，互不污染）；你所有的代码、盲写微实验、论文卡片和 5 个简历项目都沉淀在当前 `lab/` 独立 Git 仓库中，可随时 `git push` 到你自己的 GitHub 主页作为求职作品集。

---

## 一、 为什么以前觉得「读起来很累、学不下去」？这套工作流怎么改？

原本直接啃上层仓库 23 个目录之所以痛苦，是因为**只有密集静态文字输入、没有即时运行反馈、每天坐下不知道先干嘛**。本地工作流改成以下 **4 条铁律**：

1. **禁止通读上层仓库，只做「按需查字典」**
   - 主线输入全部换成**视频/可视化 + 开源项目源码**（Karpathy / 3B1B / 李宏毅 / MiniMind / hello-agents / HF LeRobot）。
   - 卡在某个公式（如 RoPE、GRPO、雅可比伪逆）时，在终端敲一行命令精准定位上层仓库对应段落，看完即走：
     ```bash
     python3 study.py dict RoPE
     python3 study.py dict 雅可比
     ```
2. **「每日四段并行」替代「连啃一周理论」**
   - **上午（1.5h · 原理）**：1.25x 看视频，看完不抄长篇笔记，去 `concepts/` 用 30–50 行代码盲写核心逻辑并 `assert` 跑通。
   - **下午（3.0h · 项目）**：在 `projects/p1..p5` 推进实战，**当天必须看到可感知的输出**（Loss 下降 / Agent 调通工具 / 机械臂在仿真器里动起来）。
   - **晚上（45m · 论文）**：用 `python3 study.py paper <简称> --skim`（略读 30 分钟填 3 行）或 `--deep`（精读 2 小时填半页），绝不写万字翻译。
   - **睡前（30m · 手撕）**：从第 3 周起在 `leetcode/` 每天写 1 道 Hot100，保持编码手感。
3. **「阶段串行 + 阶段内多线并行」榨干三端算力**
   - **阶段串行**：`W1-4 地基(GPT)` → `W5-10 LLM训练 ∥ Agent` → `W11-16 运动学 ∥ 模仿学习 ∥ VLA`。
   - **阶段内并行**：当本地 **RTX 4080 Laptop (12GB)** 或远程 **A800 (80GB)** 在后台跑训练时，切去写纯 CPU/API 的 Agent 代码或读论文，不干等进度条。
4. **两天熔断机制**
   - 任何推导或环境报错卡住超过 2 天，立刻记录在 `daily/` 的「阻塞问题」栏跳过，先保项目主线推进。

---

## 二、 目录结构全景

```text
lab/                                  # 独立 Git 仓库（你的个人作品集）
├── README.md                         # 本手册：学习方式 + 目录导航 + 常用命令
├── ROADMAP_16W.md                    # 16 周任务看板（支持 study.py 自动统计进度）
├── REFERENCE_INDEX.md                # 上层仓库「字典映射表」与断舍离清单
├── study.py                          # 零依赖 CLI 学习助手（打卡/查字典/建笔记/网页AI同步简报）
├── AGENTS.md                         # AI 全局助教宪法（防代写 · 分目录切换教练/架构师/面试官模式）
├── CLAUDE.md                         # Claude Code 规则指针（自动引用 AGENTS.md）
├── WEB_AI_BRIEF.md                   # 网页端 AI 实时交接单（由 study.py brief 一键刷新）
├── .agents/skills/                   # 4 个专属 AI 技能（苏格拉底教学/论文陪读/模拟面/多端同步）
├── ai_companion/MULTI_DEVICE_GUIDE.md # 多设备 Git 推送 + 网页版 AI 协同完整指南
│
├── env/                              # 算力环境配置（RTX 4080 12G / Colab T4 16G / A800 80G）
│   ├── README.md                     # 三卡精细分工（附本机 Ubuntu 26.04 Python 3.14 避坑说明）
│   ├── setup_local_conda.sh          # 一键配置本地 Conda 环境（ai-lab 与 robot-lab）
│   ├── check_gpu.py                  # 显卡能力自检（BF16 / TF32 / SDPA FlashAttention）
│   ├── colab_bootstrap.md            # Colab T4 启动代码片段（FP16 避坑）
│   └── sync_a800.sh                  # 本地 ↔ A800 代码同步与 tmux 训练启动模板
│
├── concepts/                         # 费曼盲写沙盒：每个核心概念一个 <80 行可运行脚本
│   └── w01_micro_autograd.py         # [立即可跑] 50 行微型自动微分引擎 + 神经元训练验证
├── daily/                            # 每日并行打卡日志（由 study.py today 自动生成）
├── papers/                           # 30 篇精选论文卡片（区分 🔴精读 与 🟢略读 极简模板）
├── leetcode/                         # 实习必刷 Hot100 追踪单与带测试模板
│
├── projects/                         # 5 大递进式简历项目（最终浓缩为简历上的 3 段硬核经历）
│   ├── p1-tiny-llm/                  # [W1-W6] 手写 GPT & BPE → MiniMind 全流程 → 7B QLoRA
│   ├── p2-scratch-agent/             # [W5-W8] 纯手写 ReAct + MCP + 混合检索 RAG + Coding Agent
│   ├── p3-agentic-rl/                # [W9-W10] GRPO / Search-R1：训练 3B 模型自主调用检索器
│   ├── p4-robot-learning/            # [W11-W13] MuJoCo 雅可比 IK + LeRobot ACT/DP + VLA 微调
│   └── p5-embodied-capstone/         # [W14-W16] 分层具身智能体：VLM/Agent 大脑 + 技能/VLA 小脑
│
└── career/                           # 27 届实习投递作战室（W8 简历 v1 / W16 简历 v2 / 面经复盘）
```

---

## 三、 本机硬件专属诊断（已为你实测）

- **本机 GPU**：`NVIDIA GeForce RTX 4080 Laptop GPU (12 GB)`（Ada Lovelace 架构）
  - **关键优势**：原生支持 **BF16** 与 **FlashAttention-2**，算力与显存带宽远强于 Colab T4！因此 **90% 的日常开发、MiniMind 全流程、Unsloth 7B 4-bit QLoRA、0.5B/1.5B GRPO 小实验、MuJoCo 仿真、LeRobot ACT/Diffusion Policy 全部优先在本机跑**，体验最丝滑。
  - **Colab T4 (16GB)** 仅在需要 13–15GB 显存或并行跑第二组超参时作为辅助（注意 T4 不支持 BF16，必须开 `fp16=True`）。
  - **远程 A800 (80GB)** 专攻重型任务：W8 部署 vLLM 7B/14B、W10 跑 3B Agentic RL (veRL/TRL)、W13 微调 OpenVLA / π0。**本周内请先提交 A800 申请！**
- **本机 Python 避坑**：系统自带 `/usr/bin/python3` 为 `Python 3.14`（Ubuntu 26.04），直接 `pip install` 深度学习或机器人库会因缺少预编译包报错。请务必使用你本机已安装的 `~/Apps/miniconda3` 运行 `bash env/setup_local_conda.sh` 创建 **Python 3.11** 环境。

---

## 四、 Day 1 五分钟点火启动（现在就能敲）

```bash
cd /mnt/study/github/autumn-recruitment/lab

# 1. 查看整体进度看板与第 1 周任务
python3 study.py status
python3 study.py week 1

# 2. 零依赖跑通第一个 50 行自动微分实验（立刻获得正反馈！）
python3 concepts/w01_micro_autograd.py

# 3. 生成今天的学习作战单
python3 study.py today

# 4. 试试把上层仓库当「字典」检索（例如查 Attention 或 线性代数）
python3 study.py dict 自注意力

# 5. 一键初始化本地 Conda 深度学习与具身环境（需联网）
bash env/setup_local_conda.sh
```

---

## 五、 `study.py` 常用命令速查

| 命令 | 作用 |
|---|---|
| `python3 study.py status` | 查看 16 周任务、30 篇论文、Hot100 与 5 大项目的整体完成度 |
| `python3 study.py week 5` | 单独打印第 5 周的多线并行任务清单（不翻长文档） |
| `python3 study.py today` | 在 `daily/` 下生成今日四段式打卡文件，并自动带出当前周待办 |
| `python3 study.py dict <关键词>` | 在上层 `autumn-recruitment` 仓库的核心章节中秒搜概念与公式位置 |
| `python3 study.py paper attention --deep` | 用精读模板创建 `papers/` 笔记（加 `--skim` 则用 3 行略读卡） |
| `python3 study.py lc 001_two_sum` | 在 `leetcode/` 下生成带 `assert` 自测框架的刷题脚本 |
| `python3 study.py brief` | 一键刷新 `WEB_AI_BRIEF.md`，推上 GitHub 或粘贴给网页版 AI 秒级续接进度 |

