# 🤖 Project 4: 机器人控制基础、模仿学习策略与 VLA 微调（W11–W13）

> **简历定位**：打通具身智能从**经典运动学（IK） → 现代生成式模仿学习（ACT / Diffusion Policy） → 端到端视觉语言动作模型（SmolVLA / OpenVLA / $\pi_0$）**的完整演进链。  
> **算力分工**：
> - **本机 RTX 4080 Laptop (12GB)**：MuJoCo 实时渲染仿真 + Franka Panda 雅可比伪逆 IK + HuggingFace `LeRobot` 训练 ACT / Diffusion Policy / SmolVLA。
> - **远程 A800 (80GB)**：LIBERO 基准上微调与评测 7B 级 `OpenVLA` 或 `openpi` ($\pi_0$ LoRA)。

---

## 三周实战阶梯

### Step 1（W11）：刚体变换与阻尼最小二乘逆运动学（IK）
- [ ] 先运行零依赖玩具脚本验证数学直觉：`python3 projects/p4-robot-learning/src/ik_2d_toy.py`
- [ ] 在 `robot-lab` 环境加载 MuJoCo Franka Emika Panda 7-DoF 机械臂，读取 `mj_jacSite` 雅可比矩阵，手写阻尼伪逆 $\Delta q = J^T (J J^T + \lambda^2 I)^{-1} e$ 实现三维空间精准抓取与放置原语（此原语将在 P5 中直接被 Agent 调用！）。

### Step 2（W12）：模仿学习双壁 —— ACT 与 Diffusion Policy
- [ ] 使用 HuggingFace `LeRobot` 跑通 `PushT`（2D 推 T 形块，典型多模态分叉轨迹任务）上的 **Diffusion Policy**，亲眼验证为什么普通单步 MSE 行为克隆（BC）会在障碍物前卡死（对左右两条轨迹求均值撞上中间），而扩散策略能稳定绕行。
- [ ] 在 ALOHA 仿真任务（如块转移）上训练 **ACT (Action Chunking with Transformers)**，验证 Action Chunking 长度 $k$ 对复合误差的抑制效果。

### Step 3（W13）：开源 VLA 微调评测
- [ ] 本机跑通轻量级 `SmolVLA` 推理与微调；
- [ ] 远程 A800 在 `LIBERO-Spatial` / `LIBERO-Object` 子集上跑通 `OpenVLA` 或 $\pi_0$ LoRA 微调，填写成功率对比表：

## 📊 待填实验结果表

| 任务环境 | 策略模型 | 训练演示轨迹数 | 成功率 Success Rate (%) | 控制推理延迟 (ms) |
|---|---|---|---|---|
| PushT | 单步 MLP 行为克隆 (BC Baseline) | | | |
| PushT | **Diffusion Policy** | | | |
| ALOHA Sim | **ACT (Chunk size = 50)** | | | |
| LIBERO-Spatial | **VLA LoRA 微调** | | | |

