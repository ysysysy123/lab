# AI Lab 核心术语表（Glossary）

本表只收录**已学懂并能准确使用**的概念压缩定义；后续所有课程页、推导与速查表统一沿用此处术语与记号。

## 自动微分与反向传播

**计算图节点（`Value` / Computation Graph Node）**:
同时保存前向标量值 `data`、反向累积偏导 `grad`（即 $\frac{\partial L}{\partial v}$）、直接前驱集合 `_prev` 与单步局部回传闭包 `_backward` 的基本有向无环图单元。
_Avoid_: 普通浮点数变量（丢失运算历史，无法自动回传梯度）

**局部导数与上游梯度（Local Derivative & Upstream Gradient）**:
对运算 $u = f(v)$，局部导数是该算子自身在当前输入处的斜率 $\frac{\partial u}{\partial v}$，上游梯度是从损失终点一路回传到输出端的敏感度 $\frac{\partial L}{\partial u}$；反向传播单步永远只做一件事：`v.grad += local_grad * u.grad`。
_Avoid_: 把局部导数直接当成最终对 Loss 的梯度

**梯度累加（Gradient Accumulation across Branches, `+=`）**:
当同一节点 $v$ 被多条前向支路复用（如 $y = a \cdot a + a$ 或残差连接 $y = F(x) + x$）时，根据多元链式法则 $\frac{\partial L}{\partial v} = \sum_k \frac{\partial L}{\partial u_k}\frac{\partial u_k}{\partial v}$，各支路回传的梯度必须用 `+=` 相加而非 `=` 覆盖。
_Avoid_: 直接赋值 `self.grad = ...`

**逆拓扑序（Reverse Topological Order）**:
在有向无环计算图上通过 DFS 后序遍历得到拓扑序列并反转后的执行顺序，保证任意节点执行 `_backward()` 时，所有依赖它的下游节点都已经把梯度完整传回给了它。
_Avoid_: 按代码行顺序盲目回传、未去重的递归回传（指数级重复计算）

**中心差分梯度检验（Central Finite-Difference Check）**:
用 $\frac{f(w+\epsilon) - f(w-\epsilon)}{2\epsilon}$（通常取 $\epsilon = 10^{-6}$，截断误差 $O(\epsilon^2)$）独立估算偏导，用于校验手写解析反向传播是否写对的黄金标尺。
_Avoid_: 单侧差分用于高精度检验（误差仅 $O(\epsilon)$，在曲率大处易误报）
