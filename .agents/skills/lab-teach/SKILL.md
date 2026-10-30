---
name: lab-teach
description: >-
  Teaches AI, math, deep learning, LLM, Agent, RL, and Embodied VLA topics over
  multi-session interactive HTML lessons grounded in AI Tutorial notebooks and
  Lab source code. Use whenever the user says "开始学习 XX", "继续", "详细推导",
  "讲解代码", "可视化", "复习", "整理笔记", or asks to learn a course/concept with
  clear intuition, math derivations, code walkthroughs, interactive visualizations,
  and persistent HTML notes in 学习/.
---

# Lab-Teach Skill（AI Lab 分轮教学与交互式 HTML 课程引擎）

本技能借鉴 Matt Pocock `teach` 的工作区与认知科学设计，结合本仓 **LLM → Agent → 具身智能（VLA）** 16 周主线，将上层 `../`（AI Tutorial 原始 `.ipynb`/`.md`）与 `lab/` 真实代码转化为**分轮渐进教学 + 可复用交互式 HTML 课程页**。

---

## 1. 核心教学哲学（获取期减负 · 默认不强制考核）

1. **以「真正教会」为唯一目标**：讲清 **痛点直觉 → 2×2 极小数字例子 → 核心原理与公式推导 → 真实代码逐段映射 → 可交互可视化实验**。
2. **获取知识时，阻力是敌人（Fluency vs Storage Strength）**：
   - 初学概念时工作记忆极小，**严禁为了形式主义把关键公式或核心代码藏起来逼用户猜**。在 `学习/` 课程中，直接展示完整公式与真实代码并讲透每一行。
   - **默认不强制练习或提问考核**：自测题与面试三层追问统一放进 HTML 页面底部的 `details.reveal.q` 折叠块（默认收起，用户想自测时再点开）。
   - 仅当用户主动发出 `练一下` / `盲写` / `考考我` 时，才联动 `socratic-tutor`（去 `concepts/` 生成 `# TODO(human)` 盲写桩）或 `mock-interviewer`。
3. **按知识点类型灵活裁剪结构**（切勿每节课机械套同一套八股，详见 [references/pedagogy.md](./references/pedagogy.md)）：
   - **数学 / 算子类**（如自动微分、Softmax+CE、RoPE、DPO/GRPO Loss、雅可比阻尼伪逆）：重 **2×2 手算 + 分步符号推导 `.lab-stepper` + 滑块动态曲线/热力图**。
   - **模型架构类**（如 MLP、Causal Self-Attention、GQA、MiniMind、LLaVA、ACT/DP）：重 **张量 Shape 追踪表 `table.shape` + 计算图/数据流 `LabPlot.graph` + 源码 `.code-walk`**。
   - **工程 / Agent 协议类**（如 BPE、KV Cache、ReAct、MCP、Hybrid RAG RRF）：重 **状态流转演示 + 边界/退化案例对比 + 真实项目文件逐段拆解**。
4. **单课工作记忆边界**：一节 HTML 课只聚焦 **1 个可触摸的收获（Tangible Win）**，控制在 15–25 分钟可读完。大主题拆成 3–6 节小课分轮推进。

---

## 2. 一句话指令自动路由表

收到用户简短指令时，无需反问流程，直接按表执行对应动作并同步 HTML 笔记：

