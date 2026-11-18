# W01 复习卡：标量自动微分 · 批量矩阵 BP · MNIST · ResNet

> **用法**：每天开始学习前运行 `python3 study.py review` 合上资料自测。  
> **规则**：这些是 AI 为你生成的初始草稿——复习时如果哪张卡觉得拗口或没记住，**直接用你自己的大白话改写 `A:`**（每张卡答案不超过 3 行）。

## Q: `Value.backward()` 缺一不可的「三条铁律」是什么？漏掉任意一条会发生什么？
A: ① 起点 `self.grad = 1.0`（$\partial L/\partial L = 1$，否则全图梯度为 0）；② 支路回传必须用 `+=` 累加（否则节点复用如 `a*a+a` 或残差支路会被后面的分支覆盖）；③ 按 DFS 逆拓扑序遍历（保证父节点回传前，所有下游支路的梯度都已汇齐）。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: 为什么中心差分 $\frac{f(x+h)-f(x-h)}{2h}$ 比单侧差分 $\frac{f(x+h)-f(x)}{h}$ 更适合做梯度检验？
A: 泰勒展开后，中心差分的二阶偶次项 $\pm \frac{1}{2}f''(x)h^2$ 刚好正负抵消，截断误差是 $O(h^2)$（取 $h=10^{-5}$ 精度即可达 $10^{-10}$）；单侧差分误差只有 $O(h)$，在曲率大处容易误报梯度错误。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: Softmax + 交叉熵损失对 logits $z_i$ 的合成梯度是什么？为什么分类不用 Sigmoid + MSE？
A: 合成梯度极简为 $\frac{\partial L}{\partial z_i} = p_i - y_i$（预测概率减真实 one-hot 标签）。如果用 Sigmoid + MSE，梯度会多乘一个 $\sigma'(z)=\sigma(1-\sigma)$，当模型严重猜错导致饱和时梯度反而趋近 0，学不动；而 $p - y$ 错得越离谱梯度越大。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: 为什么算 Softmax 或 Log-Sum-Exp 时必须先减去每行最大值 $m = \max_j z_j$？
A: 因为分子分母同乘 $e^{-m}$ 不改变 Softmax 概率值（平移不变性），但把最大指数变成了 $e^0=1$，其余全 $\le 1$：既彻底消除了大整数 $e^{z_i}$ 的上溢（`inf`），又保证分母求和至少为 $1$ 不会下溢除零。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: 批量矩阵前向 $Z_2 = A_1 W_2 + b_2$（其中 $A_1:(B,H), W_2:(H,C), Z_2:(B,C)$），不用死背公式怎么秒推 `dW2`、`dA1`、`db2`？
A: 只看 Shape 对齐：`dZ2` 是 `(B,C)`，要凑出 `dW2:(H,C)` 只能消掉 `B` $\Rightarrow$ `dW2 = A1.T @ dZ2`；要凑出 `dA1:(B,H)` 只能消掉 `C` $\Rightarrow$ `dA1 = dZ2 @ W2.T`；偏置沿 batch 维求和 `db2 = dZ2.sum(axis=0)`。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: 在 `dW2 = A1.T @ dZ2` 中，矩阵乘法在维度 `B`（batch）上的内积求和在物理意义上对应什么？
A: 对应一个 mini-batch 内 $B$ 个样本对同一个权重参数 $W_2$ 产生的梯度贡献之和（如果在计算 `dZ2 = (P - Y) / B` 时已经除以了 $B$，那这个矩阵乘算出来的就正好是 batch 平均梯度）。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: ReLU 激活函数在反向传播时，局部导数怎么处理？写成矩阵代码是什么？
A: 前向大于 0 的位置斜率为 1（原样放行上游梯度），小于等于 0 的位置斜率为 0（截断梯度）；矩阵代码直接写掩码逐元素相乘：`dZ1 = dA1 * (Z1 > 0)`。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: 用 PyTorch 的 `nn.CrossEntropyLoss()` 时，模型最后一层能不能接 `Softmax`？为什么每步训练前要调 `optimizer.zero_grad()`？
A: ① **不能接 Softmax**，因为 `nn.CrossEntropyLoss` 内部已经融合了数值稳定的 `LogSoftmax + NLLLoss`，直接传原始 `logits` 即可；② PyTorch 默认对 `.grad` 做 `+=` 累加（方便梯度累积），不调 `zero_grad()` 会把上一批的旧梯度混进当前步。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: ResNet 论文里 56 层普通网络比 20 层网络在「训练集」上误差更高，这是过拟合吗？残差连接 $y = F(x) + x$ 怎么解决的？
A: **不是过拟合**（过拟合是训练误差低、测试误差高），而是深层网络的**退化问题（Degradation）**。加上恒等捷径 $+x$ 后，反向求导 $\frac{\partial L}{\partial x} = \frac{\partial L}{\partial y}(\frac{\partial F}{\partial x} + 1)$ 自带常数 $+1$ 梯度高速公路，上游梯度可无损直达浅层。
<!-- due: 2026-11-18 | interval: 1 -->

## Q: Keshav《How to Read a Paper》里「30 分钟略读」和「2 小时精读」分别看什么？
A: 🟢 **略读（第一遍）**只看 Title、Abstract、Introduction、小标题、Figure 1 和 Conclusion，用 3 句话搞清痛点与核心招数；🔴 **精读（第二/三遍）**重点手推核心公式、拆解架构图，并去开源代码里找到对应的 20 行实现。
<!-- due: 2026-11-18 | interval: 1 -->
