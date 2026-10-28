# ☁️ Colab T4 (16GB) 快速启动代码片段

当需要在 Google Colab 跑实验时，新建一个 Notebook（Runtime → Change runtime type → **T4 GPU**），按顺序粘贴以下两个单元格即可与你的 GitHub 学习库无缝同步：

## Cell 1：挂载 Google Drive（防止断联丢权重）并拉取你的学习库

```python
from google.colab import drive
drive.mount("/content/drive")

# 将 Checkpoint 统一指到云盘目录
CKPT_DIR = "/content/drive/MyDrive/ai_lab_checkpoints"
!mkdir -p {CKPT_DIR}

# 克隆你自己的 GitHub lab 仓库
!git clone https://github.com/ysysysy123/lab.git /content/lab
%cd /content/lab
```

## Cell 2：T4 专属训练参数模板（避开 BF16 报错）

```python
import torch
assert torch.cuda.is_available(), "请在菜单栏切换为 T4 GPU Runtime！"
print("GPU:", torch.cuda.get_device_name(0))

# ⚠️ T4 (Compute Capability 7.5) 铁律：
# 1. bf16=False, fp16=True
# 2. attn_implementation="sdpa"（不要强制设 flash_attention_2）
T4_TRAINING_KWARGS = dict(
    fp16=True,
    bf16=False,
    gradient_checkpointing=True,
    save_strategy="steps",
    save_steps=200,
    save_total_limit=2,
    output_dir=CKPT_DIR,
)
```