| 用户指令 | 立即执行的标准动作流 |
|---|---|
| **「开始学习 XX」** | ① 跑 `python3 study.py learn status` 与 `python3 study.py dict <XX>` 定位上层原始 `.ipynb`/`.md` 及 `lab/` 代码 → ② 读 `learning-records/` 与 `ROADMAP_16W.md` 分析前置依赖（区分 `✓已掌握` / `△本课顺手3句话补齐` / `主线分课`）→ ③ 用 `new-topic` 建立（或复用）`学习/<slug>/计划.md` 写入 Mermaid 依赖图与 3–6 步分课单 → ④ **不空谈计划，当轮直接生成并讲授第 1 课 HTML**！ |
| **「继续」** | ① 跑 `python3 study.py learn status` 找到当前 `👉` 课题；若上一课刚学完且无阻塞，先 `learn done <topic> <prev_step>` → ② 跑 `learn context <topic>` 读取下一课目标、术语表与 ZPD 记录 → ③ 读取对应原始 Notebook/代码，跑 Python 金标准，生成下一课 `lessons/NNNN-*.html`，通过 `check --browser` 后在对话中做精要导读并 `learn open`。 |
| **「详细推导」** | 针对当前课（或指定公式）：先给 2×2 具体数字算例，再写每步只变一处的完整符号推导（标明维度、展开依据、抵消项）+ Python 数值差分验证；将推导写入或更新至当前 HTML 课程页的 `.lab-stepper` / `.eq-explain` / `details.deep`。 |
| **「讲解代码」** | 用 `python3 study.py learn nb` / `snippet` 精确提取 AI Tutorial Notebook Cell 或 `concepts/`、`projects/` 真实源码（绝不凭记忆瞎编伪代码）；构建「公式符号 ↔ 变量名 ↔ Shape ↔ 防坑细节」的 `.code-walk` 双栏高亮联动并更新到当前 HTML 课程页。 |
| **「可视化」** | 为当前概念设计可交互实验（`Lab.playground` 参数滑块 + `LabPlot.chart / heatmap / bars / graph`），先写微型 Python 脚本算出金标准注入 `lab-golden`，再用 `Lab.check` 与 `check --browser` 校验零误差，更新进 HTML 课程页。 |
| **「复习」** | 检查 `learn status` 到期课题（1/3/7/21 天间隔）或用户指定章节；在对话中用 3 个主动回忆卡片（痛点 → 核心公式/Shape → 常见坑）带用户快速串讲，更新课程页折叠自测或速查表，并运行 `learn reviewed <topic>` 记录。 |
| **「整理笔记」** | ① 将本课题已学课程压缩成 1–2 页 A4 可打印速查卡 `学习/reference/<slug>.html`（`new-ref`）→ ② 把已真正消化的术语写入 `学习/GLOSSARY.md` → ③ 若本轮有非显然顿悟/误区修正/先验知识披露，运行 `learn record` 记一条 Learning Record → ④ 运行 `learn index` 刷新 `学习/index.md` 与 `学习/index.html`（若整章完结，提醒勾选 `ROADMAP_16W.md` 并跑 `python3 study.py brief`）。 |
| **「练一下 / 盲写」** | （用户主动要求时）切换到 `socratic-tutor` 技能，在 `concepts/` 生成 `<80` 行 `# TODO(human)` + `assert` 脚本陪练。 |

---

## 3. 工作区结构与单一真相源（严禁重复记账！）

本工作区复用 `学习/` 目录，与仓库全局文件职责严格正交（格式规范见 [references/workspace-formats.md](./references/workspace-formats.md)）：

```text
lab/
├── ROADMAP_16W.md                     # 【周/里程碑级唯一真相源】61 项主线复选框
├── REFERENCE_INDEX.md                 # 上层仓库按需速查映射表（不重复抄写）
├── .agents/skills/lab-teach/
│   ├── SKILL.md                       # 本文件
│   ├── scripts/course.py              # 零依赖引擎（通过 `python3 study.py learn ...` 调用）
│   ├── assets/                        # 共享组件：lab.css / lab.js / lab-math.js / lab-plot.js / vendor(katex,hljs)
│   ├── templates/                     # lesson.html / reference.html / plan.md
│   └── references/                    # 按需查阅的组件 API、教学法、文档格式与校验规范
└── 学习/
    ├── MISSION.md                     # 学习北极星（Why / 成功标准 / 约束 / 暂不追的支线；不记进度）
    ├── RESOURCES.md                   # 高可信课程/源码/社区策展（标注何时查阅哪份资料）
    ├── GLOSSARY.md                    # 已掌握概念的压缩定义与禁用混词（全课程统一术语）
    ├── NOTES.md                       # 用户个人学习偏好与节奏便签
    ├── learning-records/0001-*.md     # 教学版 ADR：记录先验知识、误区修正与 ZPD 边界（非流水账！）
    ├── reference/*.html               # 跨课复用的可打印高密度速查卡
    ├── index.md & index.html          # 自动生成的 Markdown 索引与可视化学习地图（勿手改）
    └── <topic-slug>/
        ├── 计划.md                    # 【课题课级真相源】依赖图 + 分课步骤 + 复习记录
        ├── verify_*.py                # （可选）生成本课题课程页 Python 金标准的验证脚本
        └── lessons/0001-*.html        # 自包含交互式 HTML 课程页（共享 assets/）
```

