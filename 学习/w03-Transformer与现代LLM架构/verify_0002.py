"""第 2 课金标准验证脚本：因果掩码（Pre-Softmax -inf vs Post-Softmax 置零穿越）与多头注意力（MHA）验证。"""
import json
import numpy as np
import torch
import torch.nn as nn


def softmax_rows(x: np.ndarray) -> np.ndarray:
    x_shift = x - np.max(x, axis=-1, keepdims=True)
    ex = np.exp(x_shift)
    return ex / np.sum(ex, axis=-1, keepdims=True)


def main() -> None:
    # 1. T=4 ("我", "爱", "深", "度") 分数矩阵 S
    S = np.array([
        [1.0, 2.0, 0.5, -0.5],
        [0.8, 1.2, 2.4, 0.2],
        [0.4, 1.0, 1.5, 2.2],
        [0.6, 0.9, 1.4, 1.8],
    ], dtype=np.float64)
    T = S.shape[0]
    upper_mask = np.triu(np.ones((T, T), dtype=bool), k=1)
    tril_01 = np.tril(np.ones((T, T), dtype=np.float64), k=0)

    # (a) 正确：Pre-Softmax 加 -inf
    S_causal = np.where(upper_mask, -np.inf, S)
    A_causal = softmax_rows(S_causal)

    # PyTorch 标准写法对照
    S_t = torch.tensor(S, dtype=torch.float64, requires_grad=True)
    causal_add = torch.triu(torch.full((T, T), float("-inf"), dtype=torch.float64), diagonal=1)
    A_causal_t = torch.softmax(S_t + causal_add, dim=-1)
    assert np.max(np.abs(A_causal - A_causal_t.detach().numpy())) < 1e-12
    A_causal_t[0, 0].backward()
    grad_causal_future_01 = float(S_t.grad[0, 1].item())
    assert abs(grad_causal_future_01) == 0.0

    # (b) 错误：先 Softmax 再乘下三角 0/1 掩码
    S_t2 = torch.tensor(S, dtype=torch.float64, requires_grad=True)
    A_full_t = torch.softmax(S_t2, dim=-1)
    A_post_t = A_full_t * torch.tensor(tril_01, dtype=torch.float64)
    A_post_t[0, 0].backward()
    grad_post_future_01 = float(S_t2.grad[0, 1].item())

    A_full = softmax_rows(S)
    A_post = A_full * tril_01
    assert np.max(np.abs(A_post - A_post_t.detach().numpy())) < 1e-12
    # 解析公式：∂A_post[0,0] / ∂S[0,1] = -A_full[0,0] * A_full[0,1]
    analytic_grad_01 = -float(A_full[0, 0] * A_full[0, 1])
    assert abs(grad_post_future_01 - analytic_grad_01) < 1e-12

    # 2. 多头注意力 (B=1, T=4, C=4, H=2, d_k=2) 与 nn.MultiheadAttention 严格对齐验证
    torch.manual_seed(42)
    B, C, H, dk = 1, 4, 2, 2
    x_t = torch.randn(B, T, C, dtype=torch.float64)
    mha = nn.MultiheadAttention(embed_dim=C, num_heads=H, batch_first=True, dtype=torch.float64)
    with torch.no_grad():
        Wq = mha.in_proj_weight[:C]
        Wk = mha.in_proj_weight[C:2 * C]
        Wv = mha.in_proj_weight[2 * C:]
        bq = mha.in_proj_bias[:C]
        bk = mha.in_proj_bias[C:2 * C]
        bv = mha.in_proj_bias[2 * C:]
        Wo = mha.out_proj.weight
        bo = mha.out_proj.bias

        q = (x_t @ Wq.T + bq).view(B, T, H, dk).transpose(1, 2)
        k = (x_t @ Wk.T + bk).view(B, T, H, dk).transpose(1, 2)
        v = (x_t @ Wv.T + bv).view(B, T, H, dk).transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) / (dk ** 0.5) + causal_add
        attn = torch.softmax(scores, dim=-1)
        merged = (attn @ v).transpose(1, 2).contiguous().view(B, T, C)
        out_manual = merged @ Wo.T + bo
        out_ref, _ = mha(x_t, x_t, x_t, attn_mask=causal_add, is_causal=False)
        assert float((out_manual - out_ref).abs().max().item()) < 1e-12

    golden = {
        "S": np.round(S, 8).tolist(),
        "A_causal": np.round(A_causal, 8).tolist(),
        "A_post": np.round(A_post, 8).tolist(),
        "A_full": np.round(A_full, 8).tolist(),
        "causal_row_sums": np.round(A_causal.sum(axis=-1), 8).tolist(),
        "post_row_sums": np.round(A_post.sum(axis=-1), 8).tolist(),
        "causal_a00": round(float(A_causal[0, 0]), 8),
        "causal_a10": round(float(A_causal[1, 0]), 8),
        "causal_a11": round(float(A_causal[1, 1]), 8),
        "post_a00": round(float(A_post[0, 0]), 8),
        "post_row1_sum": round(float(A_post[1].sum()), 8),
        "full_future_leak_sum": round(float(A_full[upper_mask].sum()), 8),
        "grad_causal_future_01": 0.0 if abs(grad_causal_future_01) == 0.0 else round(grad_causal_future_01, 8),
        "grad_post_future_01": round(grad_post_future_01, 8),
        "mha_params_c512": 4 * 512 * 512,
    }
    print(json.dumps(golden))


if __name__ == "__main__":
    main()
