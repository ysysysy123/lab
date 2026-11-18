#!/usr/bin/env python3
"""
study.py — 本地学习流零依赖 CLI 助手（v2 · 唯一入口 PLAN.md + 间隔复习卡）
用法：
  python3 study.py status                  # 查看 PLAN.md 进度、今日到期复习卡与「明天第一件事」
  python3 study.py review [--list]         # 间隔复习 学习/cards/*.md 中的到期复习卡（1→3→7→14→30→60天）
  python3 study.py week <0-10>             # 单独查看第 W00..W10 周的任务与三级验收卡
  python3 study.py today                   # 生成今日精简日志 daily/YYYY-MM-DD.md（只取当天 1 条任务 + 3 行日志）
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
import subprocess
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
REF_REPO_DIR = Path(os.environ.get("AUTUMN_REF_DIR", str(LAB_DIR.parent))).resolve()
PLAN_FILE = LAB_DIR / "PLAN.md"
# 保留 ROADMAP_FILE 别名以兼容 workbench.py 等外部导入
ROADMAP_FILE = PLAN_FILE if PLAN_FILE.exists() else (LAB_DIR / "archive" / "ROADMAP_16W.md")
CARDS_DIR = LAB_DIR / "学习" / "cards"
PAPERS_LIST_FILE = LAB_DIR / "papers" / "READING_LIST.md"
LC_TRACKER_FILE = LAB_DIR / "leetcode" / "hot100_tracker.md"
WEB_BRIEF_FILE = LAB_DIR / "WEB_AI_BRIEF.md"

REVIEW_INTERVALS = (1, 3, 7, 14, 30, 60)
CARD_PATTERN = re.compile(
    r"^##\s*Q:\s*(.+?)\n+A:\s*(.+?)\n+<!--\s*due:\s*(\d{4}-\d{2}-\d{2})\s*\|\s*interval:\s*(\d+)\s*-->",
    flags=re.MULTILINE | re.DOTALL,
)

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
    """解析 PLAN.md 中的 ### W00 .. ### W10 区块，返回 {week_num: (title, body)}"""
    pattern = re.compile(r"^###\s+W(\d{1,2})\s*·\s*(.+)$", flags=re.MULTILINE)
    matches = list(pattern.finditer(roadmap_text))
    weeks: dict[int, tuple[str, str]] = {}
    for idx, m in enumerate(matches):
        w_num = int(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(roadmap_text)
        block = roadmap_text[start:end].strip()
        block = re.split(r"\n---\s*\n", block)[0].strip()
        weeks[w_num] = (title, block)
    return weeks


def find_active_week(weeks: dict[int, tuple[str, str]]) -> int:
    """找到第一个还有未完成任务的周次"""
    for w in sorted(weeks):
        _, block = weeks[w]
        if re.search(r"^\s*-\s*\[\s\]\s+", block, flags=re.MULTILINE):
            return w
    return max(weeks) if weeks else 0


def bar(done: int, total: int, width: int = 24) -> str:
    if total == 0:
        return "[" + "." * width + "] 0/0"
    filled = int(round(width * done / total))
    pct = 100.0 * done / total
    return f"[{'█' * filled}{'░' * (width - filled)}] {done}/{total} ({pct:.0f}%)"


def load_all_cards() -> list[dict]:
    """扫描 学习/cards/*.md，返回卡片列表"""
    if not CARDS_DIR.exists():
        return []
    cards: list[dict] = []
    for path in sorted(CARDS_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        for m in CARD_PATTERN.finditer(text):
            q = m.group(1).strip()
            a = m.group(2).strip()
            due_str = m.group(3)
            interval = int(m.group(4))
            try:
                due_date = dt.date.fromisoformat(due_str)
            except ValueError:
                due_date = dt.date.today()
            cards.append(
                {
                    "path": path,
                    "q": q,
                    "a": a,
                    "due": due_date,
                    "interval": interval,
                    "span": m.span(),
                }
            )
    return cards


def next_review_interval(cur_interval: int, passed: bool) -> int:
    if not passed:
        return 1
    for iv in REVIEW_INTERVALS:
        if iv > cur_interval:
            return iv
    return REVIEW_INTERVALS[-1]


def update_card_in_file(card: dict, new_due: dt.date, new_interval: int) -> None:
    path: Path = card["path"]
    text = path.read_text(encoding="utf-8")
    old_block = text[card["span"][0] : card["span"][1]]
    new_block = re.sub(
        r"<!--\s*due:\s*\d{4}-\d{2}-\d{2}\s*\|\s*interval:\s*\d+\s*-->",
        f"<!-- due: {new_due.isoformat()} | interval: {new_interval} -->",
        old_block,
    )
    updated = text[: card["span"][0]] + new_block + text[card["span"][1] :]
    path.write_text(updated, encoding="utf-8")


def latest_tomorrow_cue() -> tuple[str, str] | None:
    """读取最近一次 daily 日志中的「下次从这里开始」提示，返回 (date_str, text)"""
    daily_dir = LAB_DIR / "daily"
    if not daily_dir.exists():
        return None
    for path in sorted(daily_dir.glob("????-??-??.md"), reverse=True):
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^###\s*下次从这里开始.*?\n(.*?)(?=\n### |\n<!-- |\Z)", text, flags=re.S | re.M)
        if m and m.group(1).strip():
            return path.stem, m.group(1).strip()
    return None


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

    today = dt.date.today()
    cards = load_all_cards()
    due_cards = [c for c in cards if c["due"] <= today]

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
    print("🚀 AI Lab 学习总控台 v2（唯一入口: PLAN.md）")
    print("=" * 64)
    print(f"  10周主线计划 : {bar(r_done, r_total)}")
    print(f"  间隔复习卡片 : 到期 {len(due_cards)} / 总计 {len(cards)} 张  (运行 `python3 study.py review`)")
    print(f"  精选论文清单 : {bar(p_done, p_total)}  (已写卡片: {len(paper_notes)} 篇)")
    print(f"  Hot100 刷题  : {bar(l_done, l_total)}")
    print(f"  每日打卡累计 : {len(daily_logs)} 天  |  盲写微实验: {len(concept_scripts)} 个")

    cue = latest_tomorrow_cue()
    if cue:
        print("-" * 64)
        print(f"🧭 上次留下的「今天第一件事」({cue[0]}): {cue[1]}")

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
            if open_tasks:
                print(f"   👉 今日主块任务: {open_tasks[0]}")
                for item in open_tasks[1:3]:
                    print(f"      后续待办: {item}")
                if len(open_tasks) > 3:
                    print(f"      ... 其余 {len(open_tasks) - 3} 项用 `python3 study.py week {active_w}` 查看")
    course_mod = _load_course_engine()
    if course_mod is not None:
        print("-" * 64)
        print("📘 交互式课程工作区 (学习/ · lab-teach):")
        for line in course_mod.summary_lines():
            print(f"  {line}")
    print("=" * 64)


def cmd_review(args: argparse.Namespace) -> None:
    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    cards = load_all_cards()
    due_cards = [c for c in cards if c["due"] <= today]

    if not cards:
        print(f"ℹ️ 尚未发现复习卡。请在 {CARDS_DIR} 下创建 Markdown 复习卡。")
        return

    if not due_cards:
        next_due = min(c["due"] for c in cards)
        print(f"🎉 今日（{today.isoformat()}）没有到期复习卡！共 {len(cards)} 张卡，最近到期日：{next_due.isoformat()}")
        return

    if args.list or not sys.stdin.isatty():
        print(f"🧠 今日到期复习卡（共 {len(due_cards)} / {len(cards)} 张，日期 ≤ {today.isoformat()}）：")
        print("-" * 64)
        for idx, c in enumerate(due_cards, start=1):
            rel = c["path"].relative_to(LAB_DIR)
            print(f"[{idx}] ({rel} · 当前间隔 {c['interval']}d)")
            print(f"  Q: {c['q']}")
            if args.show_answer:
                print(f"  A: {c['a']}")
        print("-" * 64)
        print("💡 在终端直接运行 `python3 study.py review` 进行交互式自测，或用 `--grade <序号> <y|n>` 更新单张卡片。")
        return

    if args.grade:
        idx_str, verdict = args.grade
        idx = int(idx_str)
        if idx < 1 or idx > len(due_cards):
            sys.exit(f"❌ 序号超出范围 (1..{len(due_cards)})")
        c = due_cards[idx - 1]
        passed = verdict.lower() in ("y", "yes", "pass", "1", "true")
        new_iv = next_review_interval(c["interval"], passed)
        new_due = today + dt.timedelta(days=new_iv)
        update_card_in_file(c, new_due, new_iv)
        status_str = f"✅ 记住！下次复习: {new_due.isoformat()} (间隔 {new_iv} 天)" if passed else f"🔄 需巩固！已重置为明天复习 ({new_due.isoformat()})，建议用自己的话改写 A:"
        print(f"[{idx}] {c['q']}\n{status_str}")
        return

    print("=" * 64)
    print(f"🧠 间隔复习自测（今日到期 {len(due_cards)} 张 · 间隔阶梯 1→3→7→14→30→60 天）")
    print("   先在心里或纸上作答，按 Enter 看答案；输入 y(答对) / n(答错重排) / q(退出)")
    print("=" * 64)

    for idx, c in enumerate(due_cards, start=1):
        # 重新加载以保证同一文件多张卡片偏移量准确
        fresh_due = [fc for fc in load_all_cards() if fc["path"] == c["path"] and fc["q"] == c["q"]]
        if not fresh_due:
            continue
        target_card = fresh_due[0]
        rel = target_card["path"].relative_to(LAB_DIR)
        print(f"\n[{idx}/{len(due_cards)}] ({rel} · 当前间隔 {target_card['interval']}d)")
        print(f"❓ Q: {target_card['q']}")
        try:
            input("   [按 Enter 显示答案] ")
        except EOFError:
            break
        print(f"💡 A: {target_card['a']}")
        while True:
            try:
                ans = input("   答对了吗？[y=记住推进 / n=卡壳重置为1天 / q=退出]: ").strip().lower()
            except EOFError:
                ans = "q"
            if ans in ("y", "yes", ""):
                new_iv = next_review_interval(target_card["interval"], True)
                new_due = today + dt.timedelta(days=new_iv)
                update_card_in_file(target_card, new_due, new_iv)
                print(f"   ✅ 下次复习: {new_due.isoformat()} (间隔 {new_iv} 天)")
                break
            if ans in ("n", "no"):
                new_iv = 1
                new_due = today + dt.timedelta(days=1)
                update_card_in_file(target_card, new_due, new_iv)
                print(f"   🔄 已重置为明天 ({new_due.isoformat()})，记得顺手把 A: 改成更好记的话！")
                break
            if ans == "q":
                print("👋 已保存当前复习进度。")
                return


def cmd_week(args: argparse.Namespace) -> None:
    if not ROADMAP_FILE.exists():
        sys.exit(f"未找到 {ROADMAP_FILE}")
    weeks = parse_weeks(ROADMAP_FILE.read_text(encoding="utf-8"))
    w = args.num
    if w not in weeks:
        lo, hi = min(weeks, default=0), max(weeks, default=10)
        sys.exit(f"周次 {w} 不在 {lo}..{hi} 范围内")
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

    active_header = "W00"
    first_task = "推进 PLAN.md 当前周下一条任务"
    task_id = "week:0:0"
    if ROADMAP_FILE.exists():
        roadmap_txt = ROADMAP_FILE.read_text(encoding="utf-8")
        weeks = parse_weeks(roadmap_txt)
        active_w = find_active_week(weeks)
        if active_w in weeks:
            title, block = weeks[active_w]
            active_header = f"W{active_w:02d} · {title}"
            all_tasks = re.findall(r"^\s*-\s*\[([ xX])\]\s+(.+)$", block, flags=re.MULTILINE)
            for idx, (state_ch, t_text) in enumerate(all_tasks):
                if state_ch.strip() == "":
                    first_task = t_text.strip()
                    task_id = f"week:{active_w}:{idx}"
                    break

    cue = latest_tomorrow_cue()
    cue_note = f"\n> 🧭 接上次（{cue[0]}）留下的第一件事：{cue[1]}\n" if cue else ""

    content = f"""# {today_str} 学习日志（{active_header}）
{cue_note}
<!-- ai-lab:today -->
## 今日工作台
状态：未打卡
投入分钟：

### 今日任务
- [ ] {first_task} <!-- task:{task_id} -->

### 今日收获


### 卡住的问题


### 下次从这里开始

<!-- /ai-lab:today -->
"""
    target.write_text(content, encoding="utf-8")
    print(f"✨ 已生成今日极简日志: {target}")
    print(f"   👉 今日唯一主块: {first_task}")


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
        print("   👉 你可以直接让当前 AI 按 AGENTS.md 为你推导，或设置环境变量 AUTUMN_REF_DIR=/path/to/autumn-recruitment。")
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
    cards = load_all_cards()
    due_cards = [c for c in cards if c["due"] <= dt.date.today()]

    active_header = "W00"
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
> *最后自动刷新日期：{today_iso}（由 `python3 study.py brief` 生成，唯一进度源：`PLAN.md`）*

---

## 1. 给网页端 AI 的系统指令（System Persona）

你现在是我的 **27 届实习（主攻 LLM → AI Agent，少量接触具身智能）专属 AI 课程导师与结对教练**。请严格遵守以下交互准则：
1. **讲课时减负，模块结束必做三级验收**：讲新概念时，先用 **不超过 3 句话** 说清痛点，再用 **2×2 极小具体数值例子** 建立直觉，接着讲透公式与真实代码对应关系；每个核心模块学完后，按 **L1 讲得出 / L2 写得出 / L3 扛得住（含预测题）** 帮我验收，不再只看不练。
2. **项目核心算法保面试可解释性**：推进 `projects/p1..p5` 简历项目核心模块（Attention、RoPE、LoRA/QLoRA、DPO/GRPO、ReAct、RRF 等）或我在 `concepts/` 盲写时，确保我能手撕并扛住 3 层追问。
3. **知晓我的三端算力配置**：本机有 `RTX 4080 Laptop 12GB`（支持 BF16 + FlashAttention-2，主力开发与中小训练/MuJoCo 仿真），备用 `Colab T4 16GB`（仅支持 FP16），远程有 `A800 80GB`。
4. **沉淀闭环**：每个模块结束提醒我用自己的话写 3–5 张复习卡存入 `学习/cards/`，并在 `daily/` 留下一句「下次从这里开始（明天第一件事）」。

---

## 2. 我当前的实时进度快照

- **10 周主线完成度（`PLAN.md`）**：`{r_done} / {r_total}`
- **间隔复习卡片（`学习/cards/`）**：今日到期 `{len(due_cards)} / {len(cards)}` 张
- **精选论文清单**：`{p_done} / {p_total}`
- **Hot100 手撕题**：`{l_done} / {l_total}`
- **最近一次打卡文件**：`daily/{latest_daily_name}`

### 📘 当前交互式学习课题（`学习/`）
{learn_md}

### 📍 当前正在攻坚的周次：{active_header}
{open_md}

### ✅ 最近已掌握/已勾选的任务（验收与模拟面试范围）
{recent_done_md}

---

## 3. 四大高频场景一键开聊指令（复制最后一行发给网页 AI）

- **场景 A（模块三级验收）**：`请针对我刚学完的【填模块名】，依次考我 L1 口述直觉与 Shape、L2 盲写核心代码、L3 预测题（先问我改某个超参/设计会怎样）。`
- **场景 B（上传论文 PDF 陪读）**：`我上传了论文 PDF，请按【30分钟略读三句话 / 2小时精读半页卡】模式带我读，最后输出可直接粘贴进我仓库 papers/ 目录的 Markdown 卡片。`
- **场景 C（模拟面试三层追问）**：`请扮演 27 届大模型/Agent 算法实习面试官，严格只从我上面「已掌握任务」中挑 1 个切入点提问，每次只问 1 个问题，根据我的回答连追 3 层！`
- **场景 D（批改复习卡）**：`这是我用自己的话写的几张复习卡，请帮我检查有没有概念错误或遗漏的边界条件：【粘贴 Q/A】。`
"""
    WEB_BRIEF_FILE.write_text(brief_md, encoding="utf-8")
    print(f"✨ 已更新跨设备 & 网页端 AI 交接简报: {WEB_BRIEF_FILE}")


def git_sync_info() -> dict:
    """获取当前 Git 最新提交与未提交变更状态"""
    try:
        head = subprocess.run(
            ["git", "log", "-1", "--format=%h · %s (%cr)"],
            cwd=str(LAB_DIR),
            capture_output=True,
            text=True,
            timeout=3,
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(LAB_DIR),
            capture_output=True,
            text=True,
            timeout=3,
        )
        return {
            "head": head.stdout.strip() if head.returncode == 0 else "未知",
            "dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else False,
        }
    except Exception:
        return {"head": "未知", "dirty": False}


def sync_repo(reason: str = "chore(study): auto sync progress") -> dict:
    """刷新 brief & index，自动 git add + commit + push 到 origin main"""
    try:
        course_mod = _load_course_engine()
        if course_mod is not None:
            course_mod.build_index(quiet=True)
        cmd_brief(argparse.Namespace())
    except Exception:
        pass

    try:
        subprocess.run(["git", "add", "-A"], cwd=str(LAB_DIR), check=False, timeout=5)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(LAB_DIR),
            capture_output=True,
            text=True,
            timeout=5,
        )
        committed = False
        if status.stdout.strip():
            c_res = subprocess.run(
                ["git", "commit", "-m", reason],
                cwd=str(LAB_DIR),
                capture_output=True,
                text=True,
                timeout=10,
            )
            committed = c_res.returncode == 0

        p_res = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(LAB_DIR),
            capture_output=True,
            text=True,
            timeout=20,
        )
        pushed = p_res.returncode == 0
        info = git_sync_info()
        return {
            "ok": pushed,
            "committed": committed,
            "pushed": pushed,
            "head": info["head"],
            "dirty": info["dirty"],
            "error": "" if pushed else (p_res.stderr.strip() or "git push 失败"),
        }
    except Exception as exc:
        info = git_sync_info()
        return {
            "ok": False,
            "committed": False,
            "pushed": False,
            "head": info["head"],
            "dirty": info["dirty"],
            "error": str(exc),
        }


def cmd_sync(args: argparse.Namespace) -> None:
    msg = getattr(args, "message", None) or f"chore(study): sync {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    res = sync_repo(msg)
    if res["ok"]:
        print(f"🟢 已自动同步至远程 GitHub (origin/main)！最新提交: {res['head']}")
    else:
        print(f"⚠️ 本地已提交 ({res['head']})，但远程推送遇到问题: {res['error']}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) >= 2 and sys.argv[1] == "learn":
        course_mod = _load_course_engine()
        if course_mod is None:
            sys.exit("❌ 未找到 .agents/skills/lab-teach/scripts/course.py")
        course_mod.main(sys.argv[2:] or ["status"])
        return

    parser = argparse.ArgumentParser(description="AI Lab 本地学习流 CLI 助手 v2")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="查看整体学习进度看板与今日第一件事")

    p_review = sub.add_parser("review", help="间隔复习 学习/cards/*.md 中的到期卡片")
    p_review.add_argument("--list", action="store_true", help="仅列出今日到期卡片（非交互）")
    p_review.add_argument("--show-answer", action="store_true", help="--list 模式下同时显示答案")
    p_review.add_argument("--grade", nargs=2, metavar=("INDEX", "Y_OR_N"), help="非交互标记第 INDEX 张到期卡 (y/n)")
    p_review.add_argument("--date", help="指定基准日期 YYYY-MM-DD（默认今天）")

    p_week = sub.add_parser("week", help="查看指定周次 (0-10) 的任务与验收标准")
    p_week.add_argument("num", type=int, help="周次编号 (0-10)")

    p_today = sub.add_parser("today", help="生成今日极简打卡日志")
    p_today.add_argument("--date", help="指定日期 YYYY-MM-DD（默认今天）")
    p_today.add_argument("--force", action="store_true", help="覆盖已有文件")

    p_dict = sub.add_parser("dict", help="在上层参考仓库按需秒搜概念/公式")
    p_dict.add_argument("keyword", help="检索关键词，如 RoPE / GRPO / 雅可比 / ReAct")
    p_dict.add_argument("--all", action="store_true", help="扩展搜索至全部 23 个目录")
    p_dict.add_argument("--limit", type=int, default=8, help="最多展示的正文命中文件数")

    p_paper = sub.add_parser("paper", help="从精读/略读模板创建论文卡片")
    p_paper.add_argument("slug", help="论文简称，如 attention / dpo / lora")
    grp = p_paper.add_mutually_exclusive_group()
    grp.add_argument("--deep", action="store_true", help="使用 2 小时精读模板（默认）")
    grp.add_argument("--skim", action="store_true", help="使用 30 分钟三行略读卡模板")

    p_lc = sub.add_parser("lc", help="新建带本地 assert 测试的 LeetCode 脚本")
    p_lc.add_argument("slug", help="题目标识，如 001_two_sum / 146_lru_cache")

    sub.add_parser("learn", help="交互式课程与 HTML 笔记工作区（详见 study.py learn -h）")

    sub.add_parser("brief", help="生成 WEB_AI_BRIEF.md 供网页端 AI 与多设备秒级同步")

    p_sync = sub.add_parser("sync", help="一键刷新 brief/index 并自动 git commit & push 到远程 GitHub")
    p_sync.add_argument("-m", "--message", help="自定义提交信息")

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "review": cmd_review,
        "week": cmd_week,
        "today": cmd_today,
        "dict": cmd_dict,
        "paper": cmd_paper,
        "lc": cmd_lc,
        "brief": cmd_brief,
        "sync": cmd_sync,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
