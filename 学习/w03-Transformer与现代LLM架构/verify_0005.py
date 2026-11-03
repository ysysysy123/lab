"""Lesson 0005 金标准验证脚本：SwiGLU 2x3 手算、8/3d 参数对齐与 GQA KV Cache 字节显存账本。"""
from __future__ import annotations

import json
import math
import numpy as np
import torch
import torch.nn.functional as F


def main() -> None:
    # 1. §2 SwiGLU 极小数字手算：d = 2, d_ff = 3, 无偏置
    x = np.array([1.0, 2.0], dtype=np.float64)  # (2,)
    W_gate = np.array([
        [1.0, -1.0, 0.0],
        [0.5,  0.0, -2.0],
    ], dtype=np.float64)  # (2, 3) -> g = [2.0, -1.0, -4.0]
    W_up = np.array([
        [0.5, 1.0, 1.0],
        [0.5, 1.5, 1.0],
    ], dtype=np.float64)  # (2, 3) -> u = [1.5, 4.0, 3.0]
    W_down = np.array([
        [1.0,  0.0],
        [0.5, -1.0],
        [0.0,  2.0],
    ], dtype=np.float64)  # (3, 2)

    gate_pre = x @ W_gate                     # [2.0, -1.0, -4.0]
    gate_sig = 1.0 / (1.0 + np.exp(-gate_pre))
    gate_silu = gate_pre * gate_sig           # SiLU(g)
    up_val = x @ W_up                         # [1.5, 4.0, 3.0]
    hidden_gated = gate_silu * up_val         # SiLU(g) * u
    swiglu_out = hidden_gated @ W_down        # (2,)

    # 与 PyTorch F.silu 严格对齐
    xt = torch.tensor(x, dtype=torch.float64)
    gt = xt @ torch.tensor(W_gate, dtype=torch.float64)
    ut = xt @ torch.tensor(W_up, dtype=torch.float64)
    out_t = (F.silu(gt) * ut) @ torch.tensor(W_down, dtype=torch.float64)
    assert np.allclose(swiglu_out, out_t.numpy(), atol=1e-12)

    # 2. §2 8/3 d 参数对齐推导验证（Llama-2-7B: d = 4096, multiple_of = 256 -> 11008）
    d_llama = 4096
    raw_dff = (8.0 / 3.0) * d_llama
    llama_dff = int(math.ceil(raw_dff / 256.0) * 256)
    assert llama_dff == 11008
    ffn_std_params = 2 * d_llama * (4 * d_llama)       # 134,217,728
    ffn_swiglu_params = 3 * d_llama * llama_dff        # 135,266,304

    # 3. §3 & §5 KV Cache 字节级显存账本验证（B=1, T=32768, BF16=2 Bytes）
    def kv_bytes(layers: int, h_kv: int, d_k: int, b: int, t: int, elem_bytes: float) -> float:
        return 2.0 * layers * h_kv * d_k * b * t * elem_bytes

    # Llama-2-7B (MHA: L=32, H_q=32, H_kv=32, d_k=128, params=6.74B)
    l2_per_tok_mib = kv_bytes(32, 32, 128, 1, 1, 2.0) / (1024 ** 2)        # 0.5 MiB
    l2_32k_gib = kv_bytes(32, 32, 128, 1, 32768, 2.0) / (1024 ** 3)        # 16.0 GiB

    # Llama-3-8B (GQA: L=32, H_q=32, H_kv=8, d_k=128, params=8.03B)
    l3_per_tok_mib = kv_bytes(32, 8, 128, 1, 1, 2.0) / (1024 ** 2)         # 0.125 MiB
    l3_32k_gib = kv_bytes(32, 8, 128, 1, 32768, 2.0) / (1024 ** 3)         # 4.0 GiB

    # Qwen2.5-7B (GQA: L=28, H_q=28, H_kv=4, d_k=128, params=7.62B)
    qwen_per_tok_kib = kv_bytes(28, 4, 128, 1, 1, 2.0) / 1024.0            # 56.0 KiB
    qwen_32k_gib = kv_bytes(28, 4, 128, 1, 32768, 2.0) / (1024 ** 3)      # 1.75 GiB

    # §7 自测题验证：14B 模型 L=40, H_q=40, H_kv=8, d_k=128, BF16(2B), B=4, T=8192
    quiz_14b_gib = kv_bytes(40, 8, 128, 4, 8192, 2.0) / (1024 ** 3)        # 5.0 GiB

    golden = {
        "gate_pre": [round(float(v), 8) for v in gate_pre],
        "gate_silu": [round(float(v), 8) for v in gate_silu],
        "up_val": [round(float(v), 8) for v in up_val],
        "hidden_gated": [round(float(v), 8) for v in hidden_gated],
        "swiglu_out": [round(float(v), 8) for v in swiglu_out],
        "llama_dff": llama_dff,
        "ffn_swiglu_mparams": round(ffn_swiglu_params / 1e6, 6),
        "l2_per_tok_mib": round(l2_per_tok_mib, 8),
        "l2_32k_gib": round(l2_32k_gib, 8),
        "l3_per_tok_mib": round(l3_per_tok_mib, 8),
        "l3_32k_gib": round(l3_32k_gib, 8),
        "qwen_per_tok_kib": round(qwen_per_tok_kib, 8),
        "qwen_32k_gib": round(qwen_32k_gib, 8),
        "quiz_14b_gib": round(quiz_14b_gib, 8),
    }
    print(json.dumps(golden))


if __name__ == "__main__":
    main()
