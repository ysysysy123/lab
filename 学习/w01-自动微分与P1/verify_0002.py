#!/usr/bin/env python3
"""Lesson 0002 金标准验证脚本：校验 Sigmoid 饱和对比、3 类 Softmax+CE 手算算例、数值差分与 PyTorch autograd"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_DIR))

import importlib.util
import numpy as np
import torch
import torch.nn.functional as F

# 直接加载真实源码 projects/p1-tiny-llm/src/w01_mlp_mnist.py 中的 NumpyMLP.softmax
spec = importlib.util.spec_from_file_location(
    "w01_mlp_mnist", LAB_DIR / "projects/p1-tiny-llm/src/w01_mlp_mnist.py"
)
assert spec and spec.loader
mlp_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlp_mod)
NumpyMLP = mlp_mod.NumpyMLP


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))


# 1. §1 痛点对比：真实标签 y = 1，预测错得离谱 z = -5.0 时 Sigmoid+MSE vs Sigmoid+BCE
z_bad = -5.0
y_bin = 1.0
sig_bad = sigmoid(z_bad)
sig_deriv_bad = sig_bad * (1.0 - sig_bad)
# L_MSE = 0.5 * (sigma(z) - y)^2  =>  dL/dz = (sigma - y) * sigma * (1 - sigma)
mse_loss_bad = 0.5 * (sig_bad - y_bin) ** 2
mse_grad_bad = (sig_bad - y_bin) * sig_deriv_bad
# L_BCE = -(y * ln(sigma) + (1-y) * ln(1-sigma))  =>  dL/dz = sigma - y
bce_loss_bad = -math.log(sig_bad)
bce_grad_bad = sig_bad - y_bin
grad_ratio_bad = abs(bce_grad_bad / mse_grad_bad)

# PyTorch 校验 §1
zt = torch.tensor(z_bad, dtype=torch.float64, requires_grad=True)
st = torch.sigmoid(zt)
(0.5 * (st - y_bin) ** 2).backward()
assert abs(zt.grad.item() - mse_grad_bad) < 1e-12

zt2 = torch.tensor(z_bad, dtype=torch.float64, requires_grad=True)
F.binary_cross_entropy_with_logits(zt2, torch.tensor(y_bin, dtype=torch.float64)).backward()
assert abs(zt2.grad.item() - bce_grad_bad) < 1e-12

# 对比 z = 0.0 (轻度不确定点)
sig_0 = sigmoid(0.0)
mse_grad_0 = (sig_0 - y_bin) * sig_0 * (1.0 - sig_0)  # -0.125
bce_grad_0 = sig_0 - y_bin                            # -0.5

# 2. §2 3 类极小具体数字算例：z = [2.0, 1.0, -1.0], y = 0
z_np = np.array([[2.0, 1.0, -1.0]], dtype=np.float64)
y_cls = 0
exp_raw = np.exp(z_np[0])
sum_exp_raw = float(np.sum(exp_raw))

# 调用真实源码 NumpyMLP.softmax（内部先减 max 防溢出）
p_np = NumpyMLP.softmax(z_np)[0]
onehot = np.array([1.0, 0.0, 0.0], dtype=np.float64)
ce_loss = float(-np.log(p_np[y_cls]))
ce_loss_lse = float(np.log(np.sum(np.exp(z_np[0]))) - z_np[0, y_cls])
assert abs(ce_loss - ce_loss_lse) < 1e-12

grad_z = p_np - onehot
assert abs(float(np.sum(grad_z))) < 1e-15

# PyTorch autograd 校验 3 类算例
z_t = torch.tensor([[2.0, 1.0, -1.0]], dtype=torch.float64, requires_grad=True)
loss_t = F.cross_entropy(z_t, torch.tensor([y_cls], dtype=torch.long))
loss_t.backward()
assert abs(loss_t.item() - ce_loss) < 1e-12
assert np.allclose(z_t.grad.numpy()[0], grad_z, atol=1e-12)

# 中心差分数值梯度校验
eps = 1e-6
num_grad_z = np.zeros(3, dtype=np.float64)
for i in range(3):
    zp = z_np.copy()
    zm = z_np.copy()
    zp[0, i] += eps
    zm[0, i] -= eps
    lp = -math.log(NumpyMLP.softmax(zp)[0, y_cls])
    lm = -math.log(NumpyMLP.softmax(zm)[0, y_cls])
    num_grad_z[i] = (lp - lm) / (2.0 * eps)
assert np.allclose(grad_z, num_grad_z, atol=1e-9)

# 一步 SGD 更新效果（eta = 0.5）
eta = 0.5
z_after = z_np - eta * grad_z.reshape(1, -1)
p_after = NumpyMLP.softmax(z_after)[0]
loss_after = float(-np.log(p_after[y_cls]))
assert loss_after < ce_loss and p_after[y_cls] > p_np[y_cls]

# 3. §7 标签平滑（Label Smoothing, eps_ls = 0.1, K = 3, y = 0）校验
eps_ls = 0.1
K = 3
y_smooth = (1.0 - eps_ls) * onehot + eps_ls / K
grad_smooth = p_np - y_smooth
z_ts = torch.tensor([[2.0, 1.0, -1.0]], dtype=torch.float64, requires_grad=True)
loss_ts = F.cross_entropy(z_ts, torch.tensor([y_cls], dtype=torch.long), label_smoothing=eps_ls)
loss_ts.backward()
assert np.allclose(z_ts.grad.numpy()[0], grad_smooth, atol=1e-12)

golden = {
    "bad_z": z_bad,
    "bad_sig": round(sig_bad, 8),
    "bad_sig_deriv": round(sig_deriv_bad, 8),
    "bad_mse_loss": round(mse_loss_bad, 8),
    "bad_mse_grad": round(mse_grad_bad, 8),
    "bad_bce_loss": round(bce_loss_bad, 8),
    "bad_bce_grad": round(bce_grad_bad, 8),
    "bad_grad_ratio": round(grad_ratio_bad, 4),
    "zero_mse_grad": round(mse_grad_0, 8),
    "zero_bce_grad": round(bce_grad_0, 8),
    "ex_z": [2.0, 1.0, -1.0],
    "ex_exp": [round(float(v), 8) for v in exp_raw],
    "ex_sum_exp": round(sum_exp_raw, 8),
    "ex_p": [round(float(v), 8) for v in p_np],
    "ex_loss": round(ce_loss, 8),
    "ex_gz": [round(float(v), 8) for v in grad_z],
    "ex_num_gz": [round(float(v), 8) for v in num_grad_z],
    "ex_gz_sum": round(float(np.sum(grad_z)), 12),
    "sgd_z_after": [round(float(v), 8) for v in z_after[0]],
    "sgd_p_after": [round(float(v), 8) for v in p_after],
    "sgd_loss_after": round(loss_after, 8),
    "ls_target": [round(float(v), 8) for v in y_smooth],
    "ls_gz": [round(float(v), 8) for v in grad_smooth],
    "ls_loss": round(float(loss_ts.item()), 8),
}
print(json.dumps(golden, ensure_ascii=False))