---

## 4. 生成或更新一节 HTML 课程页的 6 步标准流水线

每次制作或大改 HTML 课程页时，严格执行以下闭环（详见 [references/sources-and-verification.md](./references/sources-and-verification.md) 与 [references/html-lesson.md](./references/html-lesson.md)）：

1. **取源（Ground in Real Course & Code）**
   - 主力机存在 `../` 时，先跑：
     ```bash
     python3 study.py dict <关键词>
     python3 study.py learn nb "../路径/课程.ipynb" --outline
     python3 study.py learn nb "../路径/课程.ipynb" --cells 5-8
     ```
   - 同时检查 `concepts/` 与 `projects/p1..p5` 是否已有对应真实代码。**优先使用原始 Notebook 公式符号体系与 Lab 真实源码**（远程/网页端无 `../` 时，使用 Lab 代码 + 一手论文推导，并在 `context` 输出中确认）。
2. **建页（Scaffold）**
   - 新课运行：
     ```bash
     python3 study.py learn new-lesson <topic> <slug> --title "课程标题" --step <N>
     ```
   - 代码块一律用 `snippet` 生成以保证文件路径、起始行号、转义 100% 准确：
     ```bash
     python3 study.py learn snippet concepts/w01_micro_autograd.py --lines 24-62 --for 学习/<topic>/lessons/0001-xxx.html
     ```
3. **算金标准（Python Golden Standard）**
   - **严禁心算任何小数、梯度、矩阵乘积或损失值！**
   - 写一个微型验证脚本（如 `学习/<topic>/verify_0001.py`，最后一行 `print(json.dumps(golden))`），用 Conda Python 跑出精确数值并注入课程页 `#lab-golden`：
     ```bash
     python3 study.py learn golden 学习/<topic>/lessons/0001-xxx.html 学习/<topic>/verify_0001.py
     ```
4. **写交互（Author Components）**
   - 复用 `assets/` 组件（`.callout`、`.lab-stepper`、`.eq-explain`、`.code-walk`、`Lab.playground`、`LabPlot.chart/heatmap/bars/graph`、`details.reveal`），绝不重复手写一套内联样式。
   - 在 `Lab.ready(() => { ... })` 中调用 `Lab.check("键名", jsComputedValue)` 将浏览器端交互默认输出与 `#lab-golden` 比对。
5. **自检（Automated Verification）**
   - 交付前必须运行无头浏览器校验，确保 **0 个未填占位符、0 断链、0 JS 报错、所有 `Lab.check` 100% 通过**：
     ```bash
     python3 study.py learn check 学习/<topic>/lessons/0001-xxx.html --browser
     python3 study.py learn index
     ```
   - 复杂排版或新图表可用 `python3 study.py learn shot <html路径> --out /tmp/preview.png` 截图目检。
6. **导读与打开（Deliver Concisely）**
   - 运行 `python3 study.py learn open 学习/<topic>/lessons/0001-xxx.html` 为用户打开页面（无桌面环境则只给可点击链接）。
   - **聊天窗口不要把 HTML 全文复述一遍！** 只需用 5–10 行给出：① 本课核心直觉（3 句话内）、② 建议在页面里重点拖动的 1 个交互实验、③ 下一步可以说的快捷指令（如 `继续` / `详细推导` / `可视化` / `整理笔记`）。

---

## 5. 按需深读参考手册（Progressive Disclosure）

- 需要编写 HTML 交互组件、绘图或查阅 CSS/JS 类名与 API → 读 [references/html-lesson.md](./references/html-lesson.md)
- 需要针对不同类型知识点设计教学节奏、依赖拆分或间隔复习 → 读 [references/pedagogy.md](./references/pedagogy.md)
- 需要创建/维护 `MISSION.md`、`GLOSSARY.md`、`RESOURCES.md`、`learning-records/` → 读 [references/workspace-formats.md](./references/workspace-formats.md)
- 需要查阅 Notebook 提取与 Python 金标准数值验证细节 → 读 [references/sources-and-verification.md](./references/sources-and-verification.md)
