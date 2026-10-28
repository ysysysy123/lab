#!/usr/bin/env bash
# 本地 ↔ 远程 A800 (80GB) 轻量同步脚本模板
# 用前先配置 SSH 免密登录，并通过环境变量或修改下方默认值指定远程机器：
#   export A800_HOST="user@your-a800-server"
#   export A800_DIR="~/ai-lab"
#
# 用法:
#   bash env/sync_a800.sh push          # 把本地调试通的代码推上 A800（自动排除大文件）
#   bash env/sync_a800.sh pull          # 把远程训练日志与轻量评测结果拉回本地

set -euo pipefail

A800_HOST="${A800_HOST:-your_user@your_a800_ip}"
A800_DIR="${A800_DIR:-~/ai-lab}"
LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "$A800_HOST" == "your_user@your_a800_ip" ]]; then
    echo "⚠️ 请先设置环境变量: export A800_HOST='用户名@A800服务器地址'"
    exit 1
fi

case "${1:-}" in
    push)
        echo "🚀 正在同步本地代码 → ${A800_HOST}:${A800_DIR} ..."
        rsync -avzP \
            --exclude='.git/' \
            --exclude='__pycache__/' \
            --exclude='*.pt' --exclude='*.safetensors' --exclude='*.bin' \
            --exclude='checkpoints/' --exclude='outputs/' --exclude='wandb/' \
            --exclude='projects/*/external/' \
            "$LAB_ROOT/" "${A800_HOST}:${A800_DIR}/"
        echo "✅ 推送完成！登录开跑命令示例："
        echo "   ssh ${A800_HOST} -t 'cd ${A800_DIR} && tmux new -A -s train'"
        ;;
    pull)
        echo "📥 正在拉回远程实验结果与日志 → ${LAB_ROOT}/outputs/ ..."
        mkdir -p "${LAB_ROOT}/outputs"
        rsync -avzP \
            --exclude='*.safetensors' --exclude='*.bin' --exclude='global_step*' \
            "${A800_HOST}:${A800_DIR}/outputs/" "${LAB_ROOT}/outputs/"
        ;;
    *)
        echo "用法: bash env/sync_a800.sh [push|pull]"
        exit 1
        ;;
esac

