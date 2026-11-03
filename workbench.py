#!/usr/bin/env python3
"""AI Lab 本地今日工作台。直接运行打开；--serve 仅启动本机服务。"""
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


def now():
    return dt.datetime.now(ZONE)


def file_url(path):
    return "/files/" + quote(path.relative_to(ROOT).as_posix())


def catalog():
    tasks, weeks, topics = {}, [], []
    week = None
    for index, line in enumerate(study.ROADMAP_FILE.read_text().splitlines()):
        heading = re.match(r"^### W(\d+) · (.+)", line)
        if heading:
            week = {"number": int(heading[1]), "title": heading[2], "tasks": []}
            weeks.append(week)
        match = CHECK.match(line)
        if week is not None and match:
            key = f"week:{week['number']}:{len(week['tasks'])}"
            task = dict(id=key, title=match[3], done=match[2].lower() == "x",
                        kind="周任务", week=week["number"], url=file_url(study.ROADMAP_FILE),
                        path=study.ROADMAP_FILE, line=index, mastery="")
            tasks[key] = task
            week["tasks"].append(key)
    if COURSE:
        for topic in COURSE.topics():
            keys = []
            for step in topic.steps:
                key = f"lesson:{topic.slug}:{step['n']}"
                path = topic.dir / step["lesson"] if step["lesson"] else None
                line = next(i for i, raw in enumerate(topic.text.splitlines())
                            if (m := COURSE.STEP_RE.match(raw.strip())) and int(m[2]) == step["n"])
                tasks[key] = dict(id=key, title=step["title"], done=step["done"],
                                  kind="课程", topic=topic.slug, number=step["n"],
                                  url=file_url(path) if path and path.exists() else "",
                                  mastery=step["mastery"], path=topic.plan_path, line=line)
                keys.append(key)
            due = topic.review_due()
            topics.append(dict(slug=topic.slug, title=topic.title, goal=topic.goal,
                               tasks=keys, review_due=due.isoformat() if due else None,
                               plan=file_url(topic.plan_path)))
    return tasks, weeks, topics


def read_daily(date):
    path = ROOT / "daily" / f"{date}.md"
    text = path.read_text() if path.exists() else ""
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


def state():
    date = now().date().isoformat()
    tasks, weeks, topics = catalog()
    active = next((week for week in weeks if any(not tasks[key]["done"] for key in week["tasks"])), weeks[-1])
    daily = read_daily(date)
    # 今日默认只排一课；周任务由用户按精力加入。
    if not daily["selected"] and daily["status"] == "未打卡":
        nxt = next((task for task in tasks.values() if task["kind"] == "课程" and not task["done"]), None)
        if nxt is None:
            nxt = next((tasks[key] for key in active["tasks"] if not tasks[key]["done"]), None)
        daily["selected"] = [dict(id=nxt["id"], title=nxt["title"], done=False)] if nxt else []
    for selected in daily["selected"]:
        if selected["id"] in tasks:
            selected["done"] = tasks[selected["id"]]["done"]
    history = []
    for path in sorted((ROOT / "daily").glob("????-??-??.md"), reverse=True)[:30]:
        log = read_daily(path.stem)
        history.append(dict(date=path.stem, status=log["status"] if log["status"] != "未打卡" else "已有日志",
                            notes=log["notes"], tomorrow=log["tomorrow"],
                            url=file_url(path), minutes=log["minutes"]))
    records = sorted((ROOT / "学习/learning-records").glob("*.md"), reverse=True)
    latest = dict(text=records[0].read_text(), url=file_url(records[0])) if records else None
    public = {key: {k: v for k, v in task.items() if k not in ("path", "line")} for key, task in tasks.items()}
    return dict(service="ai-lab-workbench", date=date, timezone=str(ZONE), daily=daily,
                tasks=public, weeks=weeks, topics=topics, active=active["number"],
                history=history, latest=latest, map=file_url(ROOT / "学习/index.html"))


