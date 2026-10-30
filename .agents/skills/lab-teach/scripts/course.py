#!/usr/bin/env python3
"""
course.py — lab-teach 学习工作区引擎（纯标准库，Python 3.10+，任何设备可跑）

推荐入口：python3 study.py learn <子命令> ...（等价于直接运行本文件）

状态与上下文
  status                          所有课题进度 / 下一课 / 待复习（"继续" 先跑它）
  context <topic>                 教下一课前需要的全部上下文（Mission/偏好/计划/课程/学习记录/术语）
读课程与代码
  nb <ipynb> [--outline|--cells 3-7|--grep 关键词|--export out.py --cells 7,9]
  snippet <file|ipynb> [--lines a-b] [--cell N] [--for lesson.html]   输出可直接粘贴的 <pre> 代码块
脚手架
  new-topic <slug> --title T --goal G [--roadmap R] [--sources S] [--step "第一课" ...]
  new-lesson <topic> <slug> --title T [--step N]
  new-ref <slug> --title T
  record <slug> --title T --body B [--evidence E] [--implications I]
进度
  done <topic> <step>             勾选计划步骤并记日期（ROADMAP 仍需在课题完成时手动勾选）
  reviewed <topic> --what "第 1–2 课"
  index                           重建 学习/index.md + index.html + 各课上一课/下一课导航
正确性
  golden <lesson.html> <verify.py>   运行验证脚本（打印 JSON）并注入课程页金标准
  check [html ...] [--browser]       静态检查 + 无头浏览器跑 JS 校验
  shot <html> [--out png]            无头浏览器截图（AI 自检排版用）
其他
  open <path>    py（打印用于跑实验的 Python 解释器）
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
LAB_DIR = SKILL_DIR.parents[2]
LEARN_DIR = LAB_DIR / "学习"
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATES_DIR = SKILL_DIR / "templates"
REF_DIR = Path(os.environ.get("AUTUMN_REF_DIR", str(LAB_DIR.parent))).resolve()
ROADMAP_FILE = LAB_DIR / "ROADMAP_16W.md"
RECORDS_DIR = LEARN_DIR / "learning-records"
REFS_DIR = LEARN_DIR / "reference"
PLAN_NAME = "计划.md"
REVIEW_INTERVALS = (1, 3, 7, 21)  # 间隔复习建议（天）
TODAY = dt.date.today()

STEP_RE = re.compile(r"^-\s*\[( |x|X)\]\s*(\d+)\.\s*(.+?)\s*$")
DATE_RE = re.compile(r"✓\s*(\d{4}-\d{2}-\d{2})")
FIELD_RE = re.compile(r"^(目标|关联|来源|状态|截止)\s*[:：]\s*(.*)$")


# ============================================================ 解析工作区状态
def rel(p: Path, start: Path) -> str:
    return Path(os.path.relpath(p, start)).as_posix()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def parse_date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def html_title(p: Path) -> str:
    m = re.search(r"<title>(.*?)</title>", read(p), flags=re.S)
    t = html.unescape(m.group(1).strip()) if m else p.stem
    return t.split(" · ")[0]


def html_meta(p: Path, name: str) -> str:
    m = re.search(rf'<meta name="lab:{name}" content="([^"]*)"', read(p))
    return m.group(1) if m else ""


class Topic:
    def __init__(self, d: Path):
        self.dir = d
        self.slug = d.name
        self.plan_path = d / PLAN_NAME
        text = read(self.plan_path)
        self.text = text
        self.title = self.slug
        self.fields: dict[str, str] = {}
        self.steps: list[dict] = []
        self.reviews: list[dt.date] = []
        section = ""
        for line in text.splitlines():
            if line.startswith("# ") and self.title == self.slug:
                self.title = line[2:].strip()
                continue
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            fm = FIELD_RE.match(line.strip())
            if fm and not section:
                self.fields[fm.group(1)] = fm.group(2).strip()
                continue
            sm = STEP_RE.match(line.strip())
            if sm:
                body = sm.group(3)
                parts = re.split(r"\s+—\s+", body, maxsplit=1)
                title = re.sub(r"\s*(?:→\s*\[.*?\]\(.*?\)|✓\s*\d{4}-\d{2}-\d{2}).*$", "", parts[0]).strip()
                rest = parts[1] if len(parts) > 1 else ""
                mastery = ""
                mm = re.search(r"(?:掌握标志|检验)\s*[:：]\s*(.+?)(?:\s+→|\s+✓|$)", rest)
                if mm:
                    mastery = mm.group(1).strip()
                link = re.search(r"\]\((lessons/[^)]+)\)", body)
                dm = DATE_RE.search(body)
                self.steps.append({
                    "n": int(sm.group(2)), "done": sm.group(1) in "xX", "title": title,
                    "mastery": mastery, "lesson": link.group(1) if link else "",
                    "date": parse_date(dm.group(1)) if dm else None,
                })
                continue
            if section.startswith("复习"):
                rm = re.match(r"^-\s*(\d{4}-\d{2}-\d{2})", line.strip())
                if rm and parse_date(rm.group(1)):
                    self.reviews.append(parse_date(rm.group(1)))

    @property
    def goal(self) -> str:
        return self.fields.get("目标", "")

    @property
    def status(self) -> str:
        s = self.fields.get("状态", "")
        if s:
            return s
        return "已完成" if self.steps and all(x["done"] for x in self.steps) else "进行中"

    @property
    def lessons(self) -> list[Path]:
        return sorted((self.dir / "lessons").glob("[0-9][0-9][0-9][0-9]-*.html"))

    @property
    def progress(self) -> tuple[int, int]:
        return sum(s["done"] for s in self.steps), len(self.steps)

    @property
    def next_step(self) -> dict | None:
        return next((s for s in self.steps if not s["done"]), None)

    @property
    def last_date(self) -> dt.date | None:
        ds = [s["date"] for s in self.steps if s["date"]] + self.reviews
        for p in self.lessons:
            d = parse_date(html_meta(p, "date"))
            if d:
                ds.append(d)
        legacy = re.search(r"最后学习\D*(\d{4}-\d{2}-\d{2})", self.text)
        if legacy and parse_date(legacy.group(1)):
            ds.append(parse_date(legacy.group(1)))
        return max(ds) if ds else None

    def review_due(self) -> dt.date | None:
        done_dates = [s["date"] for s in self.steps if s["done"] and s["date"]]
        if not done_dates:
            return None
        first = min(done_dates)
        later = sorted(r for r in self.reviews if r >= first)
        k = min(len(later), len(REVIEW_INTERVALS) - 1)
        base = later[-1] if later else max(done_dates)
        return base + dt.timedelta(days=REVIEW_INTERVALS[k])


def topics() -> list[Topic]:
    if not LEARN_DIR.exists():
        return []
    out = [Topic(d) for d in sorted(LEARN_DIR.iterdir()) if d.is_dir() and (d / PLAN_NAME).exists()]
    return out


def find_topic(q: str) -> Topic:
    ts = topics()
    for t in ts:
        if t.slug == q:
            return t
    hits = [t for t in ts if q.lower() in t.slug.lower() or q in t.title]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"❌ 找不到课题「{q}」。现有：{', '.join(t.slug for t in ts) or '（无）'}；新建用 new-topic")
    sys.exit(f"❌ 「{q}」匹配到多个课题：{', '.join(t.slug for t in hits)}")


def current_topic() -> Topic | None:
    active = [t for t in topics() if t.status not in ("已完成", "暂停")]
    if not active:
        return None
    return max(active, key=lambda t: (t.last_date or dt.date.min, t.slug))


def records() -> list[tuple[Path, str, str]]:
    out = []
    for p in sorted(RECORDS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")):
        lines = [l for l in read(p).splitlines() if l.strip() and not l.startswith("---") and not re.match(r"^\w+:\s", l)]
        title = lines[0].lstrip("# ").strip() if lines else p.stem
        body = lines[1].strip() if len(lines) > 1 else ""
        out.append((p, title, body))
    return out


def roadmap_progress() -> tuple[int, int]:
    text = read(ROADMAP_FILE)
    done = len(re.findall(r"^\s*-\s*\[[xX]\]\s+", text, flags=re.M))
    todo = len(re.findall(r"^\s*-\s*\[\s\]\s+", text, flags=re.M))
    return done, done + todo


def summary_lines() -> list[str]:
    """供 study.py status / brief 复用的简短摘要（避免两处各写一套解析）"""
    ts = topics()
    if not ts:
        return ["学习课题：暂无（说「开始学习 XX」创建）"]
    lines = []
    cur = current_topic()
    for t in ts:
        d, n = t.progress
        nxt = t.next_step
        mark = "👉 " if cur and t.slug == cur.slug else "   "
        lines.append(f"{mark}{t.slug} [{t.status}] {d}/{n} 课" + (f" → 下一课: {nxt['n']}. {nxt['title']}" if nxt else ""))
    due = [t for t in ts if t.review_due() and t.review_due() <= TODAY]
    if due:
        lines.append("⏰ 建议复习：" + "、".join(t.slug for t in due))
    return lines


# ============================================================ status / context
def cmd_status(_a) -> None:
    ts = topics()
    rd, rt = roadmap_progress()
    print("=" * 66)
    print(f"📚 lab-teach 学习工作区   ROADMAP {rd}/{rt}   学习记录 {len(records())} 条")
    print("=" * 66)
    if not ts:
        print("暂无课题。对 AI 说「开始学习 XX」，或运行 new-topic。")
        return
    cur = current_topic()
    for t in ts:
        d, n = t.progress
        flag = "👉" if cur and t.slug == cur.slug else "  "
        print(f"{flag} {t.slug}  [{t.status}]  {d}/{n} 课  最近: {t.last_date or '-'}  课程页: {len(t.lessons)}")
        if t.goal:
            print(f"     目标: {t.goal}")
        nxt = t.next_step
        if nxt:
            print(f"     下一课: {nxt['n']}. {nxt['title']}" + (f"（掌握标志: {nxt['mastery']}）" if nxt["mastery"] else ""))
        due = t.review_due()
        if due:
            print(f"     复习建议: {'⏰ 今天/已到期' if due <= TODAY else due.isoformat()}")
    print("-" * 66)
    print("提示：说「继续」= 当前👉课题的下一课；「复习」= 到期课题的回顾卡。")


def cmd_context(a) -> None:
    t = find_topic(a.topic)
    sec = lambda s: print(f"\n{'=' * 20} {s} {'=' * 20}")
    for name in ("MISSION.md", "NOTES.md"):
        p = LEARN_DIR / name
        if p.exists():
            sec(name)
            print(read(p).strip())
    sec(f"计划 {rel(t.plan_path, LAB_DIR)}")
    print(t.text.strip())
    sec("已有课程页")
    for p in t.lessons:
        print(f"  {rel(p, LAB_DIR)}  ←  {html_title(p)}  (step {html_meta(p, 'step') or '?'})")
    if not t.lessons:
        print("  （无）")
    src = t.fields.get("来源", "")
    if src:
        sec("来源文件存在性")
        for token in re.findall(r"[\w./\-\u4e00-\u9fff]+\.(?:ipynb|py|md)", src):
            cands = [LAB_DIR / token, REF_DIR / token.removeprefix("../")]
            ok = next((c for c in cands if c.exists()), None)
            print(f"  {'✓' if ok else '✗'} {token}" + ("" if ok else "（本设备不存在：改用 Lab 代码或直接推导）"))
    sec("学习记录（ZPD 依据）")
    for p, title, body in records():
        print(f"  {p.stem}: {title} — {body[:80]}")
    if not records():
        print("  （无）")
    g = LEARN_DIR / "GLOSSARY.md"
    if g.exists():
        sec("术语表（讲课必须沿用）")
        print("  " + "、".join(re.findall(r"^\*\*(.+?)\*\*", read(g), flags=re.M)))
    rd, rt = roadmap_progress()
    sec("ROADMAP")
    print(f"  {rd}/{rt}；本课题关联：{t.fields.get('关联', '-')}")


# ============================================================ 读 Notebook / 代码
def load_nb(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("cells", [])


def cell_src(c: dict) -> str:
    s = c.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def parse_ranges(spec: str) -> list[int]:
    out: list[int] = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def resolve_path(s: str) -> Path:
    p = Path(s)
    for c in (p, LAB_DIR / s, REF_DIR / s.removeprefix("../")):
        if c.exists():
            return c.resolve()
    sys.exit(f"❌ 文件不存在：{s}")


def display_path(p: Path) -> str:
    try:
        return rel(p, LAB_DIR) if p.is_relative_to(LAB_DIR) else "../" + rel(p, REF_DIR)
    except ValueError:
        return str(p)


def cmd_nb(a) -> None:
    path = resolve_path(a.path)
    cells = load_nb(path)
    if a.export:
        idx = parse_ranges(a.cells) if a.cells else [i for i, c in enumerate(cells, 1) if c.get("cell_type") == "code"]
        code = [f"# ---- {display_path(path)} Cell#{i} ----\n" + cell_src(cells[i - 1]) for i in idx if cells[i - 1].get("cell_type") == "code"]
        Path(a.export).write_text("\n\n".join(code) + "\n", encoding="utf-8")
        print(f"✨ 导出 {len(code)} 个代码单元 → {a.export}（Cell 编号从 1 开始，与 study.py dict 一致）")
        return
    if a.cells:
        for i in parse_ranges(a.cells):
            if 1 <= i <= len(cells):
                c = cells[i - 1]
                print(f"\n────── Cell#{i} [{c.get('cell_type')}] ──────")
                print(cell_src(c))
        return
    if a.grep:
        pat = re.compile(re.escape(a.grep), re.I)
        for i, c in enumerate(cells, 1):
            src = cell_src(c)
            hits = [l.strip() for l in src.splitlines() if pat.search(l)]
            if hits:
                print(f"Cell#{i} [{c.get('cell_type')}] {hits[0][:100]}" + (f"  (+{len(hits) - 1})" if len(hits) > 1 else ""))
        return
    print(f"📓 {display_path(path)} — {len(cells)} cells（Cell 编号从 1 开始）")
    for i, c in enumerate(cells, 1):
        src = cell_src(c)
        kind = c.get("cell_type", "?")
        if kind == "markdown":
            heads = [l for l in src.splitlines() if l.startswith("#")]
            first = heads[0] if heads else (src.strip().splitlines() or [""])[0]
            print(f"  {i:>3} md   {first[:90]}")
        else:
            first = next((l for l in src.splitlines() if l.strip() and not l.strip().startswith("# ----")), "")
            print(f"  {i:>3} code {len(src.splitlines()):>3} 行  {first.strip()[:80]}")


def cmd_snippet(a) -> None:
    path = resolve_path(a.path)
    disp = display_path(path)
    start = 1
    if path.suffix == ".ipynb":
        if not a.cell:
            sys.exit("❌ Notebook 需要 --cell N")
        lines = cell_src(load_nb(path)[a.cell - 1]).splitlines()
        disp += f" · Cell#{a.cell}"
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
    if a.lines:
        lo, _, hi = a.lines.partition("-")
        lo_i, hi_i = int(lo), int(hi or lo)
        lines = lines[lo_i - 1: hi_i]
        start = lo_i
    lang = a.lang or {".py": "python", ".sh": "bash", ".js": "javascript", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown"}.get(path.suffix, "python")
    href = ""
    if a.for_lesson and path.suffix != ".ipynb":
        href = f' data-href="{html.escape(rel(path, Path(a.for_lesson).resolve().parent))}"'
    code = html.escape("\n".join(lines), quote=False)
    print(f'<pre data-file="{html.escape(disp)}" data-start="{start}"{href}><code class="language-{lang}">{code}</code></pre>')


# ============================================================ 脚手架
def slugify(s: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", s.strip()).strip("-")
    return s or "untitled"


def fill(tpl: str, mapping: dict[str, str]) -> str:
    for k, v in mapping.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def cmd_new_topic(a) -> None:
    slug = slugify(a.slug)
    d = LEARN_DIR / slug
    plan = d / PLAN_NAME
    if plan.exists():
        print(f"✅ 课题已存在：{rel(plan, LAB_DIR)}")
        return
    d.mkdir(parents=True, exist_ok=True)
    tpl = read(TEMPLATES_DIR / "plan.md")
    steps = a.step or ["（待规划）"]
    tpl = fill(tpl, {"TITLE": a.title or slug, "GOAL": a.goal or "", "ROADMAP": a.roadmap or "-", "SOURCES": a.sources or "-", "STEP1": steps[0]})
    extra = "".join(f"- [ ] {i}. {s} — 掌握标志: \n" for i, s in enumerate(steps[1:], start=2))
    tpl = tpl.replace("— 掌握标志: （可观察的能力，非强制考核）\n", "— 掌握标志: （可观察的能力，非强制考核）\n" + extra, 1)
    plan.write_text(tpl, encoding="utf-8")
    print(f"✨ 新课题：{rel(plan, LAB_DIR)}（请补全依赖图与掌握标志）")
    build_index(quiet=True)


def lesson_mapping(target: Path, title: str, topic: Topic | None, num: int, step: str) -> dict[str, str]:
    home = LEARN_DIR / "index.html"
    m = {
        "TITLE": title, "DATE": TODAY.isoformat(), "NUM": str(num), "STEP": step or "-",
        "ASSETS": rel(ASSETS_DIR, target.parent), "HOME": rel(home, target.parent),
    }
    if topic:
        m.update({"TOPIC": topic.slug, "TOPIC_TITLE": topic.title, "PLAN": rel(home, target.parent) + "#" + topic.slug})
    return m


def cmd_new_lesson(a) -> None:
    t = find_topic(a.topic)
    if a.step and not a.force:
        ex = next((s for s in t.steps if s["n"] == a.step and s["lesson"] and (t.dir / s["lesson"]).exists()), None)
        if ex:
            print(f"✅ 步骤 {a.step} 已有课程页：{rel(t.dir / ex['lesson'], LAB_DIR)}（直接更新该文件，或加 --force 另建）")
            return
    ld = t.dir / "lessons"
    ld.mkdir(parents=True, exist_ok=True)
    nums = [int(p.name[:4]) for p in t.lessons]
    num = max(nums, default=0) + 1
    target = ld / f"{num:04d}-{slugify(a.slug)}.html"
    step = str(a.step) if a.step else ""
    target.write_text(fill(read(TEMPLATES_DIR / "lesson.html"), lesson_mapping(target, a.title, t, num, step)), encoding="utf-8")
    if a.step:
        link_step(t, a.step, rel(target, t.dir))
    build_index(quiet=True)
    print(f"✨ 新课程页：{rel(target, LAB_DIR)}")
    print("   下一步：填写 TODO-LESSON → golden 注入金标准 → check --browser → open")


def link_step(t: Topic, n: int, lesson_rel: str) -> None:
    lines = t.text.splitlines()
    for i, line in enumerate(lines):
        m = STEP_RE.match(line.strip())
        if m and int(m.group(2)) == n and lesson_rel not in line:
            lines[i] = line.rstrip() + f" → [课程页]({lesson_rel})"
            t.plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return


def cmd_new_ref(a) -> None:
    REFS_DIR.mkdir(parents=True, exist_ok=True)
    target = REFS_DIR / f"{slugify(a.slug)}.html"
    if target.exists():
        print(f"✅ 速查表已存在：{rel(target, LAB_DIR)}（直接更新它，别新建重复的）")
        return
    target.write_text(fill(read(TEMPLATES_DIR / "reference.html"), lesson_mapping(target, a.title, None, 0, "")), encoding="utf-8")
    build_index(quiet=True)
    print(f"✨ 新速查表：{rel(target, LAB_DIR)}")


def cmd_record(a) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    nums = [int(p.name[:4]) for p in RECORDS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")]
    num = max(nums, default=0) + 1
    p = RECORDS_DIR / f"{num:04d}-{slugify(a.slug)}.md"
    body = f"# {a.title}\n\n{a.body.strip()}\n"
    if a.evidence:
        body += f"\n**Evidence**: {a.evidence.strip()}\n"
    if a.implications:
        body += f"\n**Implications**: {a.implications.strip()}\n"
    body += f"\n<!-- {TODAY.isoformat()} -->\n"
    p.write_text(body, encoding="utf-8")
    print(f"✨ 学习记录 LR-{num:04d}：{rel(p, LAB_DIR)}")


# ============================================================ 进度
def cmd_done(a) -> None:
    t = find_topic(a.topic)
    lines = t.text.splitlines()
    hit = False
    for i, line in enumerate(lines):
        m = STEP_RE.match(line.strip())
        if m and int(m.group(2)) == a.step:
            new = re.sub(r"^(\s*-\s*)\[ \]", r"\1[x]", line)
            if not DATE_RE.search(new):
                new = new.rstrip() + f" ✓{TODAY.isoformat()}"
            lines[i] = new
            hit = True
    if not hit:
        sys.exit(f"❌ 计划中没有步骤 {a.step}")
    t.plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    t = Topic(t.dir)
    d, n = t.progress
    print(f"✅ {t.slug} 第 {a.step} 课完成（{d}/{n}）")
    if d == n:
        print(f"🎉 课题全部完成！请把 ROADMAP 关联项「{t.fields.get('关联', '-')}」勾为 [x]，并把计划状态改为 已完成。")
    build_index(quiet=True)


def cmd_reviewed(a) -> None:
    t = find_topic(a.topic)
    text = t.text.rstrip("\n")
    if "## 复习" not in text:
        text += "\n\n## 复习\n"
    text += f"\n- {TODAY.isoformat()} 复习 {a.what or '全部'}"
    t.plan_path.write_text(text + "\n", encoding="utf-8")
    nt = Topic(t.dir)
    print(f"✅ 已记录复习；下次建议：{nt.review_due()}")
    build_index(quiet=True)


# ============================================================ index（md + html + 导航）
def mission_why() -> str:
    m = re.search(r"##\s*Why\s*\n+(.+?)(?:\n\n|\n##|$)", read(LEARN_DIR / "MISSION.md"), flags=re.S)
    return m.group(1).strip() if m else ""


def update_nav(t: Topic) -> None:
    ls = t.lessons
    for i, p in enumerate(ls):
        text = read(p)
        if "<!-- LAB:NAV -->" not in text:
            continue
        parts = []
        if i > 0:
            parts.append(f'<a class="prev" href="{html.escape(ls[i - 1].name)}"><small>← 上一课</small>{html.escape(html_title(ls[i - 1]))}</a>')
        if i < len(ls) - 1:
            parts.append(f'<a class="next" href="{html.escape(ls[i + 1].name)}"><small>下一课 →</small>{html.escape(html_title(ls[i + 1]))}</a>')
        else:
            home = rel(LEARN_DIR / "index.html", p.parent)
            parts.append(f'<a class="next" href="{home}#{html.escape(t.slug)}"><small>本课题最新一课</small>回到学习地图 · 说「继续」生成下一课</a>')
        block = "<!-- LAB:NAV -->\n    <nav class=\"lab-nav\">" + "".join(parts) + "</nav>\n    <!-- /LAB:NAV -->"
        new = re.sub(r"<!-- LAB:NAV -->.*?<!-- /LAB:NAV -->", lambda _m: block, text, flags=re.S)
        if new != text:
            p.write_text(new, encoding="utf-8")


def build_index(quiet: bool = False) -> None:
    LEARN_DIR.mkdir(exist_ok=True)
    ts = topics()
    cur = current_topic()
    for t in ts:
        update_nav(t)

    # ---------- index.md（GitHub / 网页 AI 可读）
    md = ["# 学习档案索引", "", "> 由 `python3 study.py learn index` 自动生成，勿手改。可视化版本：[index.html](index.html)", "",
          "| 主题 | 目标 | 进度 | 下一课 | 最后学习 |", "|---|---|---|---|---|"]
    for t in ts:
        d, n = t.progress
        nxt = t.next_step
        md.append(f"| [{t.slug}]({t.slug}/{PLAN_NAME}) | {t.goal} | {d}/{n} {t.status} | {f'{nxt[chr(110)]}. {nxt[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)]}' if nxt else '—'} | {t.last_date or '-'} |")
    refs = sorted(REFS_DIR.glob("*.html")) if REFS_DIR.exists() else []
    if refs:
        md += ["", "## 速查表", ""] + [f"- [{html_title(p)}](reference/{p.name})" for p in refs]
    recs = records()
    if recs:
        md += ["", "## 学习记录", ""] + [f"- [{p.stem}](learning-records/{p.name})：{title}" for p, title, _ in recs]
    (LEARN_DIR / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---------- index.html（课程首页仪表盘）
    e = html.escape
    md_in = lambda s: re.sub(r"`([^`]+)`", r"<code>\1</code>", e(s))
    rd, rt = roadmap_progress()
    n_less = sum(len(t.lessons) for t in ts)
    cards = []
    for t in ts:
        d, n = t.progress
        pct = int(100 * d / n) if n else 0
        cls = "done" if t.status == "已完成" else "paused" if t.status == "暂停" else ""
        items = []
        for s in t.steps:
            label = f"{s['n']}. {md_in(s['title'])}"
            if s["lesson"] and (t.dir / s["lesson"]).exists():
                label = f'<a href="{e(t.slug)}/{e(s["lesson"])}">{label}</a>'
            items.append(f"<li>{'✅' if s['done'] else '⬜'} {label}</li>")
        linked = {s["lesson"] for s in t.steps}
        for p in t.lessons:
            if rel(p, t.dir) not in linked:
                items.append(f'<li>📄 <a href="{e(t.slug)}/lessons/{e(p.name)}">{e(html_title(p))}</a></li>')
        due = t.review_due()
        due_html = f' · <span class="status-tag">⏰ 建议复习</span>' if due and due <= TODAY else ""
        cards.append(f"""<div class="card" id="{e(t.slug)}">
  <h3>{e(t.title)} <span class="status-tag {cls}">{e(t.status)}</span>{due_html}</h3>
  <div class="goal">{md_in(t.goal)}</div>
  <div class="bar"><span style="width:{pct}%"></span></div>
  <div class="small muted">{d}/{n} 课 · 最近 {t.last_date or '-'} · <a href="{e(t.slug)}/{PLAN_NAME}">计划.md</a></div>
  <ul>{''.join(items)}</ul>
