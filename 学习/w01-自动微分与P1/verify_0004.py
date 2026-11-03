#!/usr/bin/env python3
"""Lesson 0004 金标准验证脚本：用 NumPy 与 PyTorch 双重校验 Log-Sum-Exp 与上下溢边界"""
from __future__ import annotations

import json
import math

import numpy as np
import torch
import torch.nn.functional as F

# 1. 各浮点格式 exp 上溢阈值 ln(MAX_FLOAT)
fp64_max_z = float(np.log(np.finfo(np.float64).max))
fp32_max_z = float(np.log(np.finfo(np.float32).max))
fp16_max_z = float(np.log(np.finfo(np.float16).max))
bf16_max_z = math.log(float(torch.finfo(torch.bfloat16).max))

with np.errstate(over="ignore"):
    assert math.isinf(float(np.exp(np.float64(710.0))))
    assert math.isinf(float(np.exp(np.float32(89.0))))
    assert math.isinf(float(np.exp(np.float16(12.0))))
assert not math.isinf(float(torch.exp(torch.tensor(88.0, dtype=torch.bfloat16)).item()))

# 2. §1 下溢算例：z = [0.0, -2.0, -1000.0], y = 2
z_under = np.array([0.0, -2.0, -1000.0], dtype=np.float64)
shift_under = z_under - np.max(z_under)
p_under = np.exp(shift_under) / np.sum(np.exp(shift_under))
assert p_under[2] == 0.0  # IEEE 754 float64 下精确下溢为 0.0
eps_clamp_loss = float(-np.log(p_under[2] + 1e-12))
under_true_loss = float(
    F.cross_entropy(
        torch.from_numpy(z_under[None, :]),
        torch.tensor([2], dtype=torch.long),
    ).item()
)
assert abs(under_true_loss - (1000.0 + math.log(1.0 + math.exp(-2.0)))) < 1e-12

# 3. §2 核心推导算例：z = [1000.0, 999.0, 995.0], y = 2
z_ex_list = [1000.0, 999.0, 995.0]
y_ex = 2
zt = torch.tensor([z_ex_list], dtype=torch.float64, requires_grad=True)
yt = torch.tensor([y_ex], dtype=torch.long)
loss_torch = F.cross_entropy(zt, yt)
loss_torch.backward()

m_ex = max(z_ex_list)
sum_exp_ex = sum(math.exp(v - m_ex) for v in z_ex_list)
loss_manual = m_ex - z_ex_list[y_ex] + math.log(sum_exp_ex)
probs_manual = [math.exp(v - m_ex) / sum_exp_ex for v in z_ex_list]
grad_manual = [probs_manual[i] - (1.0 if i == y_ex else 0.0) for i in range(3)]

assert abs(loss_manual - loss_torch.item()) < 1e-12
for i in range(3):
    assert abs(grad_manual[i] - float(zt.grad[0, i].item())) < 1e-12

# 4. §3 误加 nn.Softmax 导致 10 分类损失锁死下界 ln(e + 9) - 1
p_onehot = torch.zeros((1, 10), dtype=torch.float64)
p_onehot[0, 0] = 1.0
double_softmax_min_loss = float(F.cross_entropy(p_onehot, torch.tensor([0])).item())
assert abs(double_softmax_min_loss - (math.log(math.e + 9.0) - 1.0)) < 1e-12

# 5. §4 交互实验金标准点：z(k) = k * [1.0, 0.8, -0.5], y = 2
base_v = [1.0, 0.8, -0.5]


def lse_ce(k: float, y: int = 2) -> float:
    zk = torch.tensor([[k * x for x in base_v]], dtype=torch.float64)
    return float(F.cross_entropy(zk, torch.tensor([y], dtype=torch.long)).item())


def naive_eps_ce(k: float, y: int = 2, eps: float = 1e-12) -> float:
    """朴素交叉熵 -sum_j y_j log(p_j + eps)：当 k > 709.78 时 p_0 = inf/inf = NaN，0*NaN 传染整式为 NaN"""
    with np.errstate(over="ignore", invalid="ignore"):
        zk = np.array([k * x for x in base_v], dtype=np.float64)
        ez = np.exp(zk)
        pk = ez / np.sum(ez)
        onehot = np.zeros_like(pk)
        onehot[y] = 1.0
        return float(-np.sum(onehot * np.log(pk + eps)))


pg_k1_lse = lse_ce(1.0, 2)
pg_k1_naive_eps = naive_eps_ce(1.0, 2)
pg_k100_lse = lse_ce(100.0, 2)
pg_k100_naive_eps = naive_eps_ce(100.0, 2)
pg_k800_lse = lse_ce(800.0, 2)
assert math.isnan(naive_eps_ce(800.0, 2))  # k > 709.78 时朴素法必为 NaN

golden = {
    "fp64_max_z": round(fp64_max_z, 6),
    "fp32_max_z": round(fp32_max_z, 6),
    "bf16_max_z": round(bf16_max_z, 6),
    "fp16_max_z": round(fp16_max_z, 6),
    "eps_clamp_loss": round(eps_clamp_loss, 8),
    "under_true_loss": round(under_true_loss, 8),
    "ex_sum_exp": round(sum_exp_ex, 8),
    "ex_lse_loss": round(loss_manual, 8),
    "ex_probs": [round(p, 8) for p in probs_manual],
    "ex_grad_z": [round(g, 8) for g in grad_manual],
    "double_softmax_min_loss": round(double_softmax_min_loss, 8),
    "pg_k1_lse": round(pg_k1_lse, 8),
    "pg_k1_naive_eps": round(pg_k1_naive_eps, 8),
    "pg_k100_lse": round(pg_k100_lse, 8),
    "pg_k100_naive_eps": round(pg_k100_naive_eps, 8),
    "pg_k800_lse": round(pg_k800_lse, 8),
}
print(json.dumps(golden, ensure_ascii=False))