def save(payload):
    date = now().date().isoformat()
    if payload.get("date") != date:
        raise ValueError("日期已经变化，请刷新页面后再保存。")
    tasks, _, _ = catalog()
    selected = payload.get("selected", [])
    changes = payload.get("changes", {})
    if any(key not in tasks for key in changes):
        raise ValueError("计划已更新，请刷新后重新选择任务。")
    minutes = str(payload.get("minutes", "")).strip()
    if minutes and (not minutes.isdigit() or int(minutes) > 1440):
        raise ValueError("学习时长请填 0–1440 分钟。")
    if payload.get("checkin") and not any(key in tasks for key in selected) and not payload.get("notes", "").strip():
        raise ValueError("先选择一项任务，或写一句今天的收获，再打卡。")
    files = {}
    for key, done in changes.items():
        task = tasks[key]
        if task["done"] == bool(done):
            continue
        path = task["path"]
        lines = files.setdefault(path, path.read_text().splitlines())
        line = re.sub(r"^(\s*-\s*)\[[ xX]\]", lambda m: m[1] + ("[x]" if done else "[ ]"), lines[task["line"]])
        if task["kind"] == "课程":
            line = re.sub(r"\s*✓\s*\d{4}-\d{2}-\d{2}", "", line)
            if done:
                line += f" ✓{date}"
        lines[task["line"]] = line
    for path, lines in files.items():
        path.write_text("\n".join(lines) + "\n")
    if files and COURSE:
        COURSE.build_index(quiet=True)
    tasks, _, _ = catalog()
    path = ROOT / "daily" / f"{date}.md"
    original = path.read_text() if path.exists() else f"# {date} 学习日志\n"
    previous = read_daily(date)
    status = "已打卡" if payload.get("checkin") or previous["status"] == "已打卡" else "草稿"
    lines = [START, "## 今日工作台", f"状态：{status}", f"投入分钟：{minutes}",
             f"更新时间：{now().isoformat(timespec='minutes')}", "", "### 今日任务"]
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
    path.write_text(updated)
    return state()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def respond(self, body, content_type="application/json; charset=utf-8", status=200):
        raw = json.dumps(body, ensure_ascii=False).encode() if content_type.startswith("application/json") else body
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
        if path.suffix == ".md":
            body = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>' + html.escape(path.name)
                    + '</title><style>body{max-width:960px;margin:50px auto;padding:0 24px;background:#faf9f6;color:#252c29;'
                    'font:16px/1.8 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#27674d}</style>'
                    '<a href="/">← 返回今日工作台</a><pre>' + html.escape(path.read_text()) + '</pre></html>').encode()
            return self.respond(body, "text/html; charset=utf-8")
        return self.respond(path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")

    def do_POST(self):
        if self.path != "/api/save":
            return self.respond({"error": "接口不存在"}, status=404)
        # 浏览器中的其他网站不能以表单请求修改本地进度。
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.respond({"error": "请使用工作台保存"}, status=415)
        if self.headers.get("Origin") not in (None, URL):
            return self.respond({"error": "请从本地工作台保存"}, status=403)
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            self.respond(save(payload))
        except (ValueError, KeyError) as error:
            self.respond({"error": str(error)}, status=400)


def launch():
    try:
        with urlopen(URL + "/api/state", timeout=1) as response:
            if json.load(response).get("service") != "ai-lab-workbench":
                raise RuntimeError(f"端口 {PORT} 已被其他程序占用")
    except OSError:
        log = Path.home() / ".local/share/ai-lab/workbench.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as output:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--serve"],
                             stdout=output, stderr=output, start_new_session=True)
        for _ in range(40):
            try:
                with urlopen(URL + "/api/state", timeout=1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError(f"工作台未启动，请查看 {log}")
    subprocess.Popen(["/usr/bin/google-chrome", f"--app={URL}",
                      f"--user-data-dir={Path.home()}/.local/share/ai-lab/chrome", "--class=AI-Lab",
                      "--no-first-run", "--no-default-browser-check", "--disable-background-mode"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    if parser.parse_args().serve:
        print(f"AI Lab: {URL}", flush=True)
        HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    else:
        launch()