</div>""")
    cont = ""
    if cur and cur.next_step:
        s = cur.next_step
        cont = f"""<div class="win"><div class="icon">📍</div><div><h4>继续学习</h4>
<p><b>{e(cur.title)}</b> → 第 {s['n']} 课：{md_in(s['title'])}</p>
<p class="small muted">对 AI 说「继续」即可；掌握标志：{md_in(s['mastery'] or '—')}</p></div></div>"""
    ref_html = "".join(f'<li><a href="reference/{e(p.name)}">{e(html_title(p))}</a></li>' for p in refs) or "<li class='muted'>暂无（说「整理笔记」生成）</li>"
    rec_html = "".join(f'<li><a href="learning-records/{e(p.name)}">{e(p.stem[:4])}</a> · {e(title)}</li>' for p, title, _ in recs[-10:][::-1]) or "<li class='muted'>暂无</li>"
    assets = rel(ASSETS_DIR, LEARN_DIR)
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>学习地图 · AI Lab</title><link rel="stylesheet" href="{assets}/lab.css"></head>
<body class="ref"><div class="lab-layout"><main class="lab-main">
<!-- 由 python3 study.py learn index 自动生成，勿手改 -->
<header class="lab-hero">
  <div class="crumbs">AI Lab / 学习</div>
  <h1>📚 学习地图</h1>
  <p class="subtitle">{e(mission_why() or 'LLM → Agent → 具身智能：把每个知识点讲透、跑通、讲得出来')}</p>
  <div class="chips"><span class="chip">🗺 ROADMAP {rd}/{rt}</span><span class="chip">📘 课题 {len(ts)}</span><span class="chip">📄 课程页 {n_less}</span><span class="chip">🧠 学习记录 {len(recs)}</span><span class="chip">🕒 {TODAY.isoformat()}</span></div>
</header>
{cont}
<h2>课题</h2>
<div class="cards topics">{''.join(cards) or '<p class="muted">还没有课题，对 AI 说「开始学习 XX」。</p>'}</div>
<div class="cards">
  <div class="card"><h3>📇 速查表</h3><ul>{ref_html}</ul></div>
  <div class="card"><h3>🧠 最近的学习记录</h3><ul>{rec_html}</ul></div>
  <div class="card"><h3>💬 常用指令</h3><ul><li>开始学习 XX · 继续</li><li>详细推导 · 讲解代码 · 可视化</li><li>复习 · 整理笔记 · 练一下（可选）</li></ul></div>
</div>
<footer class="lab-footer">lab-teach · 进度真相源：ROADMAP_16W.md（周级）+ 各课题 计划.md（课级）</footer>
</main></div><script src="{assets}/lab.js"></script></body></html>
"""
    (LEARN_DIR / "index.html").write_text(page, encoding="utf-8")
    if not quiet:
        print(f"✨ 已重建 {rel(LEARN_DIR / 'index.md', LAB_DIR)} 与 index.html（{len(ts)} 课题 / {n_less} 课程页）")


