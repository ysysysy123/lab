#!/usr/bin/env python3
"""AI Lab 交互式学习工作台 v2（ADHD 零决策驾驶舱 + 真实文件读写 + 自动 Git 远程同步）。"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlsplit, quote
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import study

ROOT = Path(__file__).resolve().parent
UI = ROOT / "workbench"
PORT = 18761
URL = f"http://127.0.0.1:{PORT}"
ZONE = ZoneInfo("America/Los_Angeles")
START, END = "<!-- ai-lab:today -->", "<!-- /ai-lab:today -->"
COURSE = study._load_course_engine()
CHECK = re.compile(r"^(\s*-\s*)\[([ xX])\]\s+(.+)$")
LC_SLUG_RE = re.compile(r"\(`([a-zA-Z0-9_]+)`")

_SYNC_STATUS = {"running": False, "last_ok": True, "last_time": "", "last_msg": "就绪"}


def now():
    return dt.datetime.now(ZONE)


def trigger_async_sync(reason: str) -> None:
    """后台非阻塞执行 Git 自动提交与推送，不卡前端点击响应"""
    def _worker():
        _SYNC_STATUS["running"] = True
        res = study.sync_repo(reason)
        _SYNC_STATUS["running"] = False
        _SYNC_STATUS["last_ok"] = res.get("ok", False)
        _SYNC_STATUS["last_time"] = now().strftime("%H:%M:%S")
        _SYNC_STATUS["last_msg"] = (
            f"已同步 GitHub ({res.get('head', '')[:7]})"
            if res.get("ok")
            else f"本地已存 · 推送待重试 ({res.get('error', '')[:40]})"
        )

    threading.Thread(target=_worker, daemon=True).start()


def file_url(path: Path) -> str:
    return "/files/" + quote(path.relative_to(ROOT).as_posix())


def catalog():
    tasks, weeks, topics, lc_list, paper_list = {}, [], [], [], []
    week = None
    if study.ROADMAP_FILE.exists():
        for index, line in enumerate(study.ROADMAP_FILE.read_text(encoding="utf-8").splitlines()):
            heading = re.match(r"^### W(\d+) · (.+)", line)
            if heading:
                week = {"number": int(heading[1]), "title": heading[2].strip(), "tasks": []}
                weeks.append(week)
            match = CHECK.match(line)
            if week is not None and match:
                key = f"week:{week['number']}:{len(week['tasks'])}"
                task = dict(
                    id=key,
                    title=match[3].strip(),
                    done=match[2].lower() == "x",
                    kind="周计划",
                    week=week["number"],
                    url=file_url(study.ROADMAP_FILE),
                    path=study.ROADMAP_FILE,
                    line=index,
                    mastery="",
                )
                tasks[key] = task
                week["tasks"].append(key)

    if COURSE:
        for topic in COURSE.topics():
            keys = []
            for step in topic.steps:
                key = f"lesson:{topic.slug}:{step['n']}"
                path = topic.dir / step["lesson"] if step["lesson"] else None
                line = next(
                    i
                    for i, raw in enumerate(topic.text.splitlines())
                    if (m := COURSE.STEP_RE.match(raw.strip())) and int(m[2]) == step["n"]
                )
                tasks[key] = dict(
                    id=key,
                    title=step["title"],
                    done=step["done"],
                    kind="课程",
                    topic=topic.slug,
                    number=step["n"],
                    url=file_url(path) if path and path.exists() else "",
                    mastery=step["mastery"],
                    path=topic.plan_path,
                    line=line,
                )
                keys.append(key)
            due = topic.review_due()
            topics.append(
                dict(
                    slug=topic.slug,
                    title=topic.title,
                    goal=topic.goal,
                    tasks=keys,
                    review_due=due.isoformat() if due else None,
                    plan=file_url(topic.plan_path),
                )
            )

    # 解析力扣 Hot100 追踪单
    if study.LC_TRACKER_FILE.exists():
        sec_title = "Hot100"
        lc_idx = 0
        for index, line in enumerate(study.LC_TRACKER_FILE.read_text(encoding="utf-8").splitlines()):
            sec_m = re.match(r"^##\s+\d+\.\s*(.+)$", line)
            if sec_m:
                sec_title = sec_m.group(1).strip()
            match = CHECK.match(line)
            if match:
                raw_title = match[3].strip()
                slug_m = LC_SLUG_RE.search(raw_title)
                slug = slug_m.group(1) if slug_m else ""
                script_path = ROOT / "leetcode" / f"{slug}.py" if slug else None
                key = f"lc:{lc_idx}"
                lc_idx += 1
                item = dict(
                    id=key,
                    title=raw_title,
                    done=match[2].lower() == "x",
                    kind="力扣",
                    section=sec_title,
                    slug=slug,
                    script_exists=bool(script_path and script_path.exists()),
                    script_rel=f"leetcode/{slug}.py" if slug else "",
                    url=file_url(script_path) if script_path and script_path.exists() else file_url(study.LC_TRACKER_FILE),
                    path=study.LC_TRACKER_FILE,
                    line=index,
                    mastery="",
                )
                tasks[key] = item
                lc_list.append(item)

    # 解析 30 篇论文清单
    if study.PAPERS_LIST_FILE.exists():
        p_sec = "论文"
        p_idx = 0
        for index, line in enumerate(study.PAPERS_LIST_FILE.read_text(encoding="utf-8").splitlines()):
            sec_m = re.match(r"^##\s+(.+)$", line)
            if sec_m:
                p_sec = sec_m.group(1).strip()
            match = CHECK.match(line)
            if match:
                key = f"paper:{p_idx}"
                p_idx += 1
                item = dict(
                    id=key,
                    title=match[3].strip(),
                    done=match[2].lower() == "x",
                    kind="论文",
                    section=p_sec,
                    url=file_url(study.PAPERS_LIST_FILE),
                    path=study.PAPERS_LIST_FILE,
                    line=index,
                    mastery="",
                )
                tasks[key] = item
                paper_list.append(item)

    return tasks, weeks, topics, lc_list, paper_list


def read_daily(date: str) -> dict:
    path = ROOT / "daily" / f"{date}.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    block = text.partition(START)[2].partition(END)[0]
    result = dict(status="未打卡", minutes="", notes="", blocker="", tomorrow="", selected=[])
    if block:
        for name, label in [("status", "状态"), ("minutes", "投入分钟")]:
            match = re.search(rf"^{label}：(.*)$", block, re.M)
            if match:
                result[name] = match[1].strip()
        for name, label in [("notes", "今日收获"), ("blocker", "卡住的问题"), ("tomorrow", "下次从这里开始")]:
            match = re.search(rf"^### {label}\n(.*?)(?=\n### |\Z)", block, re.S | re.M)
            if match:
                result[name] = match[1].strip()
        for match in re.finditer(r"^- \[([ xX])\] (.*?) <!-- task:(.*?) -->$", block, re.M):
            result["selected"].append(dict(id=match[3], title=match[2], done=match[1].lower() == "x"))
    result["exists"] = path.exists()
    result["url"] = file_url(path) if path.exists() else ""
    return result


def serialize_cards(today_date: dt.date) -> list[dict]:
    out = []
    for idx, c in enumerate(study.load_all_cards()):
        out.append(
            dict(
                index=idx,
                q=c["q"],
                a=c["a"],
                due=c["due"].isoformat(),
                interval=c["interval"],
                is_due=c["due"] <= today_date,
                file=c["path"].relative_to(ROOT).as_posix(),
            )
        )
    return out


def state():
    today_dt = now().date()
    date = today_dt.isoformat()
    tasks, weeks, topics, lc_list, paper_list = catalog()
    active = next(
        (week for week in weeks if any(not tasks[key]["done"] for key in week["tasks"])),
        weeks[-1] if weeks else {"number": 0, "title": "切换周", "tasks": []},
    )
    daily = read_daily(date)
    history = []
    for path in sorted((ROOT / "daily").glob("????-??-??.md"), reverse=True)[:30]:
        log = read_daily(path.stem)
        history.append(
            dict(
                date=path.stem,
                status=log["status"] if log["status"] != "未打卡" else "已有日志",
                notes=log["notes"],
                tomorrow=log["tomorrow"],
                blocker=log["blocker"],
                selected=log["selected"],
                url=file_url(path),
                minutes=log["minutes"],
            )
        )

    if not daily["selected"] and daily["status"] == "未打卡":
        nxt = next((tasks[key] for key in active["tasks"] if not tasks[key]["done"]), None)
        if nxt is None:
            nxt = next((task for task in tasks.values() if task["kind"] == "课程" and not task["done"]), None)
        daily["selected"] = [dict(id=nxt["id"], title=nxt["title"], done=False)] if nxt else []

    for selected in daily["selected"]:
        if selected["id"] in tasks:
            selected["done"] = tasks[selected["id"]]["done"]

    cards = serialize_cards(today_dt)
    records = sorted((ROOT / "学习/learning-records").glob("*.md"), reverse=True)
    latest = dict(text=records[0].read_text(encoding="utf-8"), url=file_url(records[0])) if records else None
    public_tasks = {
        key: {k: v for k, v in task.items() if k not in ("path", "line")}
        for key, task in tasks.items()
    }
    public_lc = [{k: v for k, v in item.items() if k not in ("path", "line")} for item in lc_list]
    public_papers = [{k: v for k, v in item.items() if k not in ("path", "line")} for item in paper_list]

    git_info = study.git_sync_info()
    git_info.update(_SYNC_STATUS)

    return dict(
        service="ai-lab-workbench",
        date=date,
        timezone=str(ZONE),
        daily=daily,
        tasks=public_tasks,
        weeks=weeks,
        topics=topics,
        leetcode=public_lc,
        papers=public_papers,
        cards=cards,
        active=active["number"],
        history=history,
        latest=latest,
        git=git_info,
        map=file_url(ROOT / "学习/index.html"),
    )


def apply_task_changes(changes: dict) -> bool:
    tasks, _, _, _, _ = catalog()
    date = now().date().isoformat()
    files: dict[Path, list[str]] = {}
    any_changed = False
    for key, done in changes.items():
        if key not in tasks:
            continue
        task = tasks[key]
        if task["done"] == bool(done):
            continue
        any_changed = True
        path: Path = task["path"]
        lines = files.setdefault(path, path.read_text(encoding="utf-8").splitlines())
        line = re.sub(
            r"^(\s*-\s*)\[[ xX]\]",
            lambda m: m[1] + ("[x]" if done else "[ ]"),
            lines[task["line"]],
        )
        if task["kind"] == "课程":
            line = re.sub(r"\s*✓\s*\d{4}-\d{2}-\d{2}", "", line)
            if done:
                line += f" ✓{date}"
        lines[task["line"]] = line
    for path, lines in files.items():
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if files and COURSE:
        COURSE.build_index(quiet=True)
    return any_changed


def save(payload: dict) -> dict:
    date = now().date().isoformat()
    selected = payload.get("selected", [])
    changes = payload.get("changes", {})
    minutes = str(payload.get("minutes", "")).strip()
    if minutes and (not minutes.isdigit() or int(minutes) > 1440):
        raise ValueError("学习时长请填 0–1440 分钟。")

    apply_task_changes(changes)
    tasks, _, _, _, _ = catalog()

    path = ROOT / "daily" / f"{date}.md"
    original = path.read_text(encoding="utf-8") if path.exists() else f"# {date} 学习日志\n"
    previous = read_daily(date)
    status = "已打卡" if payload.get("checkin") or previous["status"] == "已打卡" else "草稿"
    lines = [
        START,
        "## 今日工作台",
        f"状态：{status}",
        f"投入分钟：{minutes}",
        f"更新时间：{now().isoformat(timespec='minutes')}",
        "",
        "### 今日任务",
    ]
    for key in dict.fromkeys(selected):
        if key in tasks:
            task = tasks[key]
            lines.append(f"- [{'x' if task['done'] else ' '}] {task['title']} <!-- task:{key} -->")
    for key, label in [("notes", "今日收获"), ("blocker", "卡住的问题"), ("tomorrow", "下次从这里开始")]:
        lines.extend(["", f"### {label}", str(payload.get(key, "")).strip()])
    lines.append(END)
    block = "\n".join(lines)
    if START in original and END in original:
        updated = original.partition(START)[0] + block + original.partition(END)[2]
    else:
        updated = original.rstrip() + "\n\n" + block + "\n"
    path.parent.mkdir(exist_ok=True)
    path.write_text(updated, encoding="utf-8")

    trigger_async_sync(f"chore(workbench): save daily progress ({date})")
    return state()


def toggle_single(payload: dict) -> dict:
    task_id = str(payload.get("id", ""))
    done = bool(payload.get("done", False))
    changed = apply_task_changes({task_id: done})
    if changed:
        trigger_async_sync(f"chore(workbench): {'check' if done else 'uncheck'} {task_id}")
    return state()


def review_card(payload: dict) -> dict:
    idx = int(payload.get("index", -1))
    passed = bool(payload.get("passed", True))
    new_a = str(payload.get("new_a", "")).strip()
    today_dt = now().date()
    cards = study.load_all_cards()
    if idx < 0 or idx >= len(cards):
        raise ValueError("卡片序号不存在")
    target = cards[idx]
    if new_a:
        path: Path = target["path"]
        text = path.read_text(encoding="utf-8")
        old_block = text[target["span"][0] : target["span"][1]]
        replaced = re.sub(
            r"(^##\s*Q:\s*.+?\n+A:\s*)(.+?)(\n+<!--\s*due:)",
            lambda m: m.group(1) + new_a + m.group(3),
            old_block,
            flags=re.MULTILINE | re.DOTALL,
        )
        path.write_text(text[: target["span"][0]] + replaced + text[target["span"][1] :], encoding="utf-8")
        cards = study.load_all_cards()
        target = cards[idx]

    new_iv = study.next_review_interval(target["interval"], passed)
    new_due = today_dt + dt.timedelta(days=new_iv)
    study.update_card_in_file(target, new_due, new_iv)
    trigger_async_sync(f"chore(review): card #{idx+1} -> {new_iv}d")
    return state()


def init_lc_script(payload: dict) -> dict:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", str(payload.get("slug", "")).strip()).strip("_")
    if not slug:
        raise ValueError("缺少题目标识 slug")
    study.cmd_lc(argparse.Namespace(slug=slug))
    trigger_async_sync(f"feat(leetcode): init {slug}.py")
    return state()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def respond(self, body, content_type="application/json; charset=utf-8", status=200):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8") if content_type.startswith("application/json") else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        route = unquote(urlsplit(self.path).path)
        if route == "/api/state":
            return self.respond(state())
        if route.startswith("/files/"):
            path = (ROOT / route[7:]).resolve()
            allowed = path.is_relative_to(ROOT) and not any(p.startswith(".") for p in path.relative_to(ROOT).parts)
            allowed = allowed or path.is_relative_to(ROOT / ".agents/skills/lab-teach/assets")
        else:
            path = UI / ("index.html" if route == "/" else route.lstrip("/"))
            path = path.resolve()
            allowed = path.is_relative_to(UI)
        if not allowed or not path.is_file():
            return self.respond({"error": "文件不存在"}, status=404)
        if path.suffix in (".md", ".py"):
            body = (
                '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'
                + html.escape(path.name)
                + '</title><style>body{max-width:980px;margin:40px auto;padding:0 24px;background:#f6f7fb;color:#1c2438;'
                'font:14px/1.75 ui-monospace,SFMono-Regular,Consolas,monospace}pre{background:#fff;border:1px solid #e8ebf3;border-radius:14px;padding:22px;white-space:pre-wrap;overflow-wrap:anywhere;box-shadow:0 8px 24px rgba(20,27,62,.04)}a{display:inline-block;margin-bottom:14px;color:#5654dc;font-family:system-ui,sans-serif;font-weight:700;text-decoration:none}</style>'
                '<a href="/">← 返回 AI Lab 学习工作台</a><pre>'
                + html.escape(path.read_text(encoding="utf-8"))
                + "</pre></html>"
            ).encode("utf-8")
            return self.respond(body, "text/html; charset=utf-8")
        return self.respond(path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")

    def do_POST(self):
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.respond({"error": "请使用 JSON 请求"}, status=415)
        if self.headers.get("Origin") not in (None, URL):
            return self.respond({"error": "仅允许从本地工作台调用"}, status=403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length)) if length > 0 else {}
            if self.path == "/api/save":
                return self.respond(save(payload))
            if self.path == "/api/toggle":
                return self.respond(toggle_single(payload))
            if self.path == "/api/review":
                return self.respond(review_card(payload))
            if self.path == "/api/lc-init":
                return self.respond(init_lc_script(payload))
            if self.path == "/api/sync":
                res = study.sync_repo(payload.get("reason") or "chore(workbench): manual sync")
                _SYNC_STATUS["last_ok"] = res.get("ok", False)
                _SYNC_STATUS["last_time"] = now().strftime("%H:%M:%S")
                _SYNC_STATUS["last_msg"] = (
                    f"已同步 GitHub ({res.get('head', '')[:7]})"
                    if res.get("ok")
                    else f"推送失败: {res.get('error', '')[:40]}"
                )
                return self.respond(state())
            return self.respond({"error": "接口不存在"}, status=404)
        except Exception as error:
            return self.respond({"error": str(error)}, status=400)


def launch():
    try:
        with urlopen(URL + "/api/state", timeout=1) as response:
            if json.load(response).get("service") != "ai-lab-workbench":
                raise RuntimeError(f"端口 {PORT} 已被其他程序占用")
    except OSError:
        log = Path.home() / ".local/share/ai-lab/workbench.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as output:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--serve"],
                stdout=output,
                stderr=output,
                start_new_session=True,
            )
        for _ in range(40):
            try:
                with urlopen(URL + "/api/state", timeout=1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError(f"工作台未启动，请查看 {log}")
    subprocess.Popen(
        [
            "/usr/bin/google-chrome",
            f"--app={URL}",
            f"--user-data-dir={Path.home()}/.local/share/ai-lab/chrome",
            "--class=AI-Lab",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-mode",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    if parser.parse_args().serve:
        print(f"AI Lab: {URL}", flush=True)
        HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    else:
        launch()
