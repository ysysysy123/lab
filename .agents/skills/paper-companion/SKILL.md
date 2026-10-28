---
name: paper-companion
description: >-
  Co-reads academic papers in either 30-minute skim mode or 2-hour deep-read mode
  and populates lightweight structured cards in papers/. Use when the user wants
  to read, summarize, or discuss a paper from papers/READING_LIST.md.
---

# Paper Companion Skill (无痛论文陪读)

## Workflow

1. **Determine Tier (`--deep` vs `--skim`)**
   - Check [READING_LIST.md](../../../papers/READING_LIST.md) to see whether the paper is marked 🔴 (Deep, 2h) or 🟢 (Skim, 30m).
   - Scaffold the note file via `python3 study.py paper <slug> --deep` (or `--skim`).
2. **If 🟢 Skim Mode (30 min max)**
   - Focus strictly on 3 questions: (1) What broke before? (2) What is the single core trick in Figure 1? (3) One-sentence takeaway for interviews/projects.
   - Help fill `papers/<slug>.md` in under 15 lines and mark `[x]` in `papers/READING_LIST.md`.
3. **If 🔴 Deep Mode (2 hours)**
   - Walk interactively in 3 short turns instead of dumping a wall of text:
     1. **Architecture & Motivation**: Trace input-to-output tensor shapes.
     2. **Core Equation Derivation**: Derive the single key loss/objective step-by-step and map it to 15–20 lines of PyTorch pseudocode.
     3. **Interview Grill**: Ask the user 2 realistic interview follow-up questions; refine their answers and record them into `papers/<slug>.md`, then check `[x]` in `papers/READING_LIST.md`.

