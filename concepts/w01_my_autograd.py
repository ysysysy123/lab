#!/usr/bin/env python3
"""
w01_my_autograd.py — W01 盲写挑战：手搓标量自动微分 + ReLU / Exp
运行自测: python3 concepts/w01_my_autograd.py

通关要求：不翻看 w01_micro_autograd.py，补全下方 5 处 TODO(human)，跑通底部全部 assert！
"""

from __future__ import annotations
import math


class Value:
    """标量节点：data 存前向值 (float)，grad 存反向梯度 ∂L/∂self (float)"""

    def __init__(self, data: float, _children: tuple[Value, ...] = ()) -> None:
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    def __add__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward() -> None:
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        # # TODO(human): 1) 构造前向节点 out  2) 定义 _backward 累加 self.grad 与 other.grad
        # raise NotImplementedError
        out = Value(self.data * other.data, (self, other))
        def _backward() ->None:
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
            
        out._backward = _backward
        return out


    def relu(self) -> Value:
        # # TODO(human): 实现 ReLU(x) = max(0, x) 及其局部导数 (x > 0 时为 1，否则为 0)
        # raise NotImplementedError
        r=max(0,self.data)
        out = Value(r, (self,))
        
        def _backward() -> None:
            if r>0:
                self.grad += out.grad
        
        out._backward = _backward
        return out

    def exp(self) -> Value:
        e = math.exp(self.data)
        out = Value(e, (self,))

        def _backward() -> None:
            self.grad += out.data * out.grad

        out._backward = _backward
        return out

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

    def __neg__(self) -> Value: return self * -1.0
    def __sub__(self, other: Value | float) -> Value: return self + (-other)
    def __radd__(self, other: float) -> Value: return self + other
    def __rmul__(self, other: float) -> Value: return self * other


def test() -> None:
    # 测试 1：节点复用陷阱（检验是否用了 += 而不是 =）
    a = Value(3.0)
    y1 = a * a + a  # y1 = a^2 + a => dy1/da = 2a + 1 = 7.0
    y1.backward()
    assert abs(a.grad - 7.0) < 1e-6, f"节点复用梯度错误: 期望 7.0, 实际 {a.grad} (检查是否漏写 +=)"

    # 测试 2：复合计算图 + 数值差分检验 (Gradient Check)
    def f_scalar(w_val: float, x_val: float, b_val: float) -> float:
        z = max(0.0, w_val * x_val + b_val)
        return math.exp(z)

    w, x, b = Value(-1.5), Value(-0.8), Value(-0.2)
    loss = (w * x + b).relu().exp()
    loss.backward()

    eps = 1e-6
    num_dw = (f_scalar(-1.5 + eps, -0.8, -0.2) - f_scalar(-1.5 - eps, -0.8, -0.2)) / (2 * eps)
    assert abs(w.grad - num_dw) < 1e-5, f"dw 梯度不匹配: 解析 {w.grad:.6f} vs 数值 {num_dw:.6f}"
    print(f"✅ All checks passed! 解析梯度 dw={w.grad:.6f}, 数值梯度 dw={num_dw:.6f}")


if __name__ == "__main__":
    test()