def cmd_index(_a) -> None:
    build_index()


# ============================================================ 正确性：golden / check / shot
def find_python() -> str:
    env = os.environ.get("LAB_PY")
    if env:
        return env
    for name in ("ai-lab", "test", "robot-lab"):
        for base in (Path.home() / "Apps/miniconda3/envs", Path.home() / "miniconda3/envs", Path.home() / "anaconda3/envs"):
            for exe in (base / name / "bin/python", base / name / "python.exe"):
                if exe.exists():
                    return str(exe)
    return sys.executable


def cmd_py(_a) -> None:
    print(find_python())


def cmd_golden(a) -> None:
    lesson = Path(a.lesson).resolve()
    script = Path(a.script).resolve()
    py = find_python()
    r = subprocess.run([py, str(script)], capture_output=True, text=True, cwd=str(LAB_DIR), encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"❌ 验证脚本失败（{py}）：\n{r.stderr[-2000:]}")
    out = r.stdout.strip()
    js = None
    for chunk in (out, out.splitlines()[-1] if out else ""):
        try:
            js = json.loads(chunk)
            break
        except json.JSONDecodeError:
            continue
    if not isinstance(js, dict):
        sys.exit("❌ 验证脚本需在 stdout 最后一行打印一个 JSON 对象（json.dumps(dict)）")
    js["_meta"] = {"script": rel(script, LAB_DIR), "python": Path(py).parent.parent.name, "generated": TODAY.isoformat()}
    text = read(lesson)
    block = ("<!-- LAB:GOLDEN -->\n<script type=\"application/json\" id=\"lab-golden\">"
             + json.dumps(js, ensure_ascii=False) + "</script>\n<!-- /LAB:GOLDEN -->")
    if "<!-- LAB:GOLDEN -->" not in text:
        sys.exit("❌ 课程页缺少 <!-- LAB:GOLDEN --> 标记")
    lesson.write_text(re.sub(r"<!-- LAB:GOLDEN -->.*?<!-- /LAB:GOLDEN -->", lambda _m: block, text, flags=re.S), encoding="utf-8")
    print(f"✨ 金标准已注入 {rel(lesson, LAB_DIR)}：")
    for k, v in js.items():
        if k != "_meta":
            print(f"   {k} = {json.dumps(v, ensure_ascii=False)[:100]}")


