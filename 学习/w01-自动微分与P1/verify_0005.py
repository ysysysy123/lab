#!/usr/bin/env python3
"""Lesson 0005 金标准验证脚本：解析 papers/READING_LIST.md 并校验 16 周 30 篇时间账本"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
READING_LIST = LAB_DIR / "papers" / "READING_LIST.md"

text = READING_LIST.read_text(encoding="utf-8")
items = re.findall(r"^\s*-\s*\[[ xX]\]\s*(🟢|🔴)\s+\*\*(.+?)\*\*", text, flags=re.MULTILINE)

skim_count = sum(1 for tag, _ in items if tag == "🟢")
deep_count = sum(1 for tag, _ in items if tag == "🔴")
total_papers = len(items)

assert total_papers == 30, f"Expected 30 papers, got {total_papers}"
assert skim_count == 19, f"Expected 19 skim papers, got {skim_count}"
assert deep_count == 11, f"Expected 11 deep papers, got {deep_count}"

# 默认参数：线性硬啃 4.0h/篇，Pass 2 略读 0.5h/篇，Pass 3 精读 2.0h/篇，每周预算 2.5h
t_linear = 4.0
t_skim = 0.5
t_deep = 2.0
weekly_budget = 2.5

linear_hours = total_papers * t_linear
skim_total_hours = skim_count * t_skim
deep_total_hours = deep_count * t_deep
tiered_hours = skim_total_hours + deep_total_hours
saved_hours = linear_hours - tiered_hours
saved_pct = (saved_hours / linear_hours) * 100.0
linear_weeks = linear_hours / weekly_budget
tiered_weeks = tiered_hours / weekly_budget

# 顺带校验 W03 Attention 缩放点积方差推导：d_k = 64 时未缩放标准差为 sqrt(64) = 8.0
dk_demo = 64
unscaled_std = math.sqrt(dk_demo)
assert abs(unscaled_std - 8.0) < 1e-12

golden = {
    "total_papers": total_papers,
    "skim_count": skim_count,
    "deep_count": deep_count,
    "default_skim_hours": round(skim_total_hours, 6),
    "default_deep_hours": round(deep_total_hours, 6),
    "default_linear_hours": round(linear_hours, 6),
    "default_tiered_hours": round(tiered_hours, 6),
    "default_saved_hours": round(saved_hours, 6),
    "default_saved_pct": round(saved_pct, 6),
    "default_linear_weeks": round(linear_weeks, 6),
    "default_tiered_weeks": round(tiered_weeks, 6),
    "attn_dk64_std": round(unscaled_std, 6),
}
print(json.dumps(golden, ensure_ascii=False))
