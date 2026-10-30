# 学习工作区文档规范（与现有 Lab 进度零冗余整合）

本设计吸收 Matt Pocock `teach` 的 `MISSION`、`RESOURCES`、`GLOSSARY`、`LEARNING-RECORDS`、`NOTES` 机制，并与本仓既有的 `ROADMAP_16W.md`、`REFERENCE_INDEX.md`、`学习/` 严格分工，**绝不维护两份相互冲突的进度表**。

---

## 1. 真相源边界表（什么往哪写？）

| 信息类型 | 唯一存放位置 | 严禁重复写到哪里 |
|---|---|---|
| 16 周里程碑、论文、刷题完成度 | `ROADMAP_16W.md`、`papers/READING_LIST.md`、`leetcode/hot100_tracker.md` | 不要在 `MISSION.md` 或 `NOTES.md` 复制任务勾选项 |
| 某个课题拆成哪几节课、学到第几课、何时复习 | `学习/<topic>/计划.md`（自动汇总到 `学习/index.md` 与 `index.html`） | 不要把细碎分课塞进 `ROADMAP_16W.md` |
| 为什么学、求职目标、全局取舍与硬约束 | `学习/MISSION.md` | 不要每节课重复问用户学习目的 |
| 主课程/视频/源码何时用哪份、社区与资料缺口 | `学习/RESOURCES.md`（与 `REFERENCE_INDEX.md` 互补） | 不要把 `REFERENCE_INDEX.md` 全表复制一遍 |
| 已学懂术语的统一定义与禁用混称 | `学习/GLOSSARY.md` | 未学过的陌生词不要提前塞进术语表充数 |
| 用户已具备的先验知识、踩过并纠正的关键误区 | `学习/learning-records/NNNN-<slug>.md` | 不要写成「今天学了第 X 课」的流水账日记（日记归 `daily/`） |
| 用户表达的教学偏好与节奏习惯 | `学习/NOTES.md` | — |

---

## 2. 各文件精简格式约定

### 2.1 `学习/MISSION.md`（保持一屏以内）
```markdown
# Mission: 27 届 LLM · Agent · 具身智能（VLA）算法实习通关

## Why
...（1–3 句真实目标）

## Success looks like
- ...（具体、可观察的产出）

## Constraints
- ...（算力、时间、教学方式偏好）

## Out of scope
- ...（保护最近发展区，当前明确不追的支线）
```

### 2.2 `学习/GLOSSARY.md`（只记已消化的概念！）
```markdown
**拓扑序（Topological Order）**:
有向无环计算图中保证「每个节点都在其所有后继节点之后进行反向传播」的线性排列；确保轮到节点 $v$ 执行 `_backward()` 时，$\partial L/\partial v$ 已完整汇总完毕。
_Avoid_: 层序遍历（非分层任意 DAG 中广度优先不一定满足依赖完整性）
```
- 规则：定义控制在 1–2 句话；标注 `_Avoid_` 易混词；后续课程与速查表严格沿用该术语。

### 2.3 `学习/learning-records/NNNN-<slug>.md`（教学版 ADR）
通过 `python3 study.py learn record <slug> --title "..." --body "..." [--evidence "..."] [--implications "..."]` 创建。
只在以下 4 种高价值时刻写入：
1. **证实真正掌握了某个非平凡基石**（上调后续课程的起点，不再重讲基础）。
2. **用户主动说明先验基础**（如「线性代数矩阵求导我已经很熟了」）。
3. **纠正了一个典型直觉误区**（极其宝贵，后续相似概念可主动提前预警，如广播求和梯度、掩码位置、因果偏移）。
4. **学习主线目标发生实质调整**（同步更新 `MISSION.md`）。
> 若后续理解深化推翻旧记录，在旧文件顶部加 `Status: superseded by LR-NNNN`，保留认知演进轨迹。

### 2.4 `学习/<topic>/计划.md`
头部键值字段由 `course.py` 自动解析，请保持格式稳定：
```markdown
# w01-自动微分与P1

目标: ...
关联: ROADMAP W01（标量自动微分 + P1 NumPy/PyTorch MNIST）
来源: concepts/w01_micro_autograd.py, projects/p1-tiny-llm/src/w01_mlp_mnist.py, ../03-深度学习/模型笔记/01-多层感知机与反向传播.ipynb
状态: 进行中

## 依赖图
```mermaid
flowchart LR
  ...
```

## 课程（每一步 = 一节 HTML 课）
- [x] 1. 标量计算图与反向传播三条铁律 — 掌握标志: ... → [课程页](lessons/0001-scalar-autograd-chain.html) ✓2026-10-30
- [ ] 2. ... — 掌握标志: ...

## 复习
- 2026-10-30 复习 第 1 课
```
