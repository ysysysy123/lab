#!/usr/bin/env python3
"""
react_loop_starter.py — 零框架！80 行看透 Agent 的本质（ReAct 决策循环 + 工具注册表）
运行验证（内置 Mock LLM，无需联网即可先跑通闭环）:
  python3 projects/p2-scratch-agent/src/react_loop_starter.py

W05 实战任务:
  将 MockLLM.generate() 替换为 openai.OpenAI(base_url=..., api_key=...) 真实调用，
  并新增一个调用上层参考库检索的 search_local_repo(query) 工具！
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str) -> Callable[[Callable[..., str]], Callable[..., str]]:
        def decorator(fn: Callable[..., str]) -> Callable[..., str]:
            self._tools[name] = Tool(name=name, description=description, fn=fn)
            return fn
        return decorator

    def describe_all(self) -> str:
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())

    def execute(self, name: str, kwargs: dict) -> str:
        if name not in self._tools:
            return f"Error: 未知工具 '{name}'，可用工具: {list(self._tools)}"
        try:
            return str(self._tools[name].fn(**kwargs))
        except Exception as exc:
            return f"Error: 工具执行异常 {type(exc).__name__}: {exc}"


registry = ToolRegistry()


@registry.register("kv_cache_vram_gb", "计算 FP16 下 KV Cache 显存(GB)，参数: layers, kv_heads, head_dim, seq_len, batch")
def kv_cache_vram_gb(layers: int, kv_heads: int, head_dim: int, seq_len: int, batch: int = 1) -> str:
    # 2 (K和V) * layers * batch * seq_len * kv_heads * head_dim * 2 bytes (FP16)
    bytes_total = 2 * layers * batch * seq_len * kv_heads * head_dim * 2
    return f"{bytes_total / (1024 ** 3):.3f} GB"


class MockLLM:
    """离线演示桩：模拟大模型第 1 步发起工具调用，第 2 步根据 Observation 给出最终答案"""

    def generate(self, messages: list[dict[str, str]]) -> str:
        last_msg = messages[-1]["content"]
        if "Observation:" not in last_msg:
            return (
                "Thought: 需要先精确计算 32层、8个KV头、维度128、序列长8192 在 FP16 下的 KV Cache 显存。\n"
                'Action: {"tool": "kv_cache_vram_gb", "args": {"layers": 32, "kv_heads": 8, "head_dim": 128, "seq_len": 8192, "batch": 1}}'
            )
        return f"Thought: 已拿到精确计算结果。\nFinal Answer: 在该 GQA 配置下，单并发 8K 上下文的 FP16 KV Cache 仅占 {last_msg.split('Observation:')[-1].strip()}。"


def run_react_agent(question: str, llm: MockLLM, max_steps: int = 5) -> str:
    system_prompt = (
        "你是一个严谨的 AI 助手。可使用以下工具：\n"
        f"{registry.describe_all()}\n"
        '需要调工具时输出 Action: {"tool": "...", "args": {...}}；得出答案时输出 Final Answer: ...'
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for step in range(1, max_steps + 1):
        reply = llm.generate(messages)
        print(f"[Step {step}] LLM 输出:\n{reply}\n")
        messages.append({"role": "assistant", "content": reply})

        if "Final Answer:" in reply:
            return reply.split("Final Answer:", 1)[1].strip()

        m = re.search(r"Action:\s*(\{.*\})", reply)
        if not m:
            messages.append({"role": "user", "content": "Observation: 格式错误，请输出 Action JSON 或 Final Answer。"})
            continue

        call = json.loads(m.group(1))
        obs = registry.execute(call["tool"], call.get("args", {}))
        print(f"[Step {step}] 工具返回 → Observation: {obs}\n")
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    return "达到最大步数限制，任务未完成。"


if __name__ == "__main__":
    ans = run_react_agent("Llama-3-8B (32层, GQA 8个KV头, head_dim=128) 在 8192 长度下 KV Cache 占多少显存？", MockLLM())
    assert "1.000 GB" in ans
    print(f"✅ ReAct 闭环验证成功！最终回答: {ans}")