def find_chrome() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def browser_dom(path: Path) -> str | None:
    chrome = find_chrome()
    if not chrome:
        return None
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
                        "--virtual-time-budget=6000", "--dump-dom", path.resolve().as_uri()],
                       capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
    return r.stdout


def static_check(p: Path) -> list[str]:
    issues = []
    text = read(p)
    for m in re.finditer(r"\{\{[A-Z_]+\}\}", text):
        issues.append(f"未替换占位符 {m.group(0)}")
    n_todo = text.count("TODO-LESSON")
    if n_todo:
        issues.append(f"还有 {n_todo} 处 TODO-LESSON 未填写")
    for m in re.finditer(r'(?:href|src)="([^"#:?]+)(?:[#?][^"]*)?"', text):
        target = m.group(1)
        if target.startswith(("http", "mailto", "javascript", "data")) or not target.strip():
            continue
        if not (p.parent / html.unescape(target)).exists():
            issues.append(f"链接失效 {target}")
    if "lab.css" not in text or "lab.js" not in text:
        issues.append("未引用 lab.css / lab.js")
    g = re.search(r'<script type="application/json" id="lab-golden">(.*?)</script>', text, flags=re.S)
    if g:
        try:
            gold = json.loads(g.group(1) or "{}")
            if "Lab.check(" in re.sub(r"//.*", "", text) and not {k for k in gold if k != "_meta"}:
                issues.append("用了 Lab.check 但金标准为空：先运行 golden")
        except json.JSONDecodeError as ex:
            issues.append(f"lab-golden 不是合法 JSON：{ex}")
    body = re.sub(r"<(script|pre|code|style)[^>]*>.*?</\1>", "", text, flags=re.S)
    if body.count("$$") % 2:
        issues.append("$$ 数量为奇数，可能有未闭合的公式")
    return issues


