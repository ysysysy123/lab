#!/usr/bin/env python3
"""Lesson 0003 金标准验证脚本：2×2 批量 MLP 全链路矩阵数值、中心差分与 PyTorch autograd 校验"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_DIR))

import numpy as np
import torch
import torch.nn.functional as F

spec = importlib.util.spec_from_file_location(
    "w01_mlp_mnist", LAB_DIR / "projects/p1-tiny-llm/src/w01_mlp_mnist.py"
)
assert spec and spec.loader
mlp_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlp_mod)
NumpyMLP = mlp_mod.NumpyMLP

# 1. MNIST 真实规模参数统计 (784 -> 128 -> 10, B = 128)
mnist_w1_params = 784 * 128
mnist_b1_params = 128
mnist_w2_params = 128 * 10
mnist_b2_params = 10
mnist_total_params = mnist_w1_params + mnist_b1_params + mnist_w2_params + mnist_b2_params

# 2. 2×2 极小批量算例 (B=2, D=2, H=2, K=2)
X = np.array([[1.0, 0.5], [-0.5, 1.0]], dtype=np.float64)
y = np.array([0, 1], dtype=np.int64)
Y = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float64)

W1_0 = np.array([[0.4, -0.6], [0.8, 0.5]], dtype=np.float64)
b1_0 = np.array([[0.1, 0.2]], dtype=np.float64)
W2_0 = np.array([[0.5, -0.3], [-0.4, 0.6]], dtype=np.float64)
b2_0 = np.array([[0.0, 0.1]], dtype=np.float64)

B = X.shape[0]
Z1 = X @ W1_0 + b1_0
A1 = np.maximum(0.0, Z1)
Z2 = A1 @ W2_0 + b2_0
P = NumpyMLP.softmax(Z2)
loss = float(-np.mean(np.log(P[np.arange(B), y])))

# 解析反向传播（与 w01_mlp_mnist.py 第 102-109 行逐字一致）
dZ2 = (P - Y) / B
dW2 = A1.T @ dZ2
db2 = np.sum(dZ2, axis=0, keepdims=True)
dA1 = dZ2 @ W2_0.T
dZ1 = dA1 * (Z1 > 0)
dW1 = X.T @ dZ1
db1 = np.sum(dZ1, axis=0, keepdims=True)

# 3. 与真实 NumpyMLP.train_step 对照校验（更新后权重必须完全一致）
eta = 0.5
mlp = NumpyMLP(in_dim=2, hidden_dim=2, out_dim=2, lr=eta)
mlp.W1 = W1_0.copy()
mlp.b1 = b1_0.copy()
mlp.W2 = W2_0.copy()
mlp.b2 = b2_0.copy()
step_loss = mlp.train_step(X, y)
assert abs(step_loss - loss) < 1e-11
assert np.allclose(mlp.W1, W1_0 - eta * dW1, atol=1e-12)
assert np.allclose(mlp.b1, b1_0 - eta * db1, atol=1e-12)
assert np.allclose(mlp.W2, W2_0 - eta * dW2, atol=1e-12)
assert np.allclose(mlp.b2, b2_0 - eta * db2, atol=1e-12)

# 4. 与 PyTorch autograd 对照校验
Xt = torch.tensor(X, dtype=torch.float64)
yt = torch.tensor(y, dtype=torch.long)
W1t = torch.tensor(W1_0, dtype=torch.float64, requires_grad=True)
b1t = torch.tensor(b1_0, dtype=torch.float64, requires_grad=True)
W2t = torch.tensor(W2_0, dtype=torch.float64, requires_grad=True)
b2t = torch.tensor(b2_0, dtype=torch.float64, requires_grad=True)

Z1t = Xt @ W1t + b1t
Z1t.retain_grad()
A1t = torch.relu(Z1t)
A1t.retain_grad()
Z2t = A1t @ W2t + b2t
Z2t.retain_grad()
losst = F.cross_entropy(Z2t, yt)
losst.backward()

assert abs(losst.item() - loss) < 1e-12
assert np.allclose(Z2t.grad.numpy(), dZ2, atol=1e-12)
assert np.allclose(W2t.grad.numpy(), dW2, atol=1e-12)
assert np.allclose(b2t.grad.numpy(), db2, atol=1e-12)
assert np.allclose(A1t.grad.numpy(), dA1, atol=1e-12)
assert np.allclose(Z1t.grad.numpy(), dZ1, atol=1e-12)
assert np.allclose(W1t.grad.numpy(), dW1, atol=1e-12)
assert np.allclose(b1t.grad.numpy(), db1, atol=1e-12)

# 5. 中心差分数值梯度校验 dW1
def loss_given_w1(W1_cand: np.ndarray) -> float:
    z1 = X @ W1_cand + b1_0
    a1 = np.maximum(0.0, z1)
    z2 = a1 @ W2_0 + b2_0
    p = NumpyMLP.softmax(z2)
    return float(-np.mean(np.log(p[np.arange(B), y])))

eps = 1e-6
num_dW1 = np.zeros_like(W1_0)
for i in range(2):
    for j in range(2):
        Wp = W1_0.copy()
        Wm = W1_0.copy()
        Wp[i, j] += eps
        Wm[i, j] -= eps
        num_dW1[i, j] = (loss_given_w1(Wp) - loss_given_w1(Wm)) / (2.0 * eps)

assert np.allclose(dW1, num_dW1, atol=1e-9)

# 6. 连续 15 步 SGD 训练曲线（供交互实验默认参数对比校验）
mlp_curve = NumpyMLP(in_dim=2, hidden_dim=2, out_dim=2, lr=0.5)
mlp_curve.W1 = W1_0.copy()
mlp_curve.b1 = b1_0.copy()
mlp_curve.W2 = W2_0.copy()
mlp_curve.b2 = b2_0.copy()
loss_curve = []
for _ in range(15):
    z1_c, a1_c, z2_c, p_c = mlp_curve.forward(X)
    l_c = float(-np.mean(np.log(p_c[np.arange(B), y])))
    loss_curve.append(round(l_c, 8))
    dz2_c = (p_c - Y) / B
    dw2_c = a1_c.T @ dz2_c
    db2_c = np.sum(dz2_c, axis=0, keepdims=True)
    da1_c = dz2_c @ mlp_curve.W2.T
    dz1_c = da1_c * (z1_c > 0)
    dw1_c = X.T @ dz1_c
    db1_c = np.sum(dz1_c, axis=0, keepdims=True)
    mlp_curve.W2 -= 0.5 * dw2_c
    mlp_curve.b2 -= 0.5 * db2_c
    mlp_curve.W1 -= 0.5 * dw1_c
    mlp_curve.b1 -= 0.5 * db1_c

assert loss_curve[-1] < loss_curve[0] * 0.25

r8 = lambda M: [[round(float(v), 8) for v in row] for row in M]

golden = {
    "mnist_w1_mul": mnist_w1_params,
    "mnist_total_params": mnist_total_params,
    "X": r8(X),
    "W1": r8(W1_0),
    "b1": r8(b1_0),
    "W2": r8(W2_0),
    "b2": r8(b2_0),
    "Z1": r8(Z1),
    "A1": r8(A1),
    "Z2": r8(Z2),
    "P": r8(P),
    "loss": round(loss, 8),
    "dZ2": r8(dZ2),
    "dW2": r8(dW2),
    "db2": r8(db2),
    "dA1": r8(dA1),
    "dZ1": r8(dZ1),
    "dW1": r8(dW1),
    "db1": r8(db1),
    "num_dW1": r8(num_dW1),
    "sgd_losses_lr05": loss_curve,
    "sgd_loss_step14": loss_curve[-1],
}
print(json.dumps(golden, ensure_ascii=False))
