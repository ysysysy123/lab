# ⚡ 三端算力调度指南（RTX 4080 12GB + Colab T4 16GB + 远程 A800 80GB）

## 1. 三卡黄金分工矩阵

| 算力端 | 架构关键特性 | 专属任务 | 避坑要点 |
|---|---|---|---|
| **本机 RTX 4080 Laptop (12GB)** | Ada 架构（SM89）<br>✅ 原生 **BF16**<br>✅ 原生 **FlashAttention-2**<br>✅ 零网络延迟、可弹 GUI 窗口 | • 阶段一全部（GPT / BPE）<br>• MiniMind 全流程（Pretrain / SFT / DPO）<br>• Unsloth Qwen2.5-7B 4bit QLoRA（~9.5GB）<br>• 0.5B/1.5B GRPO 小实验<br>• **MuJoCo 可视化仿真 + LeRobot ACT/DP/SmolVLA** | Ubuntu 26.04 系统自带 Python 3.14 太新，**严禁直接用系统 pip**，统一走 `~/Apps/miniconda3` 的 Python 3.11 环境 |
| **Colab T4 (16GB)** | Turing 架构（SM75）<br>❌ **不支持 BF16**<br>❌ **不支持 FlashAttention-2** | • 当本机满载训练时，并行跑第二组超参或评测<br>• 需要 12.5–15GB 显存的中型实验 | 训练参数必须设 `fp16=True, bf16=False`；Attention 设 `sdpa` 或 `eager`；每 200 step 存一次 Google Drive 防断联 |
| **远程 A800 (80GB)** | Ampere 架构（SM80）<br>✅ 80GB 超大显存 + 高带宽<br>✅ BF16 + FlashAttention-2 | • **W08**：vLLM 常驻部署 7B/14B 供本地 Agent 调接口<br>• **W10**：veRL / TRL 跑 3B Agentic RL (Search-R1)<br>• **W13-15**：OpenVLA / $\pi_0$ (`openpi`) LoRA 微调与 LIBERO 评测 | **绝不在 A800 上从零改 Bug**！代码必须先在本机用 `batch_size=1, max_steps=5` 跑通，再用 `sync_a800.sh` 推上去挂 `tmux` 跑 |

---

## 2. 本机环境两步到位

我们拆成两个独立的 Python 3.11 环境，避免大模型训练库（`vllm/trl/unsloth`）和机器人仿真库（`mujoco/lerobot`）出现依赖打架：

- **`ai-lab`**（第 1–10 周主力）：PyTorch + Transformers + TRL + PEFT + Rank-BM25 + MCP 等
- **`robot-lab`**（第 11–16 周主力）：PyTorch + MuJoCo + Gymnasium + HuggingFace LeRobot

```bash
# 在你自己的终端运行（需要联网下载包）：
bash env/setup_local_conda.sh

# 激活并体检显卡能力：
conda activate ai-lab
python env/check_gpu.py
```

---

## 3. A800 远程训练四条军规

1. **进机器第一件事开 `tmux`**：`tmux new -s train`（断网不掉进程，`Ctrl+B` 松开按 `D` 挂起，`tmux a -t train` 重连）。
2. **强制接入 WandB**：离线或断连也能在手机/网页实时看 Loss、Reward 和显存曲线，发现梯度爆炸立刻停，不浪费机时。
3. **跑前必做 Smoke Test**：正式跑几小时前，先加 `--max_steps 10 --save_steps 5` 确认**训练→验证→保存 Checkpoint** 全链路无报错（很多 OOM 发生在第一次 eval 或 save 时！）。
4. **权重不拉回本地，只拉日志与 Adapter**：LoRA adapter 只有几十 MB，用 `bash env/sync_a800.sh pull` 秒拉回本地写实验报告。

