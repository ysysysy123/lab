#!/usr/bin/env bash
# 一键基于本机 ~/Apps/miniconda3 创建 Python 3.11 深度学习环境 (ai-lab)
# 用法: bash env/setup_local_conda.sh [--with-robot]

set -euo pipefail

CONDA_BASE="${CONDA_BASE:-$HOME/Apps/miniconda3}"
if [[ ! -x "$CONDA_BASE/bin/conda" ]]; then
    echo "❌ 未在 $CONDA_BASE 找到 conda，请通过 CONDA_BASE=/path/to/miniconda3 指定路径"
    exit 1
fi

# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"

echo "=== [1/2] 创建或更新 ai-lab (Python 3.11 · LLM & Agent 主力环境) ==="
if ! conda env list | awk '{print $1}' | grep -qx "ai-lab"; then
    conda create -y -n ai-lab python=3.11
fi

conda activate ai-lab
pip install -U pip wheel setuptools
# PyTorch (CUDA 12.x 预编译包，适配 RTX 4080 Laptop)
pip install torch torchvision torchaudio
# LLM / Agent 常用轻量核心包
pip install numpy matplotlib tqdm jupyterlab ipykernel wandb \
    transformers datasets tokenizers accelerate peft trl bitsandbytes \
    sentence-transformers rank-bm25 openai httpx pydantic mcp pytest

echo "✅ ai-lab 安装完成！运行体检："
python "$(dirname "$0")/check_gpu.py"

if [[ "${1:-}" == "--with-robot" ]]; then
    echo "=== [2/2] 创建 robot-lab (Python 3.11 · W11-16 具身智能环境) ==="
    if ! conda env list | awk '{print $1}' | grep -qx "robot-lab"; then
        conda create -y -n robot-lab python=3.11
    fi
    conda activate robot-lab
    pip install -U pip
    pip install torch torchvision numpy scipy matplotlib mujoco gymnasium imageio[ffmpeg]
    echo "💡 提示：第 12 周进入模仿学习时，可执行: git clone https://github.com/huggingface/lerobot.git && pip install -e lerobot"
fi

echo "🎉 全部就绪！日常开发请执行: conda activate ai-lab"

