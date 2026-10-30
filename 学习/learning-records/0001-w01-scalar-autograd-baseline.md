# 已掌握标量计算图前反向核心算子，下一步衔接批量矩阵 BP 与数值稳定 Softmax

已完成 3Blue1Brown 神经网络 1–4 集、PyTorch 60min Blitz，并在 concepts/w01_my_autograd.py 中亲手补全了 Value.__mul__、Value.relu 与 DFS 拓扑排序 backward()，通过了节点复用 (a*a+a) 与中心差分梯度检验。

**Evidence**: ROADMAP_16W.md W01 前 4 项已勾选 [x]；concepts/w01_my_autograd.py 全部 assert 通过。

**Implications**: 后续课程无需重讲标量导数定义；应把标量链式法则作为已知跳板，重点讲透三件事：(1) backward 三条铁律背后的图论/多元微积分直觉，(2) Softmax+交叉熵 p-y 化简与减 max 防溢出，(3) 从标量梯度跨越到 (B, D) 批量矩阵转置乘法的维度对齐法。

<!-- 2026-10-30 -->
