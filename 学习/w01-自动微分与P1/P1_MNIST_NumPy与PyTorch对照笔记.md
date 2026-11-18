# P1 实战笔记：NumPy 手写矩阵反向传播 vs PyTorch GPU 对照

> **源码位置**：[`projects/p1-tiny-llm/src/w01_mlp_mnist.py`](file:///mnt/study/github/autumn-recruitment/lab/projects/p1-tiny-llm/src/w01_mlp_mnist.py)  
> **实验记录**：[`projects/p1-tiny-llm/results/mnist-2026-11-05/README.md`](file:///mnt/study/github/autumn-recruitment/lab/projects/p1-tiny-llm/results/mnist-2026-11-05/README.md)  
> **前置知识**：标量链式法则、Softmax 交叉熵梯度 $p - y$、Log-Sum-Exp 平移不变性

---

## 1. 核心实验现象与结论：为什么两者能「严丝合缝」？

在 2026-11-05 完成的严格对照实验中（相同种子 42、初始权重数值对齐、batch size 128、学习率 0.1、SGD 训练 10 轮），实验指标表现出惊人的一致性：

| 模型方案 | 训练硬件与精度 | 第 1 轮训练损失 | 第 10 轮训练损失 | 测试集准确率 (10k 样本) |
|---|---|---|---|---|
| **Softmax 逻辑回归 (NumPy)** | CPU (float64) | 0.36868 | 0.26642 | **92.26%** |
| **Softmax 逻辑回归 (PyTorch)**| GPU (BF16 autocast) | 0.36868 | 0.26645 | **92.28%** |
| **两层 MLP 784→128→10 (NumPy)** | CPU (float64) | 0.29058 | 0.03044 | **97.73%** |
| **两层 MLP 784→128→10 (PyTorch)**| GPU (BF16 autocast) | 0.29105 | 0.03051 | **97.71%** |

### 关键认知与破局点
1. **数学等价性得到完全验证**：
   - NumPy 手写梯度与 PyTorch 的 C++/CUDA 自动微分算子在第 1 轮损失前 4 位小数完全相同（`0.36868`），第 10 轮最终损失相差小于 $0.0001$。
   - 证明了手写的 **7 行矩阵反向传播** 在数学推导、Batch 维度求和归一化、以及 Softmax+交叉熵解析梯度上 100% 正确。
2. **线性分类器 vs 深度非线性网络的鸿沟**：
   - 逻辑回归（单层线性变换）无论怎么调参，MNIST 上限被锁死在 **92.2%**，因为手写数字在像素空间不是线性可分的。
   - 两层 MLP 仅加入一层 128 维隐藏层与 ReLU 激活，准确率直接跨过 **97.7%**，训练损失从 0.26 下探到 0.03。

---

## 2. 源码逐行精析：NumPy 手撕 7 行矩阵反向传播

在 [`NumpyMLP`](file:///mnt/study/github/autumn-recruitment/lab/projects/p1-tiny-llm/src/w01_mlp_mnist.py#L85-L156) 中，前向与反向传播的纯数学实现如下：

### 2.1 张量形状追踪表（Shape Alignment）

| 变量名 | 物理意义 | 数学公式 | 张量维度 (Batch=128) |
|---|---|---|---|
| `X` | 批次输入图像 | $X$ | `(128, 784)` |
| `W1, b1` | 隐层权重与偏置 | $W_1, b_1$ | `(784, 128)`, `(1, 128)` |
| `Z1` | 隐层线性输出 | $Z_1 = X W_1 + b_1$ | `(128, 128)` |
| `A1` | 隐层激活输出 (ReLU)| $A_1 = \max(0, Z_1)$ | `(128, 128)` |
| `W2, b2` | 输出层权重与偏置 | $W_2, b_2$ | `(128, 10)`, `(1, 10)` |
| `Z2` | 输出层原始分数 (Logits) | $Z_2 = A_1 W_2 + b_2$ | `(128, 10)` |
| `P` | Softmax 预测概率分布 | $P = \operatorname{softmax}(Z_2)$ | `(128, 10)` |
| `Y` | One-Hot 真实标签 | $Y$ | `(128, 10)` |

---

### 2.2 核心代码：7 行反向传播（无需死记，靠 Shape 倒推）

```python
# projects/p1-tiny-llm/src/w01_mlp_mnist.py 第 128–143 行
def train_step(self, X: np.ndarray, y: np.ndarray) -> float:
    B = X.shape[0]
    Z1, A1, Z2, P = self.forward(X)

    # 1. 计算交叉熵损失（数值稳定 Log-Sum-Exp）
    loss = cross_entropy(Z2, y)

    # 2. 构造 One-Hot 标签 Y
    Y = np.zeros_like(P)
    Y[np.arange(B), y] = 1.0

    # ================= 7 行核心反向传播开始 =================
    # ① 输出层误差梯度：由第 2 课推导的 Softmax+CE 灵魂结论 dL/dZ2 = (P - Y) / B
    dZ2 = (P - Y) / B                       # Shape: (B, 10)

    # ② 输出层权重梯度：前向是 A1 @ W2，W2 维度是 (128, 10)
    #    所以必须是 (128, B) @ (B, 10) -> A1.T @ dZ2
    #    矩阵乘法自动完成了对 Batch 内部 128 个样本梯度的累加！
    dW2 = A1.T @ dZ2                        # Shape: (128, 10)

    # ③ 输出层偏置梯度：b2 对每个样本共享广播，反向时沿 Batch 维求和
    db2 = np.sum(dZ2, axis=0, keepdims=True)# Shape: (1, 10)

    # ④ 误差回传到隐层激活：前向是 Z2 = A1 @ W2，A1 维度是 (B, 128)
    #    所以必须是 (B, 10) @ (10, 128) -> dZ2 @ W2.T
    dA1 = dZ2 @ self.W2.T                   # Shape: (B, 128)

    # ⑤ ReLU 导数门控：Z1 > 0 处梯度为 1，其余为 0
    dZ1 = dA1 * (Z1 > 0)                    # Shape: (B, 128)

    # ⑥ 隐层权重梯度：前向是 X @ W1，W1 维度是 (784, 128)
    #    所以必须是 (784, B) @ (B, 128) -> X.T @ dZ1
    dW1 = X.T @ dZ1                         # Shape: (784, 128)

    # ⑦ 隐层偏置梯度：沿 Batch 维求和
    db1 = np.sum(dZ1, axis=0, keepdims=True)# Shape: (1, 128)
    # ================= 7 行核心反向传播结束 =================

    # 3. 参数更新 (SGD)
    self.W2 -= self.lr * dW2
    self.b2 -= self.lr * db2
    self.W1 -= self.lr * dW1
    self.b1 -= self.lr * db1

    return loss
```

---

## 3. 源码逐行精析：PyTorch 工业级 GPU 五步闭环

在 [`run_torch`](file:///mnt/study/github/autumn-recruitment/lab/projects/p1-tiny-llm/src/w01_mlp_mnist.py#L217-L264) 中，展示了深度学习工业界的标准范式：

```python
# projects/p1-tiny-llm/src/w01_mlp_mnist.py 第 223–260 行
# 1. 模型定义：注意！最后一层绝不能接 nn.Softmax()！
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)

# 2. 初始权重对齐：nn.Linear 的内部存储权重是 (out_features, in_features)，即 W.T
with torch.no_grad():
    model[0].weight.copy_(torch.from_numpy(reference.W1.T))
    model[0].bias.copy_(torch.from_numpy(reference.b1.ravel()))
    model[2].weight.copy_(torch.from_numpy(reference.W2.T))
    model[2].bias.copy_(torch.from_numpy(reference.b2.ravel()))

model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=lr)

# 3. 标准训练循环（五步咒语）
for x, y in train_loader:
    x, y = x.to(device), y.to(device)

    # ① 清除历史梯度（防止默认 += 累加）
    optimizer.zero_grad()

    # ② 自动混合精度前向计算 (BF16 autocast)
    with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
        logits = model(x)              # 输出原始分数，形状 (B, 10)
        loss = criterion(logits, y)    # 内置 Log-Sum-Exp 融合计算

    # ③ 逆拓扑序反向自动求导
    loss.backward()

    # ④ 优化器步进更新参数
    optimizer.step()

    # ⑤ 累加损失（必须取 loss.item()，脱离计算图防爆显存）
    loss_sum += loss.item() * len(y)
```

---

## 4. 三大高频工程与面试避坑点

### 避坑点 1：NumPy 与 PyTorch 权重转置差异
- **数学与 NumPy 习惯**：$Z = X W + b$，其中 $X \in (B, D_{\text{in}}), W \in (D_{\text{in}}, D_{\text{out}})$。
- **PyTorch `nn.Linear` 实现**：内部公式是 $y = x A^T + b$，其 `layer.weight` 的形状被定义为 `(out_features, in_features)`！
- **后果**：如果要用 NumPy 初始值初始化 PyTorch 模型做严格对齐，必须写 `layer.weight.copy_(torch.from_numpy(W.T))`，否则维度直接报错。

### 避坑点 2：最后一层误加 `nn.Softmax()`
- `nn.CrossEntropyLoss` 内部**已经包含了** `log_softmax`。
- 如果在模型末尾接了 `nn.Softmax()`，等于对原本应该在 $[0, 1]$ 之外的真实 Logits 强行做了一次归一化，再送进 `CrossEntropyLoss` 内部做第二次 Softmax。
- **致命后果**：10 分类任务中，模型哪怕 100% 预测正确，Loss 也永远无法降到 $\ln(e+9)-1 \approx 1.4612$ 以下，且 Softmax 在两端的极小导数会导致梯度消失，训练急剧变慢。

### 避坑点 3：`loss.item()` vs `loss`
- 在记录训练日志时：
  ```python
  # 错误！loss 是带 autograd 历史的 Tensor，会导致整个 batch 的计算图一直保留在显存中
  total_loss += loss * len(y)

  # 正确！.item() 将标量 Tensor 转化为纯 Python float，断开计算图引用，显存随用随放
  total_loss += loss.item() * len(y)
  ```

---

## 5. 面试官深挖三层问题库

<details>
<summary><b>Q1: 为什么 <code>dW2 = A1.T @ dZ2</code> 这个矩阵乘法能自动算出 Batch 内所有样本对权重的梯度？</b></summary>

**答**：单个样本 $k$ 对权重矩阵的梯度是外积：$\frac{\partial L_k}{\partial W_2} = a_1^{(k)} (d z_2^{(k)})^T$。  
总损失是全 Batch 的平均：$\frac{\partial L}{\partial W_2} = \sum_{k=1}^B a_1^{(k)} \left(\frac{p^{(k)} - y^{(k)}}{B}\right)^T$。  
我们将 $A_1 \in \mathbb{R}^{B \times 128}$ 转置得到 $A_1^T \in \mathbb{R}^{128 \times B}$，其列向量恰为各样本的激活向量；与 $dZ_2 \in \mathbb{R}^{B \times 10}$（行向量为各样本误差）相乘时，矩阵乘法第 $(i, j)$ 项正是：
$$\sum_{k=1}^B A_{1}[k, i] \cdot dZ_2[k, j]$$
这恰好完成了各样本外积的逐项求和，同时避免了在 Python 里写 `for` 循环，跑在 BLAS 级并行硬件上效率极高。
</details>

<details>
<summary><b>Q2: 为什么测试阶段必须同时调用 <code>model.eval()</code> 和 <code>torch.no_grad()</code>？</b></summary>

**答**：两者职责截然不同，缺一不可：
1. `model.eval()` 改变**网络层的运算行为**（如使 Dropout 停止随机丢弃、BatchNorm 固定使用 running_mean/var 均值与方差），但它**不会关闭梯度计算**。
2. `torch.no_grad()` 是一个上下文管理器，它彻底**关闭 autograd 引擎**，在前向传播时不分配用于反向传播的激活值缓存（Activation Buffers），能节约超过 50% 显存并显著提速。
</details>

<details>
<summary><b>Q3: 为什么手写 NumPy 和 PyTorch GPU 在两层 MLP 上的测试准确率相差仅 0.02%？这微小差距来自哪里？</b></summary>

**答**：这 0.02% 的微小差异（9,773 vs 9,771，仅差 2 张图）不是代码 Bug，而是**数值精度与底层算子调度**导致的：
1. **浮点位宽**：NumPy 在 CPU 上全程使用 64 位双精度浮点数（`float64`）；PyTorch 在 RTX 4080 GPU 上开启了 `torch.bfloat16` 自动混合精度计算（仅 7 位尾数）。
2. **浮点加法非结合律**：GPU 上的并行归约（Parallel Reduction）加法求和顺序与 CPU 串行加法顺序不同，$(a + b) + c \neq a + (b + c)$，经过 10 轮迭代微小舍入误差逐渐累积，导致极少数处于分类决策边界（Decision Boundary）上的模糊手写数字概率出现微弱漂移。
</details>
