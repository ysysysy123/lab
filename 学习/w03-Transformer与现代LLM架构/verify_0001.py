"""第 1 课金标准验证脚本：缩放点积自注意力（SDPA）T=3, d_k=2 手算算例与 √d_k 缩放梯度检验。"""
import json
import math
import numpy as np
import torch
import torch.nn.functional as F


def softmax_rows(x: np.ndarray) -> np.ndarray:
    x_shift = x - np.max(x, axis=-1, keepdims=True)
    ex = np.exp(x_shift)
    return ex / np.sum(ex, axis=-1, keepdims=True)


def softmax_jacobian_frob(p: np.ndarray) -> float:
    """单行 Softmax 概率向量 p 的雅可比矩阵 J_ij = p_i (delta_ij - p_j) 的 Frobenius 范数。"""
    J = np.diag(p) - np.outer(p, p)
    return float(np.linalg.norm(J, ord="fro"))


def main() -> None:
    # 1. T=3 ("猫", "追", "鱼"), d_k=2 极小算例
    Q = np.array([[1.0, 0.0], [0.5, 1.0], [0.0, 1.0]], dtype=np.float64)
    K = np.array([[1.0, 0.2], [0.2, 0.8], [0.4, 1.0]], dtype=np.float64)
    V = np.array([[1.0, 0.0], [0.4, 0.6], [0.0, 1.0]], dtype=np.float64)

    dk = Q.shape[-1]
    S_raw = Q @ K.T
    S_scaled = S_raw / math.sqrt(dk)
    A = softmax_rows(S_scaled)
    O = A @ V

    # PyTorch F.scaled_dot_product_attention 双重验证
    Q_t = torch.tensor(Q, dtype=torch.float64).unsqueeze(0)
    K_t = torch.tensor(K, dtype=torch.float64).unsqueeze(0)
    V_t = torch.tensor(V, dtype=torch.float64).unsqueeze(0)
    O_torch = F.scaled_dot_product_attention(Q_t, K_t, V_t).squeeze(0).numpy()
    assert np.max(np.abs(O - O_torch)) < 1e-12, f"SDPA mismatch: {np.max(np.abs(O - O_torch))}"

    # PyTorch autograd.functional.jacobian 验证第 0 行 Softmax 雅可比矩阵
    s0_t = torch.tensor(S_scaled[0], dtype=torch.float64, requires_grad=True)
    J0_torch = torch.autograd.functional.jacobian(lambda s: torch.softmax(s, dim=-1), s0_t).numpy()
    J0_np = np.diag(A[0]) - np.outer(A[0], A[0])
    assert np.max(np.abs(J0_np - J0_torch)) < 1e-12

    # 2. 不同头维度 d_k 下的未缩放 vs 缩放对比（按独立同分布标准差 ∝ √d_k 放大：S_unscaled(dk) = S_raw * √(dk/2)）
    def eval_dk(sim_dk: float, use_scale: bool) -> dict[str, float]:
        s_unscaled = S_raw * math.sqrt(sim_dk / 2.0)
        s = s_unscaled / math.sqrt(sim_dk) if use_scale else s_unscaled
        attn = softmax_rows(s)
        jf_rows = [softmax_jacobian_frob(attn[r]) for r in range(attn.shape[0])]
        return {
            "max_w": float(np.max(attn)),
            "jf_row0": jf_rows[0],
            "jf_mean": float(np.mean(jf_rows)),
        }

    dk2_scaled = eval_dk(2.0, True)
    dk64_scaled = eval_dk(64.0, True)
    dk64_unscaled = eval_dk(64.0, False)
    dk256_unscaled = eval_dk(256.0, False)

    # 缩放开启时，任意 d_k 下的注意力分布与雅可比范数严格恒定
    assert abs(dk2_scaled["jf_mean"] - dk64_scaled["jf_mean"]) < 1e-12

    golden = {
        "Q": np.round(Q, 8).tolist(),
        "K": np.round(K, 8).tolist(),
        "V": np.round(V, 8).tolist(),
        "S_raw": np.round(S_raw, 8).tolist(),
        "S_scaled": np.round(S_scaled, 8).tolist(),
        "A": np.round(A, 8).tolist(),
        "O": np.round(O, 8).tolist(),
        "s_raw_12": round(float(S_raw[1, 2]), 8),
        "s_scaled_12": round(float(S_scaled[1, 2]), 8),
        "a_12": round(float(A[1, 2]), 8),
        "o_10": round(float(O[1, 0]), 8),
        "o_11": round(float(O[1, 1]), 8),
        "jf_dk2_scaled": round(dk2_scaled["jf_mean"], 8),
        "jf_dk64_scaled": round(dk64_scaled["jf_mean"], 8),
        "jf_dk64_unscaled": round(dk64_unscaled["jf_mean"], 8),
        "maxw_dk64_unscaled": round(dk64_unscaled["max_w"], 8),
        "jf_dk256_unscaled": round(dk256_unscaled["jf_mean"], 8),
        "maxw_dk256_unscaled": round(dk256_unscaled["max_w"], 8),
        "jf0_dk2_scaled": round(dk2_scaled["jf_row0"], 8),
        "jf0_dk64_unscaled": round(dk64_unscaled["jf_row0"], 8),
        "jf0_dk256_unscaled": round(dk256_unscaled["jf_row0"], 8),
    }
    print(json.dumps(golden))


if __name__ == "__main__":
    main()
