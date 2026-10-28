# 🧠 Project 1: TinyLLM 从零构建、对齐与 7B 量化部署（W01–W08）

> **简历定位**：证明你不是只会调 API，而是亲手走完 **Tokenizer → 模型架构 → Pretrain → SFT → DPO → QLoRA → vLLM/AWQ 部署** 全生命周期。  
> **主力算力**：本机 RTX 4080 Laptop (12GB, `bf16=True` + FlashAttention-2)；W08 在 A800 部署 vLLM。

---

## 阶段拆解与交付物清单

### Stage A（W01–W04）：纯手搓 BPE + nanoGPT
- [ ] 阅读并跑通 `src/bpe_starter.py`（字节对合并核心循环），扩展到中文小说/古诗小语料词表训练
- [ ] 跟随 Karpathy *Let's build GPT* 从零拼装 Decoder-only Transformer（Causal Self-Attention + MLP + Residual + LayerNorm）
- [ ] 产出：10MB 中文语料训练曲线 + 生成样例文本

### Stage B（W05–W07）：现代架构 MiniMind 全管线（RoPE + GQA + SwiGLU + DPO）
- [ ] 拉取参考源码到忽略目录：`git clone https://github.com/jingyaogong/minimind.git external/minimind`
- [ ] 对照源码在自己的 `src/` 实现或精简重构 **RoPE、RMSNorm、SwiGLU、GQA、KV Cache**
- [ ] 依次在本机 4080 跑通：`Pretrain` → `Full SFT`（理解 Assistant Loss Mask）→ `DPO`（观察 chosen/rejected margin 拉开）

### Stage C（W06 & W08）：工业级 Qwen2.5-7B QLoRA 微调与 vLLM 量化评测
- [ ] 构造「自然语言复杂指令 → 机器人/工具调用严格 JSON」数据集（为后续 P2/P5 铺路！）
- [ ] 在本机 4080 用 Unsloth / LLaMA-Factory 4-bit QLoRA 微调 `Qwen2.5-7B-Instruct`
- [ ] 在 A800 用 `vLLM` 部署，填写下方评测对比表（直接进简历！）：

## 📊 待填实验结果表（简历弹药库）

| 模型方案 | 显存占用 (GB) | JSON 严格合法率 (%) | 指令槽位准确率 (%) | 首字延迟 TTFT (ms) | 吞吐 (tok/s) |
|---|---|---|---|---|---|
| Qwen2.5-7B 基线 (Zero-shot) | | | | | |
| + QLoRA SFT (FP16 / BF16) | | | | | |
| + QLoRA SFT + AWQ 4-bit (vLLM) | | | | | |