def cmd_check(a) -> None:
    paths = [Path(x) for x in a.paths] if a.paths else sorted(p for p in LEARN_DIR.rglob("*.html"))
    total_bad = 0
    for p in paths:
        issues = static_check(p)
        if a.browser and p.name != "index.html":
            dom = browser_dom(p)
            if dom is None:
                issues.append("（未找到 Chrome/Chromium，跳过浏览器检查）")
            else:
                ready = 'data-lab-ready="1"' in dom
                m = re.search(r'data-lab-checks="pass=(\d+);fail=(\d+);errors=(\d+)"', dom)
                if not ready:
                    issues.append("浏览器中 Lab 未完成初始化（JS 报错或资源路径错）")
                if m:
                    ps, fl, er = map(int, m.groups())
                    if fl or er:
                        issues.append(f"浏览器校验：{ps} 通过 / {fl} 失败 / {er} 个 JS 错误")
                        for ck in re.findall(r'<div class="ck fail">(.*?)</div>', dom):
                            issues.append("  " + re.sub(r"<[^>]+>", "", html.unescape(ck)))
                    else:
                        print(f"   🔬 {rel(p, LAB_DIR)}：{ps} 项数值校验通过，0 JS 错误")
        if issues:
            total_bad += 1
            print(f"⚠️  {rel(p.resolve(), LAB_DIR)}")
            for i in issues:
                print(f"     - {i}")
        else:
            print(f"✅ {rel(p.resolve(), LAB_DIR)}")
    sys.exit(1 if total_bad else 0)


