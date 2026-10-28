#!/usr/bin/env python3
"""
w01_micro_autograd.py — 零第三方依赖！50 行核心代码看懂神经网络是怎么「学习」的
运行方式: python3 concepts/w01_micro_autograd.py

学习任务（W01-W02）：
1. 直接运行本文件，观察 Loss 从 ~4.0 一路降到 < 0.001。
2. 读懂 Value._backward 里的链式法则（local_grad * out.grad）。
3. 合上本文件，自己新建 my_autograd.py 独立默写一遍，并补上 exp() 或 relu()！
"""

from __future__ import annotations

import math
import random


class Value:
    """标量计算图节点：记录前向数值 data、反向梯度 grad 以及拓扑父节点"""

    def __init__(self, data: float, _children: tuple[Value, ...] = ()) -> None:
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    def __add__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward() -> None:
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward() -> None:
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __pow__(self, power: float) -> Value:
        out = Value(self.data**power, (self,))

        def _backward() -> None:
            self.grad += (power * (self.data ** (power - 1))) * out.grad

        out._backward = _backward
        return out

    def tanh(self) -> Value:
        t = math.tanh(self.data)
        out = Value(t, (self,))

        def _backward() -> None:
            self.grad += (1.0 - t * t) * out.grad

        out._backward = _backward
        return out

    def __neg__(self) -> Value:
        return self * -1.0

    def __sub__(self, other: Value | float) -> Value:
        return self + (-other)

    def __radd__(self, other: float) -> Value:
        return self + other

    def __rmul__(self, other: float) -> Value:
        return self * other

    def backward(self) -> None:
        topo: list[Value] = []
        visited: set[Value] = set()

        def build_topo(v: Value) -> None:
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)
        self.grad = 1.0
        for node in reversed(topo):
            node._backward()


def main() -> None:
    random.seed(42)

    # 1. 数值梯度检验 (Gradient Check)：验证链式法则实现 100% 正确
    x = Value(0.7)
    w = Value(-1.3)
    b = Value(0.2)
    y = (w * x + b).tanh()
    y.backward()

    eps = 1e-6
    num_grad_w = (math.tanh((-1.3 + eps) * 0.7 + 0.2) - math.tanh(-1.3 * 0.7 + 0.2)) / eps
    assert abs(w.grad - num_grad_w) < 1e-5, f"梯度不匹配: {w.grad} vs {num_grad_w}"
    print(f"✅ 数值梯度检验通过! 解析梯度 dw={w.grad:.6f}, 数值差分 dw={num_grad_w:.6f}")

    # 2. 用两层微型 MLP (2 -> 4 -> 1) 拟合非线性异或风格数据集
    xs = [[2.0, 3.0], [3.0, -1.0], [-1.0, 1.5], [1.0, 1.0]]
    ys = [1.0, -1.0, -1.0, 1.0]

    # 初始化参数: 隐藏层 4 个神经元 (每个 2 权重 + 1 偏置)，输出层 1 个神经元
    w1 = [[Value(random.uniform(-1, 1)) for _ in range(2)] for _ in range(4)]
    b1 = [Value(0.0) for _ in range(4)]
    w2 = [Value(random.uniform(-1, 1)) for _ in range(4)]
    b2 = Value(0.0)
    params = [p for row in w1 for p in row] + b1 + w2 + [b2]

    def forward(inp: list[float]) -> Value:
        h = [(w1[i][0] * inp[0] + w1[i][1] * inp[1] + b1[i]).tanh() for i in range(4)]
        out = sum((w2[i] * h[i] for i in range(4)), b2).tanh()
        return out

    lr = 0.1
    for step in range(81):
        preds = [forward(row) for row in xs]
        loss = sum(((pred - target) ** 2 for pred, target in zip(preds, ys)), Value(0.0))

        for p in params:
            p.grad = 0.0
        loss.backward()
        for p in params:
            p.data -= lr * p.grad

        if step % 20 == 0:
            print(f"  step {step:02d} | loss = {loss.data:.6f} | preds = {[round(p.data, 3) for p in preds]}")

    assert loss.data < 0.05, "训练未收敛"
    print("🎉 微型神经网络训练收敛！你已经跑通了深度学习最底层的发动机。")


if __name__ == "__main__":
    main()

