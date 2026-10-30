#!/usr/bin/env python3
"""Lesson 0001 金标准验证脚本：同时用 w01_micro_autograd.Value 与 PyTorch 校验全部算例"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_DIR))

import torch
from concepts.w01_micro_autograd import Value

# 1. 单神经元链式法则算例（来自 concepts/w01_micro_autograd.py）
x = Value(0.7)
w = Value(-1.3)
b = Value(0.2)
u = w * x
z = u + b
y = z.tanh()
y.backward()

xt = torch.tensor(0.7, dtype=torch.float64, requires_grad=True)
wt = torch.tensor(-1.3, dtype=torch.float64, requires_grad=True)
bt = torch.tensor(0.2, dtype=torch.float64, requires_grad=True)
yt = torch.tanh(wt * xt + bt)
yt.backward()

assert abs(y.data - yt.item()) < 1e-12
assert abs(w.grad - wt.grad.item()) < 1e-12
assert abs(x.grad - xt.grad.item()) < 1e-12
assert abs(b.grad - bt.grad.item()) < 1e-12

eps = 1e-6
num_dw = (((Value(-1.3 + eps) * 0.7 + 0.2).tanh().data) - ((Value(-1.3 - eps) * 0.7 + 0.2).tanh().data)) / (2 * eps)
assert abs(w.grad - num_dw) < 1e-9

# 2. 节点复用算例（来自 concepts/w01_my_autograd.py: y1 = a * a + a, a = 3.0）
a = Value(3.0)
y_reuse = a * a + a
y_reuse.backward()
assert abs(a.grad - 7.0) < 1e-12

# 3. 逆拓扑序反例（b = a + 1, c = 2 * b, L = b + c, a = 2.0）
a2 = Value(2.0)
b2 = a2 + 1.0
c2 = b2 * 2.0
L2 = b2 + c2
L2.backward()
assert abs(L2.data - 9.0) < 1e-12
assert abs(b2.grad - 3.0) < 1e-12
assert abs(a2.grad - 3.0) < 1e-12

golden = {
    "neuron_u": round(u.data, 8),
    "neuron_z": round(z.data, 8),
    "neuron_y": round(y.data, 8),
    "neuron_dz": round(z.grad, 8),
    "neuron_dw": round(w.grad, 8),
    "neuron_dx": round(x.grad, 8),
    "neuron_db": round(b.grad, 8),
    "neuron_num_dw": round(num_dw, 8),
    "reuse_y": round(y_reuse.data, 8),
    "reuse_da": round(a.grad, 8),
    "topo_L": round(L2.data, 8),
    "topo_db": round(b2.grad, 8),
    "topo_da_correct": round(a2.grad, 8),
    "topo_da_wrong_order": 1.0,
}
print(json.dumps(golden, ensure_ascii=False))
