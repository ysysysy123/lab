# 课程取源与数学/代码正确性验证协议

用户核心要求：**优先使用 AI Tutorial 原始 Notebook（`../`）和 Lab 真实代码（`concepts/`、`projects/`），确保数学、代码及交互结果 100% 正确。**

---

## 1. 取源优先级与跨设备降级策略

1. **第一优先级：Lab 仓库已有真实代码**（`concepts/*.py`、`projects/p1..p5/src/*.py`）
   - 课程页中的代码讲解（`.code-walk`）优先直接指向用户仓库里的真实脚本，行号用 `study.py learn snippet` 自动截取，`data-href` 直接链向源文件。
2. **第二优先级：上层 `autumn-recruitment` AI Tutorial 原始课程**（`../00-数学基础`、`../03-深度学习`、`../04-LLM大模型`、`../07-强化学习`、`../12-智能体开发`、`../14-具身智能`、`../15-AI-Infra`、`../20-多模态大模型`）
   - 先用 `python3 study.py dict <关键词>` 或 `REFERENCE_INDEX.md` 找准对应 `.ipynb` / `.md`。
   - 用 `python3 study.py learn nb "../路径/xxx.ipynb" --outline` 浏览结构，再用 `--cells a-b` 精读对应推导与代码 Cell，保持符号命名（如 $\delta_1, \delta_2, Z_1, H$）一致。
3. **跨设备优雅降级**：
   - `python3 study.py learn context <topic>` 会自动检测 `来源:` 字段中的文件在当前设备是否存在。
   - 在远程 A800 或 Colab（无上层 `../` 目录）上工作时，自动退回到 Lab 本地代码 + 经典原始论文推导，绝不报错阻塞教学。

---

## 2. Python 金标准（Golden Standard）铁律

大模型心算浮点数极易出错（比如 $\tanh(-0.71)$ 或 $2\times 2$ Softmax 梯度小数位算偏），而错误的数字会直接摧毁学习者对直觉和推导的信任。因此执行以下硬性检验：

1. **凡在课程正文中出现的具体数值算例、或在交互实验默认参数下展示的读数，必须先由 Python 算出！**
2. 在课题目录编写简短可复现的验证脚本（例如 `学习/<topic>/verify_0001.py`），使用 NumPy / PyTorch（本机由 `course.py` 自动定位 `~/Apps/miniconda3/envs/{ai-lab,test,robot-lab}/bin/python`，避开系统 Python 3.14）计算解析解与数值差分，并在最后一行打印 JSON：
   ```python
   import json, math
   x, w, b = 0.7, -1.3, 0.2
   z = w * x + b
   y = math.tanh(z)
   dw = (1.0 - y * y) * x
   eps = 1e-6
   num_dw = (math.tanh((w + eps) * x + b) - math.tanh((w - eps) * x + b)) / (2 * eps)
   assert abs(dw - num_dw) < 1e-9
   print(json.dumps({"z": z, "y": y, "dw": dw, "num_dw": num_dw}))
   ```
3. 运行金标准注入命令：
   ```bash
   python3 study.py learn golden 学习/<topic>/lessons/0001-xxx.html 学习/<topic>/verify_0001.py
   ```
   该命令会执行脚本并将结果写入 HTML 内的 `<script type="application/json" id="lab-golden">`。
4. 在 HTML 页面的 `Lab.ready` 脚本中，用浏览器端 JS 算出的结果调用：
   ```js
   Lab.check("z", jsZ);
   Lab.check("dw", jsDw);
   ```
5. 最后运行无头浏览器端到端检查：
   ```bash
   python3 study.py learn check 学习/<topic>/lessons/0001-xxx.html --browser
   ```
   - 静态层：检查 `{{...}}` 未替换模板变量、`TODO-LESSON` 残留、相对路径断链、`$$` 未闭合。
   - 浏览器层：用 Headless Chrome 真实加载页面，等待 KaTeX / hljs / `Lab.ready` 执行完毕，断言 `errors=0` 且 `fail=0`（所有 `Lab.check` 与 Python 金标准误差在容差内）。
