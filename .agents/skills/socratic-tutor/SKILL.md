---
name: socratic-tutor
description: >-
  Creates <80-line blind-writing coding challenges (# TODO(human) + deterministic
  asserts and numerical gradient checks) in concepts/ without giving away full
  solutions. Use ONLY when the user explicitly asks to practice/blind-write
  ("练一下", "盲写", "出个练习") or works directly inside concepts/; for general
  course learning, derivations, code walkthroughs, and HTML notes, use lab-teach instead.
---

# Socratic Tutor Skill (费曼直觉与盲写教练)

## Workflow

1. **Locate Reference (Optional, Main Laptop Only)**
   - If `../04-LLM大模型` exists locally and exact notation helps, run:
     `python3 study.py dict <keyword> --limit 3`
2. **Step 1: Pain-Point First (不超过 3 句话)**
   - Explain *what failure mode of the previous method* this concept fixes (e.g., why divide by $\sqrt{d_k}$? Why use DPO instead of PPO? Why add $\lambda^2 I$ in Jacobian IK?).
3. **Step 2: 2×2 Concrete Numerical Walkthrough**
   - Avoid abstract $B \times H \times L \times D$ walls of symbols first. Walk through a tiny concrete numerical example (e.g., 2 tokens, dim 2) so the user sees actual numbers transforming.
4. **Step 3: Create a Blind-Write Challenge in `concepts/`**
   - Create a `<80` line starter script in `concepts/` containing ONLY:
     - Clear input/output shape docstrings
     - `# TODO(human): implement core 15-25 lines here`
     - Deterministic `assert` unit tests / numerical gradient checks at the bottom
   - Wait for the user to fill in the `# TODO(human)` block, then run the script and review edge cases together.

