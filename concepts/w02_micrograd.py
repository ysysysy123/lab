#!/usr/bin/env python3
"""
w02_micrograd.py — W02 盲写挑战：tanh、pow 与中心差分数值梯度检验
运行自测: python3 concepts/w02_micrograd.py

通关要求：独立补全 3 处 TODO(human)，跑通底部全部 assert！
"""

from __future__ import annotations
import math


class Value:
    def __init__(self, data: float, _children: tuple[Value, ...] = ()) -> None:
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    def __repr__(self) -> str:
        return f"Value(data={self.data:.4f}, grad={self.grad:.4f})"

    def __add__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def tanh(self) -> Value:
        """
        # TODO(human): 1. 实现 tanh 算子
        前向: t = (exp(2x) - 1) / (exp(2x) + 1)  (可用 math.tanh(self.data))
        反向: d(tanh(x))/dx = 1 - tanh(x)^2 = 1 - t^2
        别忘了多路梯度累加: self.grad += ...
        """
        raise NotImplementedError

    def __pow__(self, other: int | float) -> Value:
        """
        # TODO(human): 2. 实现标量幂运算 x^c (other 为 int 或 float，不参与求导)
        前向: out = self.data ** other
        反向: d(x^c)/dx = c * x^(c-1)
        """
        assert isinstance(other, (int, float)), "只支持 int/float 幂"
        raise NotImplementedError

    def __neg__(self) -> Value:
        return self * -1.0

    def __sub__(self, other: Value | float) -> Value:
        return self + (-other)

    def __truediv__(self, other: Value | float) -> Value:
        return self * (other**-1)

    def backward(self) -> None:
        topo: list[Value] = []
        visited: set[Value] = set()

        def dfs(v: Value):
            if v not in visited:
                visited.add(v)
                for p in v._prev:
                    dfs(p)
                topo.append(v)

        dfs(self)
        self.grad = 1.0
        for v in reversed(topo):
            v._backward()


def numerical_grad(f, x: float, h: float = 1e-5) -> float:
    """
    # TODO(human): 3. 实现中心差分数值梯度检验 (Central Finite Difference)
    公式: (f(x + h) - f(x - h)) / (2 * h)
    """
    raise NotImplementedError


# =====================================================================
# 单元测试（写完后运行 python3 concepts/w02_micrograd.py 自测）
# =====================================================================
if __name__ == "__main__":
    print("⏳ 开始微型算子验证...")

    # 1. 验证 tanh
    x1 = Value(0.5)
    y1 = x1.tanh()
    y1.backward()
    expected_tanh_grad = 1.0 - math.tanh(0.5) ** 2
    assert abs(x1.grad - expected_tanh_grad) < 1e-6, f"tanh 梯度错误: 得到 {x1.grad}, 期望 {expected_tanh_grad}"
    print("  ✓ Value.tanh() 前向与反向通过！")

    # 2. 验证 __pow__ 与复合除法 (a / b)
    a = Value(3.0)
    b = Value(2.0)
    c = a / b  # 内部转化为 a * (b ** -1)
    c.backward()
    assert abs(a.grad - 0.5) < 1e-6, f"除法分子梯度错误: {a.grad}"
    assert abs(b.grad - (-3.0 / 4.0)) < 1e-6, f"除法分母梯度错误: {b.grad}"
    print("  ✓ Value.__pow__() 与除法复合通过！")

    # 3. 验证中心差分数值梯度与复合计算图
    def complex_fn(val: float) -> float:
        # y = tanh(val^2 + 2*val)
        return math.tanh(val**2 + 2.0 * val)

    x_val = 0.8
    num_g = numerical_grad(complex_fn, x_val)

    # 用计算图算解析梯度
    x_node = Value(x_val)
    out_node = (x_node**2 + x_node * 2.0).tanh()
    out_node.backward()

    rel_error = abs(out_node.data - complex_fn(x_val))
    assert rel_error < 1e-6, f"前向值不一致: {out_node.data} vs {complex_fn(x_val)}"

    grad_diff = abs(x_node.grad - num_g)
    assert grad_diff < 1e-5, f"解析梯度与数值梯度不符: 解析={x_node.grad}, 数值={num_g}, 误差={grad_diff}"
    print(f"  ✓ 中心差分检验通过！解析梯度={x_node.grad:.6f}, 数值梯度={num_g:.6f}, 差值={grad_diff:.2e}")

    print("\n🎉 恭喜！W02 micrograd 核心算子全部手撕通关！")
