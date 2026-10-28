# 🧪 费曼盲写微实验区（`concepts/`）

> **这是让你彻底告别「看书犯困、学完就忘」的核心武器。**

## 运作规则（每次不超过 45 分钟）

1. 看完一节视频（如 Karpathy 讲 `micrograd`、Attention、BPE 或 RoPE）后，**关掉视频和网页，绝不摘抄大段文字笔记**。
2. 在本目录新建一个单文件脚本（不超过 80 行），例如：
   - `w01_micro_autograd.py`（标量反向传播链式法则，已提供可直接运行！）
   - `w03_causal_self_attention.py`（手写 $QK^T/\sqrt{d_k}$ + 下三角掩码）
   - `w05_rope_rotation.py`（验证旋转位置编码的相对位置内积不变性）
   - `w07_dpo_loss.py`（15 行写清 DPO Loss 并验证 chosen/rejected 梯度方向）
   - `w09_grpo_advantage.py`（15 行写清组内归一化优势与 KL 惩罚）
3. 在文件末尾写 2 个 `assert`（例如与 PyTorch 官方函数对比误差 `< 1e-5`，或者在小玩具数据上观察 Loss 从 `>1.0` 降到 `<0.01`）。
4. 跑通显示 `✅ All checks passed!` 即宣告该知识点彻底拿下，面试手撕代码题也顺带练完了！

