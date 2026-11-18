#!/usr/bin/env python3
"""
w01_mlp_mnist.py — W01 项目实战：NumPy 矩阵反向传播 vs PyTorch GPU 训练 MNIST
运行方式:
  python src/w01_mlp_mnist.py --mode both --model both --debug  # 快速试跑
  python src/w01_mlp_mnist.py --mode both --model both --epochs 10  # 完整验收

学习目标：
1. 掌握 Batch 维度下的矩阵反向传播推导 (dZ = P - Y, dW = A^T @ dZ, db = sum(dZ, axis=0))
2. 体验从纯数学算子到工业级 PyTorch 模块的工程跨越
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import numpy as np


def load_mnist(batch_size: int = 128, debug: bool = False):
    """使用 torchvision 自动下载并加载 MNIST 数据集，转化为 NumPy 格式与 PyTorch DataLoader"""
    try:
        import torch
        from torchvision import datasets
    except ImportError:
        print("❌ 缺少 torch/torchvision，请使用 conda activate 切换到对应环境！")
        sys.exit(1)

    root = Path(__file__).resolve().parents[3] / "data"
    train_set = datasets.MNIST(root=root, train=True, download=True)
    test_set = datasets.MNIST(root=root, train=False, download=True)

    # 一次性归一化，避免每轮逐张转换图片；训练集与测试集分别保留。
    def tensors(dataset, limit):
        x = dataset.data[:limit].float().reshape(-1, 784) / 255.0
        x = (x - 0.1307) / 0.3081
        return torch.utils.data.TensorDataset(x, dataset.targets[:limit])

    train_set = tensors(train_set, 640 if debug else len(train_set))
    test_set = tensors(test_set, 256 if debug else len(test_set))

    train_loader = torch.utils.data.DataLoader(train_set, batch_size=batch_size, shuffle=True,
        generator=torch.Generator().manual_seed(torch.initial_seed()))
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=1000, shuffle=False)

    return train_loader, test_loader


class NumpyLogisticRegression:
    """十分类 Softmax 回归：只有线性层，作为 MLP 的基线。"""
    def __init__(self, lr: float = 0.1):
        self.lr = lr
        self.W = np.zeros((784, 10))
        self.b = np.zeros((1, 10))

    def forward(self, X):
        Z = X @ self.W + self.b
        return Z, NumpyMLP.softmax(Z)

    def train_step(self, X, y):
        Z, P = self.forward(X)
        loss = cross_entropy(Z, y)
        Y = np.zeros_like(P)
        Y[np.arange(len(y)), y] = 1
        dZ = (P - Y) / len(y)
        self.W -= self.lr * (X.T @ dZ)
        self.b -= self.lr * dZ.sum(axis=0, keepdims=True)
        return loss


def cross_entropy(logits, y):
    """直接在 logits 上算交叉熵，与 (P-Y)/B 的梯度对应。"""
    shifted = logits - logits.max(axis=1, keepdims=True)
    return float(np.mean(np.log(np.exp(shifted).sum(axis=1))
                         - shifted[np.arange(len(y)), y]))


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
        loss = cross_entropy(Z2, y)

        # 2. 构造 One-Hot 标签 Y
        Y = np.zeros_like(P)
        Y[np.arange(B), y] = 1.0

        # 从输出层向输入层求梯度，全部算完后再更新参数。
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
def evaluate_numpy(model, loader):
    correct, total, loss_sum = 0, 0, 0.0
    predictions, labels = [], []
    for x, y in loader:
        X, target = x.numpy(), y.numpy()
        output = model.forward(X)
        logits, probs = output[-2:]
        pred = probs.argmax(axis=1)
        correct += int((pred == target).sum())
        total += len(y)
        loss_sum += cross_entropy(logits, target) * len(y)
        predictions.extend(pred.tolist())
        labels.extend(target.tolist())
    return dict(test_accuracy=correct / total, test_loss=loss_sum / total,
                correct=correct, test_samples=total,
                predictions=predictions[:12], labels=labels[:12])


def run_numpy(train_loader, test_loader, model_name="mlp", epochs=10, lr=0.1,
              output_dir=Path("runs")):
    model = NumpyMLP(lr=lr) if model_name == "mlp" else NumpyLogisticRegression(lr=lr)
    print(f"\n[NumPy/{model_name}] CPU，手写梯度，SGD lr={lr}", flush=True)
    x, y = next(iter(test_loader))
    before = model.forward(x[:12].numpy())[-1].argmax(axis=1).tolist()
    history, training_seconds, seen = [], 0.0, 0
    for epoch in range(1, epochs + 1):
        start = time.perf_counter()
        loss_sum, count = 0.0, 0
        for x, y in train_loader:
            loss = model.train_step(x.numpy(), y.numpy())
            loss_sum += loss * len(y)
            count += len(y)
        seconds = time.perf_counter() - start
        training_seconds += seconds
        seen += count
        history.append(dict(epoch=epoch, train_loss=loss_sum / count, seconds=seconds))
        print(f"Epoch {epoch:02d} | train loss {loss_sum / count:.5f} | {seconds:.2f}s", flush=True)
    result = evaluate_numpy(model, test_loader)
    names = ("W1", "b1", "W2", "b2") if model_name == "mlp" else ("W", "b")
    checkpoint = output_dir / f"numpy_{model_name}.npz"
    np.savez(checkpoint, **{name: getattr(model, name) for name in names})
    # 保存后重新载入，确认评估与保存链路确实闭合。
    with np.load(checkpoint) as saved:
        for name in names:
            setattr(model, name, saved[name].copy())
    x, _ = next(iter(test_loader))
    reloaded_pred = model.forward(x[:12].numpy())[-1].argmax(axis=1)
    assert np.array_equal(reloaded_pred, np.array(result["predictions"]))
    result.update(backend="NumPy", model=model_name, device="CPU", precision="float64",
                  epochs=epochs, learning_rate=lr, history=history,
                  training_seconds=training_seconds, samples_per_second=seen / training_seconds,
                  peak_gpu_memory_mib=0, before_predictions=before,
                  checkpoint=str(checkpoint))
    return result


def run_torch(train_loader, test_loader, model_name="mlp", epochs=10, lr=0.1,
              output_dir=Path("runs")):
    import torch
    import torch.nn as nn
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_bf16 = device.type == "cuda" and torch.cuda.is_bf16_supported()
    model = (nn.Sequential(nn.Linear(784, 128), nn.ReLU(), nn.Linear(128, 10))
             if model_name == "mlp" else nn.Sequential(nn.Linear(784, 10)))
    # 使用与 NumPy 相同的初始参数；nn.Linear 的权重存储方向相反。
    reference = NumpyMLP(lr=lr) if model_name == "mlp" else NumpyLogisticRegression(lr=lr)
    with torch.no_grad():
        if model_name == "mlp":
            for layer, w, b in ((model[0], reference.W1, reference.b1),
                                (model[2], reference.W2, reference.b2)):
                layer.weight.copy_(torch.from_numpy(w.T))
                layer.bias.copy_(torch.from_numpy(b.ravel()))
        else:
            model[0].weight.copy_(torch.from_numpy(reference.W.T))
            model[0].bias.copy_(torch.from_numpy(reference.b.ravel()))
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    print(f"\n[PyTorch/{model_name}] {device}，autograd，SGD lr={lr}，BF16={use_bf16}", flush=True)
    x, y = next(iter(test_loader))
    model.eval()
    with torch.no_grad():
        before = model(x[:12].to(device)).argmax(dim=1).cpu().tolist()
    history, training_seconds, seen = [], 0.0, 0
    for epoch in range(1, epochs + 1):
        model.train()
        if device.type == "cuda":
            torch.cuda.synchronize()
        start = time.perf_counter()
        loss_sum, count = 0.0, 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
                logits = model(x)              # 原始分数，末尾不加 Softmax
                loss = criterion(logits, y)
            loss.backward()                    # 对应 NumPy 手写的反向传播
            optimizer.step()                   # 对应 W -= lr * dW
            loss_sum += loss.item() * len(y)
            count += len(y)
        if device.type == "cuda":
            torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        training_seconds += seconds
        seen += count
        history.append(dict(epoch=epoch, train_loss=loss_sum / count, seconds=seconds))
        print(f"Epoch {epoch:02d} | train loss {loss_sum / count:.5f} | {seconds:.2f}s", flush=True)
    model.eval()
    correct, total, loss_sum = 0, 0, 0.0
    predictions, labels = [], []
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            pred = logits.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += len(y)
            loss_sum += criterion(logits, y).item() * len(y)
            predictions.extend(pred.cpu().tolist())
            labels.extend(y.cpu().tolist())
    checkpoint = output_dir / f"torch_{model_name}.pt"
    torch.save(model.state_dict(), checkpoint)
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    x, _ = next(iter(test_loader))
    with torch.no_grad():
        assert model(x[:12].to(device)).argmax(dim=1).cpu().tolist() == predictions[:12]
    return dict(backend="PyTorch", model=model_name, device=str(device),
                precision="BF16 autocast; FP32 parameters/evaluation" if use_bf16 else "float32",
                epochs=epochs, learning_rate=lr, history=history,
                training_seconds=training_seconds, samples_per_second=seen / training_seconds,
                peak_gpu_memory_mib=(torch.cuda.max_memory_allocated() / 1024**2
                                     if device.type == "cuda" else 0),
                test_accuracy=correct / total, test_loss=loss_sum / total,
                correct=correct, test_samples=total, predictions=predictions[:12],
                labels=labels[:12], before_predictions=before, checkpoint=str(checkpoint))


def main():
    import torch
    from zoneinfo import ZoneInfo
    parser = argparse.ArgumentParser(description="MNIST: NumPy 手写梯度与 PyTorch 自动微分")
    parser.add_argument("--mode", choices=["numpy", "torch", "both"], default="both")
    parser.add_argument("--model", choices=["lr", "mlp", "both"], default="mlp")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--debug", action="store_true", help="只训练 640 张、评估 256 张，跑一轮并保存")
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    train_loader, test_loader = load_mnist(args.batch_size, debug=args.debug)
    timestamp = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y%m%d-%H%M%S-%f")
    output_dir = Path(__file__).resolve().parents[1] / "runs" / timestamp
    output_dir.mkdir(parents=True)
    models = ["lr", "mlp"] if args.model == "both" else [args.model]
    backends = ["numpy", "torch"] if args.mode == "both" else [args.mode]
    results = []
    for model_name in models:
        for backend in backends:
            np.random.seed(args.seed)
            torch.manual_seed(args.seed)
            train_loader.generator.manual_seed(args.seed)
            runner = run_numpy if backend == "numpy" else run_torch
            result = runner(train_loader, test_loader, model_name=model_name,
                            epochs=1 if args.debug else args.epochs, lr=args.lr, output_dir=output_dir)
            result["passed"] = None if args.debug or model_name == "lr" else result["test_accuracy"] >= 0.97
            results.append(result)
            report = dict(seed=args.seed, batch_size=args.batch_size, debug=args.debug,
                          train_samples=len(train_loader.dataset), optimizer="SGD",
                          numpy_version=np.__version__, torch_version=torch.__version__,
                          gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                          results=results)
            (output_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            label = "冒烟通过" if args.debug else ("线性基线" if model_name == "lr" else
                    ("达到 97%" if result["passed"] else "尚未达到 97%"))
            print(f"测试准确率 {result['test_accuracy']:.2%} ({result['correct']}/{result['test_samples']}) | {label}", flush=True)
    print(f"\n结果与模型已保存：{output_dir}", flush=True)
    if any(r["passed"] is False for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
