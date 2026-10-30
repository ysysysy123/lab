#!/usr/bin/env python3
"""
study.py — 本地学习流零依赖 CLI 助手
用法：
  python3 study.py status                  # 查看 16 周路线、论文、刷题整体完成度
  python3 study.py week <1-16>             # 单独查看第 N 周的多线并行任务
  python3 study.py today                   # 生成今日四段式并行打卡单 daily/YYYY-MM-DD.md
  python3 study.py dict <关键词>            # 把上层仓库当字典：秒搜核心章节中的概念/公式位置
  python3 study.py paper <slug> [--deep|--skim]  # 从精读/略读模板新建论文卡片
  python3 study.py lc <slug>               # 新建带 assert 自测的 LeetCode 练习文件
  python3 study.py learn [子命令 ...]       # lab-teach 交互式课程与 HTML 笔记工作区（默认 status）
  python3 study.py brief                   # 生成 WEB_AI_BRIEF.md 供网页端 AI / 多设备秒级同步进度
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
REF_REPO_DIR = Path(os.environ.get("AUTUMN_REF_DIR", str(LAB_DIR.parent))).resolve()
ROADMAP_FILE = LAB_DIR / "ROADMAP_16W.md"
PAPERS_LIST_FILE = LAB_DIR / "papers" / "READING_LIST.md"
LC_TRACKER_FILE = LAB_DIR / "leetcode" / "hot100_tracker.md"
WEB_BRIEF_FILE = LAB_DIR / "WEB_AI_BRIEF.md"

# 字典检索默认聚焦的核心章节（屏蔽数仓/推荐/语音/数据分析等无关噪音）
CORE_REF_PREFIXES = (
    "00-数学基础",
    "01-数据结构与算法",
    "03-深度学习",
    "04-LLM大模型",
    "05-八股与工程",
    "07-强化学习",
    "08-优化算法",
    "09-计算机视觉",
    "12-智能体开发",
    "13-编程语言",
    "14-具身智能",
    "15-AI-Infra",
    "20-多模态大模型",
    "22-图神经网络与知识图谱",
)


def count_checkboxes(md_path: Path) -> tuple[int, int]:
    """返回 (已完成数, 总数)"""
    if not md_path.exists():
        return 0, 0
    text = md_path.read_text(encoding="utf-8")
    done = len(re.findall(r"^\s*-\s*\[[xX]\]\s+", text, flags=re.MULTILINE))
    todo = len(re.findall(r"^\s*-\s*\[\s\]\s+", text, flags=re.MULTILINE))
    return done, done + todo


def parse_weeks(roadmap_text: str) -> dict[int, tuple[str, str]]:
    """解析 ROADMAP_16W.md 中的 ### W01 .. ### W16 区块，返回 {week_num: (title, body)}"""
    pattern = re.compile(r"^###\s+W(\d{2})\s*·\s*(.+)$", flags=re.MULTILINE)
    matches = list(pattern.finditer(roadmap_text))
    weeks: dict[int, tuple[str, str]] = {}
    for idx, m in enumerate(matches):
        w_num = int(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(roadmap_text)
        block = roadmap_text[start:end].strip()
        # 截掉跨阶段分隔符及下一阶段大标题
        block = re.split(r"\n---\s*\n", block)[0].strip()
        weeks[w_num] = (title, block)
    return weeks


def find_active_week(weeks: dict[int, tuple[str, str]]) -> int:
    """找到第一个还有未完成任务的周次"""
    for w in sorted(weeks):
        _, block = weeks[w]
        if re.search(r"^\s*-\s*\[\s\]\s+", block, flags=re.MULTILINE):
            return w
    return max(weeks) if weeks else 1


def bar(done: int, total: int, width: int = 24) -> str:
    if total == 0:
        return "[" + "." * width + "] 0/0"
    filled = int(round(width * done / total))
    pct = 100.0 * done / total
    return f"[{'█' * filled}{'░' * (width - filled)}] {done}/{total} ({pct:.0f}%)"


def _load_course_engine():
    script = LAB_DIR / ".agents" / "skills" / "lab-teach" / "scripts" / "course.py"
    if not script.exists():
        return None
    spec = importlib.util.spec_from_file_location("lab_teach_course", script)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_status(_args: argparse.Namespace) -> None:
    r_done, r_total = count_checkboxes(ROADMAP_FILE)
    p_done, p_total = count_checkboxes(PAPERS_LIST_FILE)
    l_done, l_total = count_checkboxes(LC_TRACKER_FILE)

    daily_logs = sorted(
        p for p in (LAB_DIR / "daily").glob("*.md") if not p.name.startswith("_")
    )
    paper_notes = sorted(
        p
        for p in (LAB_DIR / "papers").glob("*.md")
        if not p.name.startswith("_") and p.name != "READING_LIST.md"
    )
    concept_scripts = sorted(
        p for p in (LAB_DIR / "concepts").glob("*.py") if not p.name.startswith("_")
    )

    print("=" * 64)
    print("🚀 AI Lab 学习进度总控台 (LLM → Agent → 具身智能)")
    print("=" * 64)
    print(f"  16周主线任务 : {bar(r_done, r_total)}")
    print(f"  30篇论文清单 : {bar(p_done, p_total)}  (已写卡片: {len(paper_notes)} 篇)")
    print(f"  Hot100 刷题  : {bar(l_done, l_total)}")
    print(f"  每日打卡累计 : {len(daily_logs)} 天  |  盲写微实验: {len(concept_scripts)} 个")

    if ROADMAP_FILE.exists():
        weeks = parse_weeks(ROADMAP_FILE.read_text(encoding="utf-8"))
        active_w = find_active_week(weeks)
        if active_w in weeks:
            title, block = weeks[active_w]
            open_tasks = re.findall(
                r"^\s*-\s*\[\s\]\s+(.+)$", block, flags=re.MULTILINE
            )
            print("-" * 64)
            print(f"📍 当前聚焦周次: W{active_w:02d} · {title}")
            for item in open_tasks[:4]:
                print(f"   • {item}")
            if len(open_tasks) > 4:
                print(f"   ... 其余 {len(open_tasks) - 4} 项用 `python3 study.py week {active_w}` 查看")
    course_mod = _load_course_engine()
    if course_mod is not None:
        print("-" * 64)
        print("📘 交互式课程工作区 (学习/ · lab-teach):")
        for line in course_mod.summary_lines():
            print(f"  {line}")
    print("=" * 64)


def cmd_week(args: argparse.Namespace) -> None:
    if not ROADMAP_FILE.exists():
        sys.exit(f"未找到 {ROADMAP_FILE}")
    weeks = parse_weeks(ROADMAP_FILE.read_text(encoding="utf-8"))
    w = args.num
    if w not in weeks:
        sys.exit(f"周次 {w} 不在 1..{max(weeks, default=16)} 范围内")
    _, block = weeks[w]
    print(block)


def cmd_today(args: argparse.Namespace) -> None:
    today_str = args.date or dt.date.today().isoformat()
    daily_dir = LAB_DIR / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    target = daily_dir / f"{today_str}.md"
    if target.exists() and not args.force:
        print(f"✅ 今日打卡文件已存在: {target}")
        return

    active_header = "W01"
    suggested = []
    if ROADMAP_FILE.exists():
        weeks = parse_weeks(ROADMAP_FILE.read_text(encoding="utf-8"))
        active_w = find_active_week(weeks)
        if active_w in weeks:
            title, block = weeks[active_w]
            active_header = f"W{active_w:02d} · {title}"
            suggested = re.findall(
                r"^\s*-\s*\[\s\]\s+(.+)$", block, flags=re.MULTILINE
            )

    todo_lines = "\n".join(f"- [ ] {t}" for t in suggested) or "- [ ] 自选推进项"
    content = f"""# 📅 {today_str} 学习作战单（当前焦点：{active_header}）

## 🎯 本周待办池（挑 1–2 项推进即可，别贪多）
{todo_lines}

---

## ⏱️ 今日四段式并行记录

### 1. 上午 · 原理输入与盲写验证（1.5h）
- **视频 / 资料**：
- **30行盲写文件**（`concepts/...`）：
- **一句话搞懂了什么**：

### 2. 下午 · 项目实战推进（3.0h）
- **所在项目**（`projects/p1..p5`）：
- **算力端**（本机 4080 / Colab T4 / 远程 A800）：
- **今日可见产出**（Loss 数值 / 跑通模块 / 截图或日志）：

### 3. 晚上 · 论文阅读（45m）
- **论文名称与卡片路径**（`papers/...`）：
- **核心 takeaway（1–2 句）**：

### 4. 睡前 · 手撕代码（30m，W03 起）
- **题目**（`leetcode/...`）：
- **核心套路 / 卡点**：

---

## 🚧 阻塞问题（卡超 2 天自动熔断跳过！）
- 
"""
    target.write_text(content, encoding="utf-8")
    print(f"✨ 已生成今日学习作战单: {target}")


def search_in_notebook(nb_path: Path, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    try:
        data = json.loads(nb_path.read_text(encoding="utf-8"))
    except Exception:
        return hits
    for idx, cell in enumerate(data.get("cells", []), start=1):
        src = "".join(cell.get("source", []))
        for line in src.splitlines():
            if pattern.search(line):
                snippet = line.strip()
                if len(snippet) > 100:
                    snippet = snippet[:97] + "..."
                hits.append((idx, snippet))
                break
        if len(hits) >= 3:
            break
    return hits


def search_in_markdown(md_path: Path, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    try:
        lines = md_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return hits
    for lineno, line in enumerate(lines, start=1):
        if pattern.search(line):
            snippet = line.strip()
            if len(snippet) > 100:
                snippet = snippet[:97] + "..."
            hits.append((lineno, snippet))
            if len(hits) >= 3:
                break
    return hits


def cmd_dict(args: argparse.Namespace) -> None:
    core_dirs = [REF_REPO_DIR / name for name in CORE_REF_PREFIXES if (REF_REPO_DIR / name).exists()]
    if not core_dirs:
        print(f"ℹ️ 当前设备在 {REF_REPO_DIR} 未检测到 `autumn-recruitment` 参考库目录（远程 A800 / Colab 独立克隆属正常现象）。")
        print("   👉 你可以直接让当前 AI 按 AGENTS.md 的苏格拉底模式为你推导，或设置环境变量 AUTUMN_REF_DIR=/path/to/autumn-recruitment。")
        return

    keyword = args.keyword.strip()
    pattern = re.compile(re.escape(keyword), flags=re.IGNORECASE)

    search_dirs = (
        [d for d in sorted(REF_REPO_DIR.iterdir()) if d.is_dir() and not d.name.startswith(".") and d.name != "lab"]
        if args.all
        else core_dirs
    )

    filename_matches: list[Path] = []
    content_matches: list[tuple[Path, str, list[tuple[int, str]]]] = []

    for folder in search_dirs:
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".ipynb"}:
                continue
            if ".ipynb_checkpoints" in path.parts:
                continue
            if pattern.search(path.name):
                filename_matches.append(path)
            if path.suffix == ".md":
                hits = search_in_markdown(path, pattern)
                if hits:
                    content_matches.append((path, "L", hits))
            elif path.suffix == ".ipynb":
                hits = search_in_notebook(path, pattern)
                if hits:
                    content_matches.append((path, "Cell#", hits))

    print(f"🔎 在上层参考库检索「{keyword}」（范围：{'全库' if args.all else 'LLM/Agent/具身核心章节'}）")
    print("-" * 64)
    if filename_matches:
        print("📂 文件名直接命中（最推荐优先点开）：")
        for p in filename_matches[:10]:
            print(f"  ★ {p.relative_to(REF_REPO_DIR)}")
        print()

    if content_matches:
        print(f"📄 正文命中（前 {min(args.limit, len(content_matches))} 个文件，看完对应段落即关！）：")
        for p, kind, hits in content_matches[: args.limit]:
            print(f"  ▸ {p.relative_to(REF_REPO_DIR)}")
            for loc, snippet in hits:
                print(f"      [{kind}{loc}] {snippet}")
    elif not filename_matches:
        print("未命中结果。可尝试更换英文/中文简称，或加 `--all` 搜索全仓库。")


def cmd_paper(args: argparse.Namespace) -> None:
    slug = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]+", "_", args.slug.strip()).strip("_")
    mode = "skim" if args.skim else "deep"
    tpl_path = LAB_DIR / "papers" / f"_template_{mode}.md"
    out_path = LAB_DIR / "papers" / f"{slug}.md"
    if out_path.exists():
        print(f"✅ 论文笔记已存在: {out_path}")
        return
    if tpl_path.exists():
        tpl = tpl_path.read_text(encoding="utf-8").replace("{{TITLE}}", slug)
        tpl = tpl.replace("{{DATE}}", dt.date.today().isoformat())
    else:
        tpl = f"# {slug}\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl, encoding="utf-8")
    print(f"✨ 已创建{'🟢 30分钟略读卡' if mode == 'skim' else '🔴 2小时精读笔记'}: {out_path}")


def cmd_lc(args: argparse.Namespace) -> None:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", args.slug.strip()).strip("_")
    tpl_path = LAB_DIR / "leetcode" / "_template.py"
    out_path = LAB_DIR / "leetcode" / f"{slug}.py"
    if out_path.exists():
        print(f"✅ 刷题文件已存在: {out_path}")
        return
    tpl = (
        tpl_path.read_text(encoding="utf-8").replace("{{PROBLEM}}", slug)
        if tpl_path.exists()
        else f"# {slug}\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl, encoding="utf-8")
    print(f"✨ 已创建刷题练习脚本: {out_path}")


def cmd_brief(_args: argparse.Namespace) -> None:
    r_done, r_total = count_checkboxes(ROADMAP_FILE)
    p_done, p_total = count_checkboxes(PAPERS_LIST_FILE)
    l_done, l_total = count_checkboxes(LC_TRACKER_FILE)

    active_header = "W01"
    open_tasks: list[str] = []
    done_tasks: list[str] = []
    if ROADMAP_FILE.exists():
        roadmap_txt = ROADMAP_FILE.read_text(encoding="utf-8")
        weeks = parse_weeks(roadmap_txt)
        active_w = find_active_week(weeks)
        if active_w in weeks:
            title, block = weeks[active_w]
            active_header = f"W{active_w:02d} · {title}"
            open_tasks = re.findall(r"^\s*-\s*\[\s\]\s+(.+)$", block, flags=re.MULTILINE)
        done_tasks = re.findall(r"^\s*-\s*\[[xX]\]\s+(.+)$", roadmap_txt, flags=re.MULTILINE)

    daily_logs = sorted(
        p for p in (LAB_DIR / "daily").glob("*.md") if not p.name.startswith("_")
    )
    latest_daily_name = daily_logs[-1].name if daily_logs else "暂无打卡日志"

    open_md = "\n".join(f"- [ ] {t}" for t in open_tasks) or "- 全部完成！"
    recent_done_md = (
        "\n".join(f"- [x] {t}" for t in done_tasks[-8:])
        if done_tasks
        else "- 刚刚起步（0 基础破冰阶段）"
    )
    course_mod = _load_course_engine()
    learn_md = (
        "\n".join(f"- {line.strip()}" for line in course_mod.summary_lines())
        if course_mod is not None
        else "- 暂无（运行 `python3 study.py learn status` 查看）"
    )
    today_iso = dt.date.today().isoformat()

    brief_md = f"""# 🤝 WEB_AI_BRIEF — 网页端 AI / 跨设备实时学习交接单

> **用法**：在平板/手机/网页版 ChatGPT、Claude、Gemini、DeepSeek 新开对话时，直接关联本仓库或把本文件全文粘贴给它，即可 3 秒恢复你的全部学习上下文！  
> *最后自动刷新日期：{today_iso}（由 `python3 study.py brief` 生成）*

---

## 1. 给网页端 AI 的系统指令（System Persona）

你现在是我的 **27 届实习（主攻 LLM → AI Agent → 具身智能 VLA）专属 AI 课程导师与结对教练**。请严格遵守以下交互准则：
1. **以教会我为第一目标，拒绝翻译腔**：讲任何概念时，先用 **不超过 3 句话** 说清它解决了上一代技术的什么痛点，再用 **2×2 极小具体数值例子** 建立直觉，接着把原理、公式推导与真实代码对应关系彻底讲透；默认**不强制留作业或考核**，除非我主动说「练一下 / 盲写 / 考考我」。
2. **项目核心算法保面试可解释性**：推进 `projects/p1..p5` 简历项目核心模块（Attention、RoPE、DPO/GRPO Loss、ReAct、雅可比 IK 等）或我在 `concepts/` 盲写时，确保我能手撕并扛住 3 层追问。
3. **知晓我的三端算力配置**：本机有 `RTX 4080 Laptop 12GB`（支持 BF16 + FlashAttention-2，主力开发与中小训练/MuJoCo 仿真），备用 `Colab T4 16GB`（仅支持 FP16），远程有 `A800 80GB`（跑 vLLM、3B Agentic RL 和 7B VLA 微调）。
4. **沉淀闭环**：聊完一个知识点、一篇论文或攻克一个卡点时，按 Markdown 代码块输出精简总结，方便我同步回 `学习/`、`papers/` 或 `daily/`。

---

## 2. 我当前的实时进度快照

- **16 周主线完成度**：`{r_done} / {r_total}`
- **30 篇精选论文**：`{p_done} / {p_total}`
- **Hot100 手撕题**：`{l_done} / {l_total}`
- **最近一次打卡文件**：`daily/{latest_daily_name}`

### 📘 当前交互式学习课题（`学习/`）
{learn_md}

### 📍 当前正在攻坚的周次：{active_header}
{open_md}

### ✅ 最近已掌握/已勾选的任务（模拟面试拷问范围）
{recent_done_md}

---

## 3. 四大高频场景一键开聊指令（复制最后一行发给网页 AI）

- **场景 A（通勤/睡前推公式）**：`请结合上面我的进度，用 2x2 极简数字例子带我一步步推导【填概念，如 RoPE / DPO Loss / 阻尼最小二乘雅可比伪逆】，每推一步停下来问我一个检验问题。`
- **场景 B（上传论文 PDF 陪读）**：`我上传了论文 PDF，请按【30分钟略读三句话 / 2小时精读半页卡】模式带我读，最后输出可直接粘贴进我仓库 papers/ 目录的 Markdown 卡片。`
- **场景 C（模拟面试三层追问）**：`请扮演 27 届大模型/具身算法实习面试官，严格只从我上面「已掌握任务」或当前周内容中挑 1 个切入点提问，每次只问 1 个问题，根据我的回答连追 3 层！`
- **场景 D（讨论实验方案）**：`结合我的 4080 12GB + A800 80GB 算力，帮我评审接下来这个实验的超参、显存预算与防踩坑检查单：【填你的想法】。`
"""
    WEB_BRIEF_FILE.write_text(brief_md, encoding="utf-8")
    print(f"✨ 已更新跨设备 & 网页端 AI 交接简报: {WEB_BRIEF_FILE}")


def main() -> None:
    # Windows 控制台默认 GBK，print 中文/emoji 会 UnicodeEncodeError
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) >= 2 and sys.argv[1] == "learn":
        course_mod = _load_course_engine()
        if course_mod is None:
            sys.exit("❌ 未找到 .agents/skills/lab-teach/scripts/course.py")
        course_mod.main(sys.argv[2:] or ["status"])
        return

    parser = argparse.ArgumentParser(description="AI Lab 本地学习流 CLI 助手")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="查看整体学习进度看板")

    p_week = sub.add_parser("week", help="查看指定周次 (1-16) 的任务详情")
    p_week.add_argument("num", type=int, help="周次编号 (1-16)")

    p_today = sub.add_parser("today", help="生成今日四段式打卡文件")
    p_today.add_argument("--date", help="指定日期 YYYY-MM-DD（默认今天）")
    p_today.add_argument("--force", action="store_true", help="覆盖已有文件")

    p_dict = sub.add_parser("dict", help="在上层参考仓库按需秒搜概念/公式")
    p_dict.add_argument("keyword", help="检索关键词，如 RoPE / GRPO / 雅可比 / ReAct")
    p_dict.add_argument("--all", action="store_true", help="扩展搜索至全部 23 个目录")
    p_dict.add_argument("--limit", type=int, default=8, help="最多展示的正文命中文件数")

    p_paper = sub.add_parser("paper", help="从精读/略读模板创建论文卡片")
    p_paper.add_argument("slug", help="论文简称，如 attention / dpo / openvla")
    grp = p_paper.add_mutually_exclusive_group()
    grp.add_argument("--deep", action="store_true", help="使用 2 小时精读模板（默认）")
    grp.add_argument("--skim", action="store_true", help="使用 30 分钟三行略读卡模板")

    p_lc = sub.add_parser("lc", help="新建带本地 assert 测试的 LeetCode 脚本")
    p_lc.add_argument("slug", help="题目标识，如 001_two_sum / 146_lru_cache")

    sub.add_parser("learn", help="交互式课程与 HTML 笔记工作区（详见 study.py learn -h）")

    sub.add_parser("brief", help="生成 WEB_AI_BRIEF.md 供网页端 AI 与多设备秒级同步")

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "week": cmd_week,
        "today": cmd_today,
        "dict": cmd_dict,
        "paper": cmd_paper,
        "lc": cmd_lc,
        "brief": cmd_brief,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()

