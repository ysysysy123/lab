# 🟢 [略读·30min] ResNet: Deep Residual Learning for Image Recognition (2015)

- **阅读日期**：2026-11-06
- **一句话核心贡献**：提出残差跳跃连接 $y = \mathcal{F}(x) + x$，将网络优化目标从拟合原始映射转为拟合残差，彻底击溃百层深层网络的「退化问题」，让梯度能无损沿恒等映射直达浅层。

---

## 1. 核心痛点：为什么不能无脑堆叠网络层数？（Figure 1）
- **现象**：当普通网络从 20 层增加到 56 层时，不仅测试集误差升高，**训练集误差也显著升高（6% → 8%）**！
- **真凶辨析**：这**绝不是过拟合**（过拟合特征是训练误差极低、测试误差极高），而是**网络退化（Degradation Problem）**。深层网络难以通过 SGD 优化出复杂的恒等映射。

---

## 2. 核心招数：残差连接与梯度高速公路（Figure 2 & 公式）
- **思想实验**：
  若深层网络后半部分只需做恒等映射 $y = x$，传统网络需要复杂的非线性层碰巧学出单位矩阵 $W_2 W_1 = I$（极难）；而残差网络写成 $y = \mathcal{F}(x) + x$，网络只需让权重全衰减到 0（$\mathcal{F}(x) \to 0$），配合 L2 正则化极易收敛。
- **梯度高速公路推导**：
  前向公式：$y = \mathcal{F}(x) + x$  
  反向求导：
  $$\frac{\partial \mathcal{E}}{\partial x} = \frac{\partial \mathcal{E}}{\partial y} \cdot \left(\frac{\partial \mathcal{F}}{\partial x} + 1\right) = \frac{\partial \mathcal{E}}{\partial y} \frac{\partial \mathcal{F}}{\partial x} + \mathbf{\frac{\partial \mathcal{E}}{\partial y}}$$
  即使穿过权重层的第一路梯度消失（$\to 0$），第二路常数项 $+1$ 也能让上游误差毫发无损地保留并直达浅层。

---

## 3. 代码与现代 LLM（Transformer）映射
- **代码实现**：
  ```python
  class ResidualBlock(nn.Module):
      def forward(self, x):
          return F.relu(self.conv(x) + x)  # 跳跃连接恒等相加
  ```
- **Transformer 残差流（Residual Stream）**：
  现代 LLM（GPT、LLaMA、DeepSeek）的 Pre-Norm 残差连接：
  $$x = x + \operatorname{Attn}(\operatorname{RMSNorm}(x)), \quad x = x + \operatorname{MLP}(\operatorname{RMSNorm}(x))$$
  本质全靠 ResNet 的加法门构造梯度高速公路，支撑起 60~80 层大模型稳定训练。

---

## 4. 面试官最可能追问的 2 个问题

1. **Q：如果深层网络发生退化，为什么不直接在深层全用恒等映射？**  
   **A**：普通网络无法预先知道哪一层需要恒等、哪一层需要特征提取；ResNet 通过 $y = \mathcal{F}(x) + x$ 给了优化器绝对自由：需要提取特征时优化 $\mathcal{F}(x)$，无用时通过权重衰减让 $\mathcal{F}(x) \to 0$ 退化为恒等映射，理论上下限绝不低于浅层模型。

2. **Q：ResNet 的残差相加（Add）与 DenseNet 的拼接（Concat）在显存和设计哲学上有何不同？**  
   **A**：
   - ResNet 的加法不改变通道维度，计算量零额外增加，专注于构建**梯度的无损流动（Gradient Highway）**；
   - DenseNet 的 Concat 会不断扩充通道维度，显存开销随深度二次方增长，专注于**特征复用（Feature Reuse）**。现代大模型 Transformer 均统一采用 ResNet 的加法残差流。
