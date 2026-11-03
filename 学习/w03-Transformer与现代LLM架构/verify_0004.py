"""Lesson 0004 金标准验证脚本：残差梯度传播、LayerNorm vs RMSNorm 4 维手算与 PyTorch 对齐。"""
from __future__ import annotations

import json
import math
import numpy as np
import torch
import torch.nn as nn


def main() -> None:
    # 1. §1 痛点直觉：32 层无残差连乘爆炸与消失
    explode_32 = 1.5 ** 32
    vanish_32 = 0.7 ** 32

    # 2. §3 4 维向量手算对比：x = [2.0, -1.0, 3.0, 0.0], gamma = [1,1,1,1], beta = [0,0,0,0], eps = 1e-5
    eps = 1e-5
    x_np = np.array([2.0, -1.0, 3.0, 0.0], dtype=np.float64)
    gamma_np = np.ones(4, dtype=np.float64)
    beta_np = np.zeros(4, dtype=np.float64)

    # LayerNorm 手算
    ln_mu = float(np.mean(x_np))
    ln_centered = x_np - ln_mu
    ln_var = float(np.mean(ln_centered ** 2))
    ln_std = math.sqrt(ln_var + eps)
    ln_out = (ln_centered / ln_std) * gamma_np + beta_np

    # RMSNorm 手算
    rms_ms = float(np.mean(x_np ** 2))
    rms_val = math.sqrt(rms_ms + eps)
    rms_out = (x_np / rms_val) * gamma_np

    # 与 PyTorch nn.LayerNorm / nn.RMSNorm 严格对齐（float64 + float32）
    x_t = torch.tensor(x_np, dtype=torch.float64, requires_grad=True)
    ln_mod = nn.LayerNorm(4, eps=eps, dtype=torch.float64)
    y_ln_t = ln_mod(x_t)
    assert np.allclose(ln_out, y_ln_t.detach().numpy(), atol=1e-12)

    x_r = torch.tensor(x_np, dtype=torch.float64, requires_grad=True)
    rms_mod = nn.RMSNorm(4, eps=eps, dtype=torch.float64)
    y_rms_t = rms_mod(x_r)
    assert np.allclose(rms_out, y_rms_t.detach().numpy(), atol=1e-12)

    # 反向梯度对比（取上游梯度 dout = [1.0, -0.5, 0.2, 0.8]）
    dout_np = np.array([1.0, -0.5, 0.2, 0.8], dtype=np.float64)
    dout_t = torch.tensor(dout_np, dtype=torch.float64)
    y_ln_t.backward(dout_t)
    y_rms_t.backward(dout_t)

    dx_ln_manual = (dout_np - np.mean(dout_np) - ln_out * np.mean(dout_np * ln_out)) / ln_std
    dx_rms_manual = (dout_np - rms_out * np.mean(dout_np * rms_out)) / rms_val
    assert np.allclose(dx_ln_manual, x_t.grad.numpy(), atol=1e-12)
    assert np.allclose(dx_rms_manual, x_r.grad.numpy(), atol=1e-12)

    # 平移不变性 vs 缩放不变性验证（全体 +5.0）
    x_shift = x_np + 5.0
    ln_shift_out = (x_shift - np.mean(x_shift)) / np.sqrt(np.mean((x_shift - np.mean(x_shift)) ** 2) + eps)
    rms_shift_out = x_shift / np.sqrt(np.mean(x_shift ** 2) + eps)
    assert np.allclose(ln_out, ln_shift_out, atol=1e-12)

    # 3. §4 FP16 半精度溢出验证：当通道含异常激活 x_outlier = [2.0, -1.0, 300.0, 0.0]
    x_outlier_fp16 = torch.tensor([2.0, -1.0, 300.0, 0.0], dtype=torch.float16)
    fp16_sq_max = float((x_outlier_fp16 ** 2).max().item())  # inf in FP16 (300^2 = 90000 > 65504)
    assert math.isinf(fp16_sq_max)
    x_safe = (x_outlier_fp16.float() * torch.rsqrt(x_outlier_fp16.float().pow(2).mean(-1, keepdim=True) + 1e-6)).type_as(x_outlier_fp16)
    assert torch.isfinite(x_safe).all()

    # 4. §5 交互实验默认参数（L=32, alpha=0.70）三类网络底层（l=0）相对顶层（l=L）梯度范数比
    L = 32
    alpha = 0.70
    # Plain Net: g(0) = alpha^L
    grad_plain_l0 = alpha ** L
    # Post-Norm: 每层残差主干经 LN 除以 sqrt(1 + alpha^2)，正交随机支路期望均方缩放 sqrt((1 + 0.5*alpha^2)/(1 + alpha^2))
    # 主干直通分量衰减因子：(1 / sqrt(1 + alpha^2))^L
    post_step = 1.0 / math.sqrt(1.0 + alpha * alpha)
    grad_post_l0 = post_step ** L
    # Pre-Norm: 主干恒等阵 I 不衰减，第 l 层支路经 Norm 缩放 alpha / sqrt(1 + l * alpha^2)，正交期望范数：
    pre_sq = 1.0
    for l_idx in range(L - 1, -1, -1):
        pre_sq *= 1.0 + (alpha * alpha) / (1.0 + l_idx * alpha * alpha)
    grad_pre_l0 = math.sqrt(pre_sq)

    golden = {
        "explode_32": round(explode_32, 4),
        "vanish_32": round(vanish_32, 10),
        "ln_mu": round(ln_mu, 8),
        "ln_var": round(ln_var, 8),
        "ln_std": round(ln_std, 8),
        "ln_out": [round(float(v), 8) for v in ln_out],
        "rms_ms": round(rms_ms, 8),
        "rms_val": round(rms_val, 8),
        "rms_out": [round(float(v), 8) for v in rms_out],
        "dx_ln": [round(float(v), 8) for v in dx_ln_manual],
        "dx_rms": [round(float(v), 8) for v in dx_rms_manual],
        "rms_shift_out0": round(float(rms_shift_out[0]), 8),
        "grad_plain_l0": round(grad_plain_l0, 10),
        "grad_post_l0": round(grad_post_l0, 10),
        "grad_pre_l0": round(grad_pre_l0, 8),
    }
    print(json.dumps(golden))


if __name__ == "__main__":
    main()
