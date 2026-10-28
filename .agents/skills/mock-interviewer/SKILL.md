---
name: mock-interviewer
description: >-
  Conducts a realistic 27-grad AI/LLM/Agent/Embodied internship mock interview
  strictly scoped to topics and projects the user has already completed, probing
  three layers deep. Use when the user asks for a mock interview, quiz, or
  resume project defense.
---

# Mock Interviewer Skill (27 届实习三层追问模拟面)

## Workflow

1. **Scope Check (严禁超纲打击信心)**
   - Run `python3 study.py status` and inspect `[x]` items in [ROADMAP_16W.md](../../../ROADMAP_16W.md), [READING_LIST.md](../../../papers/READING_LIST.md), and completed tables in `projects/`.
   - Only ask questions covering `[x]` topics or projects currently in progress.
2. **Run a 3-Layer Progressive Grill (One Question per Turn!)**
   - Never dump 10 questions at once. Ask **one** question, wait for the user's answer, then probe deeper:
     - **Layer 1 (原理直觉 + 核心公式)**: What is it and why does it work?
     - **Layer 2 (工程细节 + 对比取舍)**: Why choose X over Y in your project? How much VRAM / latency does it cost?
     - **Layer 3 (极端失效 + 排查思路)**: If loss spikes / reward hacks / robot grasps air, how do you diagnose and fix it?
3. **Post-Interview Actionable Feedback**
   - Score clarity (`STAR` structure), formula accuracy, and engineering depth.
   - Log any 🔴 weak spots into [interview_log.md](../../../career/interview_log.md) with a concrete follow-up action.

