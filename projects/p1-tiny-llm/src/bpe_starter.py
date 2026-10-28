#!/usr/bin/env python3
"""
bpe_starter.py — 零依赖 60 行跑通 Byte-Pair Encoding (BPE) 分词器核心原理
运行验证: python3 projects/p1-tiny-llm/src/bpe_starter.py
"""

from __future__ import annotations

from collections import Counter


def get_pair_counts(ids: list[int]) -> Counter[tuple[int, int]]:
    return Counter(zip(ids, ids[1:]))


def merge_pair(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    out: list[int] = []
    i = 0
    while i < len(ids):
        if i + 1 < len(ids) and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


class MiniBPE:
    def __init__(self) -> None:
        self.merges: dict[tuple[int, int], int] = {}
        self.vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}

    def train(self, text: str, vocab_size: int) -> None:
        assert vocab_size >= 256
        ids = list(text.encode("utf-8"))
        for new_id in range(256, vocab_size):
            counts = get_pair_counts(ids)
            if not counts:
                break
            top_pair, freq = counts.most_common(1)[0]
            if freq < 2:
                break
            ids = merge_pair(ids, top_pair, new_id)
            self.merges[top_pair] = new_id
            self.vocab[new_id] = self.vocab[top_pair[0]] + self.vocab[top_pair[1]]

    def encode(self, text: str) -> list[int]:
        ids = list(text.encode("utf-8"))
        while len(ids) >= 2:
            counts = get_pair_counts(ids)
            # 按训练时的合并先后顺序（new_id 最小优先）选取可合并 pair
            candidate = min(
                counts, key=lambda p: self.merges.get(p, float("inf"))
            )
            if candidate not in self.merges:
                break
            ids = merge_pair(ids, candidate, self.merges[candidate])
        return ids

    def decode(self, ids: list[int]) -> str:
        raw = b"".join(self.vocab[idx] for idx in ids)
        return raw.decode("utf-8", errors="replace")


if __name__ == "__main__":
    sample = "智能体与具身智能大模型，智能体学会调用工具，具身智能学会控制机械臂！" * 5
    raw_len = len(sample.encode("utf-8"))

    tok = MiniBPE()
    tok.train(sample, vocab_size=300)
    encoded = tok.encode(sample)
    decoded = tok.decode(encoded)

    assert decoded == sample, "编解码不一致！"
    print(f"✅ BPE 自测通过！原始 UTF-8 字节长: {raw_len} → 压缩后 Token 数: {len(encoded)} (压缩率 {raw_len/len(encoded):.2f}x)")

