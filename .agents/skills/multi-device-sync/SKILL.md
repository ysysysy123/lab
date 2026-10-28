---
name: multi-device-sync
description: >-
  Synchronizes study progress across local RTX 4080 laptop, remote A800 server,
  Colab, and Web AI by updating checkboxes, generating WEB_AI_BRIEF.md, and
  running safe git pull/push checks. Use at the start or end of a study session
  or when switching devices.
---

# Multi-Device Sync Skill (跨设备与网页 AI 交接同步)

## Session Start ("开机同步")

1. Check git & hardware environment:
   - Run `git status -s` and `git pull --rebase` (if `origin` remote is configured).
   - Identify device (`nvidia-smi` / `uname -n`) and remind the user of device-specific rules from [AGENTS.md](../../../AGENTS.md).
2. Run `python3 study.py status` and `python3 study.py today` to set today's focus.

## Session Wrap-Up ("收工交接")

1. Update `[x]` checkboxes in `ROADMAP_16W.md`, `papers/READING_LIST.md`, or `leetcode/hot100_tracker.md` for completed items.
2. Run `python3 study.py brief` to regenerate [WEB_AI_BRIEF.md](../../../WEB_AI_BRIEF.md) so Web AI / mobile sessions have up-to-date progress.
3. Safety check before `git add`:
   - Verify `git status -s` contains **no** API keys, `.env`, server IPs, or large `.pt`/`.safetensors` weights.
4. Commit with a clear prefix (`study(wXX): ...` or `feat(pX): ...`) and push to `origin` if configured.

