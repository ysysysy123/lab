# 学习档案索引

> 由 `python3 study.py learn index` 自动生成，勿手改。可视化版本：[index.html](index.html)

| 主题 | 目标 | 进度 | 下一课 | 最后学习 |
|---|---|---|---|---|
| [w01-自动微分与P1](w01-自动微分与P1/计划.md) | 彻底吃透标量计算图反向传播与批量矩阵 BP（Softmax + 交叉熵化简、维度转置对齐、数值稳定性），打通 P1 NumPy/PyTorch MNIST 全链路 | 0/5 进行中 | 1. 标量计算图与 `Value.backward()` 三条铁律 | 2026-11-02 |
| [w03-Transformer与现代LLM架构](w03-Transformer与现代LLM架构/计划.md) | 从零推通缩放点积注意力、因果掩码与多头重排，吃透现代开源 LLM 四大标准积木（RoPE、RMSNorm + Pre-Norm 残差高速公路、SwiGLU 与 GQA KV Cache 账本） | 0/5 待开启 | 1. 缩放点积自注意力（SDPA）：$QK^\top / \sqrt{d_k}$ 方差推导与软检索直觉 | 2026-11-01 |

## 速查表

- [矩阵反向传播与 Softmax+交叉熵速查卡](reference/matrix-bp-softmax-cheatsheet.html)
- [现代 Transformer 与开源 LLM 架构速查卡](reference/modern-transformer-llm-cheatsheet.html)
- [标量自动微分与计算图反向传播速查卡](reference/scalar-autograd-cheatsheet.html)

## 学习记录

- [0001-w01-scalar-autograd-baseline](learning-records/0001-w01-scalar-autograd-baseline.md)：已掌握标量计算图前反向核心算子，下一步衔接批量矩阵 BP 与数值稳定 Softmax
