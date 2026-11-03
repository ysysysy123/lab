"""第 3 课金标准验证脚本：旋转位置编码（RoPE）2D 旋转内积平移不变性与多频复数/rotate_half 等价验证。"""
import json
import math
import numpy as np
import torch


def rot2d(vec: np.ndarray, angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    R = np.array([[c, -s], [s, c]], dtype=np.float64)
    return R @ vec


def main() -> None:
    # 1. 2D 极小手算算例：q=[1.0, 0.5], k=[0.8, 1.2], theta=0.5 rad
    q = np.array([1.0, 0.5], dtype=np.float64)
    k = np.array([0.8, 1.2], dtype=np.float64)
    theta = 0.5

    # 位置组 A: (m=1, n=3), 相对距离 n - m = 2
    q_m1 = rot2d(q, 1 * theta)
    k_n3 = rot2d(k, 3 * theta)
    dot_1_3 = float(np.dot(q_m1, k_n3))

    # 位置组 B: 整体平移 +4 -> (m=5, n=7), 相对距离 n - m = 2
    q_m5 = rot2d(q, 5 * theta)
    k_n7 = rot2d(k, 7 * theta)
    dot_5_7 = float(np.dot(q_m5, k_n7))

    # 直接相对旋转公式 q^T R_{n-m} k = q^T R_2 k
    dot_rel_2 = float(np.dot(q, rot2d(k, (3 - 1) * theta)))

    # 复数欧拉公式验证 Re[(q0 + i q1) e^{i m theta} * conj((k0 + i k1) e^{i n theta})]
    qc = complex(q[0], q[1])
    kc = complex(k[0], k[1])
    dot_complex = float(((qc * np.exp(1j * 1 * theta)) * np.conj(kc * np.exp(1j * 3 * theta))).real)

    assert abs(dot_1_3 - dot_5_7) < 1e-14
    assert abs(dot_1_3 - dot_rel_2) < 1e-14
    assert abs(dot_1_3 - dot_complex) < 1e-14

    # 模长保持不变验证
    norm_q = float(np.linalg.norm(q))
    norm_qm1 = float(np.linalg.norm(q_m1))
    norm_qm5 = float(np.linalg.norm(q_m5))
    norm_k = float(np.linalg.norm(k))
    assert abs(norm_q - norm_qm1) < 1e-14 and abs(norm_q - norm_qm5) < 1e-14

    # 2. 高维 d=8, base=10000 频率阶梯与 rotate_half vs 复数乘法等价性验证（对应 MiniMind Cell#11）
    d = 8
    base = 10000.0
    inv_freq = 1.0 / (base ** (np.arange(0, d, 2, dtype=np.float64) / d))
    # 10000^(-2j/8) = 10^(-j) = [1.0, 0.1, 0.01, 0.001]
    assert np.max(np.abs(inv_freq - np.array([1.0, 0.1, 0.01, 0.001]))) < 1e-14

    torch.manual_seed(7)
    x = torch.randn(4, d, dtype=torch.float64)
    pos = torch.arange(4, dtype=torch.float64)
    angles = torch.outer(pos, torch.tensor(inv_freq, dtype=torch.float64))  # (4, 4)

    # 写法 A（MiniMind Cell#11 halves 复数法）
    half = d // 2
    xc = torch.complex(x[:, :half], x[:, half:])
    rot_c = xc * torch.polar(torch.ones_like(angles), angles)
    out_complex_halves = torch.cat([rot_c.real, rot_c.imag], dim=-1)

    # 写法 B（工业界实数逐元素 rotate_half 写法，无需构造复数或稀疏矩阵）
    cos_full = torch.cat([torch.cos(angles), torch.cos(angles)], dim=-1)
    sin_full = torch.cat([torch.sin(angles), torch.sin(angles)], dim=-1)
    x_rot_half = torch.cat([-x[:, half:], x[:, :half]], dim=-1)
    out_rotate_half = x * cos_full + x_rot_half * sin_full

    assert float((out_complex_halves - out_rotate_half).abs().max().item()) < 1e-14

    golden = {
        "q": q.tolist(),
        "k": k.tolist(),
        "theta": theta,
        "q_m1": np.round(q_m1, 12).tolist(),
        "k_n3": np.round(k_n3, 12).tolist(),
        "q_m5": np.round(q_m5, 12).tolist(),
        "k_n7": np.round(k_n7, 12).tolist(),
        "dot_1_3": round(dot_1_3, 12),
        "dot_5_7": round(dot_5_7, 12),
        "dot_rel_2": round(dot_rel_2, 12),
        "norm_q": round(norm_q, 8),
        "norm_k": round(norm_k, 8),
        "inv_freq_d8": np.round(inv_freq, 8).tolist(),
        "wavelength_j0": round(2.0 * math.pi / inv_freq[0], 8),
        "wavelength_j3": round(2.0 * math.pi / inv_freq[3], 8),
    }
    print(json.dumps(golden))


if __name__ == "__main__":
    main()