def cmd_shot(a) -> None:
    chrome = find_chrome()
    if not chrome:
        sys.exit("❌ 未找到 Chrome/Chromium")
    p = Path(a.path).resolve()
    out = Path(a.out or (p.with_suffix(".png").name)).resolve()
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={a.width},{a.height}", "--virtual-time-budget=6000", f"--screenshot={out}", p.as_uri()],
                   capture_output=True, timeout=90)
    print(f"📸 {out}")


def cmd_open(a) -> None:
    p = str(Path(a.path).resolve())
    opener = "open" if sys.platform == "darwin" else "xdg-open" if shutil.which("xdg-open") else None
    if sys.platform.startswith("win"):
        os.startfile(p)  # type: ignore[attr-defined]
    elif opener:
        subprocess.Popen([opener, p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"🌐 {p}")


# ============================================================ CLI
def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="study.py learn", description="lab-teach 学习工作区引擎")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    s = sub.add_parser("context"); s.add_argument("topic")
    s = sub.add_parser("nb"); s.add_argument("path"); s.add_argument("--outline", action="store_true"); s.add_argument("--cells"); s.add_argument("--grep"); s.add_argument("--export")
    s = sub.add_parser("snippet"); s.add_argument("path"); s.add_argument("--lines"); s.add_argument("--cell", type=int); s.add_argument("--lang"); s.add_argument("--for", dest="for_lesson")
    s = sub.add_parser("new-topic"); s.add_argument("slug"); s.add_argument("--title"); s.add_argument("--goal"); s.add_argument("--roadmap"); s.add_argument("--sources"); s.add_argument("--step", action="append")
    s = sub.add_parser("new-lesson"); s.add_argument("topic"); s.add_argument("slug"); s.add_argument("--title", required=True); s.add_argument("--step", type=int); s.add_argument("--force", action="store_true")
    s = sub.add_parser("new-ref"); s.add_argument("slug"); s.add_argument("--title", required=True)
    s = sub.add_parser("record"); s.add_argument("slug"); s.add_argument("--title", required=True); s.add_argument("--body", required=True); s.add_argument("--evidence"); s.add_argument("--implications")
    s = sub.add_parser("done"); s.add_argument("topic"); s.add_argument("step", type=int)
    s = sub.add_parser("reviewed"); s.add_argument("topic"); s.add_argument("--what")
    sub.add_parser("index")
    s = sub.add_parser("golden"); s.add_argument("lesson"); s.add_argument("script")
    s = sub.add_parser("check"); s.add_argument("paths", nargs="*"); s.add_argument("--browser", action="store_true")
    s = sub.add_parser("shot"); s.add_argument("path"); s.add_argument("--out"); s.add_argument("--width", type=int, default=1440); s.add_argument("--height", type=int, default=2200)
    s = sub.add_parser("open"); s.add_argument("path")
    sub.add_parser("py")
    a = ap.parse_args(argv)
    {
        "status": cmd_status, "context": cmd_context, "nb": cmd_nb, "snippet": cmd_snippet,
        "new-topic": cmd_new_topic, "new-lesson": cmd_new_lesson, "new-ref": cmd_new_ref, "record": cmd_record,
        "done": cmd_done, "reviewed": cmd_reviewed, "index": cmd_index, "golden": cmd_golden,
        "check": cmd_check, "shot": cmd_shot, "open": cmd_open, "py": cmd_py,
    }[a.cmd](a)


if __name__ == "__main__":
    main()
