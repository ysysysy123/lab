#!/usr/bin/env python3
"""
w01_mlp_mnist.py — W01 项目实战：NumPy 矩阵反向传播 vs PyTorch GPU 训练 MNIST
运行方式:
  python3 src/w01_mlp_mnist.py --mode numpy    # 验证纯手写 NumPy 矩阵 BP
  python3 src/w01_mlp_mnist.py --mode torch    # 跑 PyTorch GPU 基准 (准确率 >= 97%)

学习目标：
1. 掌握 Batch 维度下的矩阵反向传播推导 (dZ = P - Y, dW = A^T @ dZ, db = sum(dZ, axis=0))
2. 体验从纯数学算子到工业级 PyTorch 模块的工程跨越
"""

from __future__ import annotations

import argparse
import sys
import numpy as np


def load_mnist(batch_size: int = 128):
    """使用 torchvision 自动下载并加载 MNIST 数据集，转化为 NumPy 格式与 PyTorch DataLoader"""
    try:
        import torch
        from torchvision import datasets, transforms
    except ImportError:
        print("❌ 缺少 torch/torchvision，请使用 conda activate 切换到对应环境！")
        sys.exit(1)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_set = datasets.MNIST(root="./data", train=True, download=True, transform=transform)
    test_set = datasets.MNIST(root="./data", train=False, download=True, transform=transform)

    train_loader = torch.utils.data.DataLoader(train_set, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=1000, shuffle=False)

    return train_loader, test_loader


# =====================================================================
# 1. 纯 NumPy 手写两层 MLP (Input: 784 -> Hidden: 128 -> Output: 10)
# =====================================================================
class NumpyMLP:
    def __init__(self, in_dim: int = 784, hidden_dim: int = 128, out_dim: int = 10, lr: float = 0.05):
        self.lr = lr
        # He/Kaiming 随机初始化
        self.W1 = np.random.randn(in_dim, hidden_dim) * np.sqrt(2.0 / in_dim)
        self.b1 = np.zeros((1, hidden_dim))
        self.W2 = np.random.randn(hidden_dim, out_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros((1, out_dim))

    @staticmethod
    def softmax(z: np.ndarray) -> np.ndarray:
        # 防数值溢出减去 max
        shift_z = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(shift_z)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        前向传播:
        X: (B, 784)
        返回: (Z1, A1, Z2, P)
        """
        Z1 = X @ self.W1 + self.b1           # (B, hidden_dim)
        A1 = np.maximum(0, Z1)                # ReLU: (B, hidden_dim)
        Z2 = A1 @ self.W2 + self.b2          # (B, out_dim)
        P = self.softmax(Z2)                 # Softmax 概率分布: (B, out_dim)
        return Z1, A1, Z2, P

    def train_step(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        X: (B, 784)
        y: (B,) 类别索引 0~9
        """
        B = X.shape[0]
        Z1, A1, Z2, P = self.forward(X)

        # 1. 计算交叉熵损失
        log_likelihood = -np.log(P[np.arange(B), y] + 1e-12)
        loss = float(np.mean(log_likelihood))

        # 2. 构造 One-Hot 标签 Y
        Y = np.zeros_like(P)
        Y[np.arange(B), y] = 1.0

        # =================================================================
        # TODO(human): 手撕矩阵反向传播 (4 行核心数学公式)
        # 提示:
        # dZ2 = (P - Y) / B                       # Softmax+CrossEntropy 优雅导数: (B, 10)
        # dW2 = ...                               # (hidden_dim, 10)
        # db2 = ...                               # (1, 10)
        # dA1 = ...                               # (B, hidden_dim)
        # dZ1 = dA1 * (Z1 > 0)                    # ReLU 局部导数: (B, hidden_dim)
        # dW1 = ...                               # (in_dim, hidden_dim)
        # db1 = ...                               # (1, hidden_dim)
        # =================================================================
        # 下面 7 行请你在弄清维度后补全，跑通训练：
        dZ2 = (P - Y) / B
        dW2 = A1.T @ dZ2
        db2 = np.sum(dZ2, axis=0, keepdims=True)

        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * (Z1 > 0)
        dW1 = X.T @ dZ1
        db1 = np.sum(dZ1, axis=0, keepdims=True)

        # 参数更新 (SGD)
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

        return loss

    def evaluate(self, test_loader) -> float:
        correct, total = 0, 0
        for x_batch, y_batch in test_loader:
            x_np = x_batch.view(x_batch.size(0), -1).numpy()
            y_np = y_batch.numpy()
            _, _, _, P = self.forward(x_np)
            preds = np.argmax(P, axis=1)
            correct += int(np.sum(preds == y_np))
            total += len(y_np)
        return correct / total


# =====================================================================
# 2. PyTorch GPU 工业级实现 (对比基准)
# =====================================================================
def run_torch(train_loader, test_loader, epochs: int = 5):
    import torch
    import torch.nn as nn
    import torch.optim as optim

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 PyTorch 训练设备: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    model = nn.Sequential(
        nn.Flatten(),
        nn.Linear(784, 128),
        nn.ReLU(),
        nn.Linear(128, 10)
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # 评测
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in test_loader:
                x, y = x.to(device), y.to(device)
                preds = model(x).argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        acc = correct / total
        print(f"Epoch {epoch:02d} | Avg Loss: {total_loss / len(train_loader):.4f} | Test Acc: {acc * 100:.2f}%")

    assert acc >= 0.97, f"未达到 97% 准确率目标: {acc*100:.2f}%"
    print(f"🎉 PyTorch 模型达标！最终测试集准确率: {acc * 100:.2f}%")


def run_numpy(train_loader, test_loader, epochs: int = 5):
    print("🧠 启动 NumPy 手写两层 MLP 训练...")
    mlp = NumpyMLP(lr=0.1)

    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for x_batch, y_batch in train_loader:
            x_np = x_batch.view(x_batch.size(0), -1).numpy()
            y_np = y_batch.numpy()
            loss = mlp.train_step(x_np, y_np)
            total_loss += loss

        acc = mlp.evaluate(test_loader)
        print(f"Epoch {epoch:02d} | Avg Loss: {total_loss / len(train_loader):.4f} | Test Acc: {acc * 100:.2f}%")

    assert acc >= 0.95, f"NumPy 模型准确率低于 95%: {acc*100:.2f}%"
    print(f"🎉 NumPy 手写 MLP 达标！最终测试集准确率: {acc * 100:.2f}%")


def main():
    parser = argparse.ArgumentParser(description="W01: MNIST MLP (NumPy vs PyTorch)")
    parser.add_argument("--mode", choices=["numpy", "torch", "both"], default="both", help="运行模式")
    parser.add_argument("--epochs", type=int, default=5, help="训练轮数")
    args = parser.parse_args()

    train_loader, test_loader = load_mnist()

    if args.mode in ("numpy", "both"):
        run_numpy(train_loader, test_loader, epochs=args.epochs)
    if args.mode in ("torch", "both"):
        run_torch(train_loader, test_loader, epochs=args.epochs)


if __name__ == "__main__":
    main()
