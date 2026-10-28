#!/usr/bin/env python3
"""
check_gpu.py — 验证当前 Python 环境、CUDA、BF16 与 SDPA/FlashAttention 支持情况
"""

import platform
import sys
import time


def main() -> None:
    print("=" * 60)
    print(f"Python 版本 : {sys.version.split()[0]}  ({sys.executable})")
    print(f"操作系统    : {platform.platform()}")
    if sys.version_info >= (3, 13):
        print("⚠️  警告: 当前使用的是 Python 3.13+，部分深度学习/机器人包可能无预编译 wheel。")
        print("   建议切换到 Conda Python 3.11: `conda activate ai-lab`")

    try:
        import torch
    except ImportError:
        print("❌ 当前环境未安装 PyTorch。请先运行 `bash env/setup_local_conda.sh` 并激活 `ai-lab`。")
        return

    print(f"PyTorch 版本: {torch.__version__}  |  CUDA 编译版本: {torch.version.cuda}")
    if not torch.cuda.is_available():
        print("❌ torch.cuda.is_available() == False，请检查驱动或是否误装了 CPU 版 torch。")
        return

    dev = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(dev)
    vram_gb = props.total_memory / (1024**3)
    bf16_ok = torch.cuda.is_bf16_supported()

    print(f"检测到 GPU  : {props.name} ({vram_gb:.1f} GB VRAM, Compute Capability {props.major}.{props.minor})")
    print(f"BF16 原生支持: {'✅ 是（训练优先开 bf16=True！）' if bf16_ok else '❌ 否（如 Colab T4，请用 fp16=True）'}")

    # 快速矩阵乘与 SDPA 验证
    dtype = torch.bfloat16 if bf16_ok else torch.float16
    x = torch.randn(2048, 2048, device="cuda", dtype=dtype)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(20):
        _ = x @ x
    torch.cuda.synchronize()
    dt_ms = (time.perf_counter() - t0) * 1000 / 20

    q = torch.randn(2, 8, 512, 64, device="cuda", dtype=dtype)
    out = torch.nn.functional.scaled_dot_product_attention(q, q, q, is_causal=True)
    print(f"2048² GEMM  : {dt_ms:.2f} ms ({dtype})  |  SDPA Causal Attention 输出形状: {tuple(out.shape)} ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()

