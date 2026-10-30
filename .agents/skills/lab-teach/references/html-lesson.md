# HTML 交互式课程页与共享组件手册

所有课程页（`学习/<topic>/lessons/NNNN-*.html`）与速查表（`学习/reference/*.html`）必须引用 `.agents/skills/lab-teach/assets/` 中的共享组件，**禁止每节课另写一套独立 CSS/JS**。离线状态下公式（KaTeX）与代码高亮（highlight.js）均可直接从本地 `assets/vendor/` 加载。

---

## 1. 页面骨架与布局

- 由 `python3 study.py learn new-lesson <topic> <slug> --title "..." --step N` 自动注入正确的 `{{ASSETS}}` 相对路径、面包屑、`<!-- LAB:NAV -->` 与 `<!-- LAB:GOLDEN -->`。
- **三栏自适应（`.lab-layout`）**：
  - 左栏 `<nav id="lab-toc">`：`lab.js` 自动扫描正文 `h2, h3` 生成目录并随滚动高亮。
  - 中栏 `<main class="lab-main">`：最大宽度 `760px`（速查表 `body.ref` 为 `980px`），排版克制耐读。
  - 右栏 `<aside class="lab-margin">`：宽屏（`>1280px`）下，正文中 `<aside class="sidenote">补充说明…</aside>` 会像 Tufte 书籍一样自动浮动到右侧边注栏；窄屏下优雅退化为内嵌小卡片。
- **章节标题写法**：`<h2><span class="num">01</span>痛点与直觉</h2>`（目录自动显示为 `01 · 痛点与直觉`）。

---

## 2. 语义卡片、公式字典与表格

### 2.1 九种语义 Callout
```html
<div class="callout intuition">
  <span class="ct">直觉类比</span>
  <p>正向传播像多米诺骨牌依次触发；反向传播像按贡献比例分摊账单。</p>
</div>
```
可用修饰类：`intuition`（💡直觉）、`principle`（🔧原理）、`formula`（📐公式）、`code`（💻代码）、`lab`（🧪实验）、`warn`（⚠️防坑）、`interview`（🎤面试）、`summary`（📌小结）、`source`（📚资料）。

### 2.2 核心公式与符号字典（`.eq-explain`）
所有非平凡公式下方紧跟符号与维度说明，杜绝裸贴公式墙：
```html
<div class="eq-explain">
  <span class="eq-tag">(式 1)</span>
  <p>$$\delta_1 = (\delta_2 W_2) \odot \sigma'(Z_1)$$</p>
  <dl>
    <dt>$\delta_2 \in \mathbb{R}^{B \times K}$</dt><dd>输出层上游梯度 $\partial L / \partial Z_2$</dd>
    <dt>$W_2 \in \mathbb{R}^{K \times H}$</dt><dd>输出层权重，右乘 $W_2$ 把维度从 $K$ 投回隐藏层 $H$</dd>
    <dt>$\odot\ \sigma'(Z_1)$</dt><dd>逐元素乘局部激活导数（ReLU 下即掩码 $\mathbb{1}[Z_1 > 0]$）</dd>
  </dl>
</div>
```
> **注意**：正文与 `Lab.playground`、`Lab.readout` 内均支持 `$...$` 与 `$$...$$` 自动渲染；若正文需写字面美元符号请写 `\$` 或包在 `<code>` 内。

### 2.3 张量 Shape 追踪表（`table.shape`）
架构课必配，第 2 列自动使用等宽主题色字体：
```html
<table class="shape">
  <tr><th>张量 / 步骤</th><th>Shape</th><th>物理含义</th></tr>
  <tr><td><code>Q, K, V</code></td><td>(B, H, T, d_k)</td><td>分头重排后的查询/键/值</td></tr>
  <tr><td><code>scores</code></td><td>(B, H, T, T)</td><td>缩放点积 $QK^\top / \sqrt{d_k}$ + 因果掩码</td></tr>
</table>
```

---

## 3. 逐步演示、标签页、点击展开与双栏代码讲解

### 3.1 逐步演示（`.lab-stepper`）
支持 `← / →` 键盘切换与圆点跳转；设置 `data-mode="accumulate"` 时已走过的步骤保持可见（最适合数学分步推导），不设则每次只显示当前步（适合状态切换动画）：
```html
<div class="lab-stepper" id="deriv-1" data-title="Softmax + 交叉熵梯度化简" data-mode="accumulate">
  <div class="step" data-title="写出单样本损失">
    <p>$$L = -\log p_y = -\log \frac{e^{z_y}}{\sum_j e^{z_j}} = \log \sum_j e^{z_j} - z_y$$</p>
  </div>
  <div class="step" data-title="对任意 logit z_i 求偏导">
    <p>$$\frac{\partial L}{\partial z_i} = \frac{e^{z_i}}{\sum_j e^{z_j}} - \mathbb{1}[i = y] = p_i - y_i$$</p>
  </div>
</div>
```
需要把 stepper 与 SVG 图联动时：`Lab.onStep("#deriv-1", (idx, stepEl) => { ... });`

### 3.2 双栏代码讲解（`.code-walk`）
左侧真实代码（带源文件头、行号、一键复制），右侧编号讲解卡片；点击任一卡片自动高亮并滚动到对应行（加 `data-dim` 会淡化非当前行）：
```html
<div class="code-walk" data-dim>
<pre data-file="concepts/w01_micro_autograd.py" data-start="32" data-href="../../../concepts/w01_micro_autograd.py"><code class="language-python">    def __mul__(self, other: Value | float) -> Value:
        ...</code></pre>
  <ol class="walk">
    <li data-lines="32-34">前向：把乘法结果包成新 <code>Value</code>，并记录左右父节点 <code>(self, other)</code></li>
    <li data-lines="36-38">反向：链式法则 $\frac{\partial(ab)}{\partial a}=b$，<strong>必须用 <code>+=</code></strong> 防止变量复用时梯度被覆盖</li>
  </ol>
</div>
```
> 务必使用 `python3 study.py learn snippet <path> --lines a-b --for <lesson.html>` 生成 `<pre>`，不要手抄行号！

### 3.3 点击展开答案 / 选读深挖（`details.reveal`）
- 自测问题与面试追问（默认折叠，右上角显示「点击展开」）：
  ```html
  <details class="reveal q">
    <summary>如果把 <code>self.grad += ...</code> 改成 <code>=</code>，哪个最简表达式会立刻算错？</summary>
    <div><p><code>y = x + x</code>（或 <code>y = x * x</code> 当 $x\neq 0$）：两条支路回传时第二次赋值会把第一次覆盖掉，导致 <code>x.grad</code> 只剩一半。</p></div>
  </details>
  ```
- 严谨证明或扩展阅读：`<details class="reveal deep"><summary>选读：雅可比矩阵视角</summary><div>...</div></details>`
- 页面右上角工具条会自动出现「展开全部 / 收起全部」按钮，打印（`Ctrl+P`）时也会自动全部展开。

### 3.4 多实现对比标签页（`.lab-tabs`）
适合对比「纯 NumPy 手写 vs PyTorch 官方实现」或「FP16 vs BF16 配置」；相同 `data-group="impl"` 的多组标签页会同步切换：
```html
<div class="lab-tabs" data-group="impl">
  <div class="tab" data-label="NumPy 手写"><pre><code class="language-python">...</code></pre></div>
  <div class="tab" data-label="PyTorch 对照"><pre><code class="language-python">...</code></pre></div>
</div>
```

---

## 4. 动态实验与 SVG 图表 API（`Lab` · `LabMath` · `LabPlot`）

所有脚本写在页面底部 `Lab.ready(() => { ... });` 内。

### 4.1 参数实验台 `Lab.playground(target, spec)` + `Lab.readout(container, kv, digits)`
```js
Lab.playground("#pg-demo", {
  title: "调节权重 w 观察 tanh 输出与局部导数",
  params: [
    { name: "w", label: "权重 $w$", min: -3, max: 3, step: 0.05, value: -1.3 },
    { name: "x", label: "输入 $x$", min: -2, max: 2, step: 0.05, value: 0.7 },
  ],
  selects: [
    { name: "act", label: "激活函数", options: [["tanh", "tanh"], ["relu", "ReLU"]], value: "tanh" },
  ],
  buttons: [
    { label: "重置为课程算例", onClick: (_p, ctl) => { ctl.set("w", -1.3); ctl.set("x", 0.7); } },
  ],
  caption: "实线为激活函数 $f(z)$，虚线为局部导数 $f'(z)$，圆点为当前前向工作点。",
  render(p, out) {
    out.innerHTML = '<div class="plot-box"></div>';
    const z = p.w * p.x + 0.2;
    const y = Math.tanh(z), dy = 1 - y * y;
    LabPlot.chart(out.querySelector(".plot-box"), { x: [-3, 3], y: [-1.2, 1.2], xLabel: "z = wx + b", height: 280 })
      .fn(Math.tanh, { label: "tanh(z)", color: 1 })
      .fn((t) => 1 - Math.tanh(t) ** 2, { label: "1 - tanh²(z)", color: 2, dash: true })
      .point(z, y, { label: `z=${Lab.fmt(z, 2)}`, color: 1 })
      .draw();
    Lab.readout(out, { "线性输出 $z$": z, "激活值 $y$": y, "局部导数 $\\partial y/\\partial z$": dy, "权重梯度 $\\partial y/\\partial w$": dy * p.x });
  },
});
```

### 4.2 四类零依赖 SVG 图表 `LabPlot`（深浅色切换自动重绘）
1. **函数/折线/散点/向量图 `LabPlot.chart(el, opts)`**：
   - `opts`：`{ x: [lo, hi], y: [lo, hi] | "auto", xLabel, yLabel, title, width: 640, height: 320, yZero: false }`
   - 链式图层：`.fn(f, {label, color, dash, fill, samples})`、`.line(xs, ys, o)`、`.scatter(xs, ys, o)`、`.vline(v, o)`、`.hline(v, o)`、`.point(x, y, o)`、`.arrow(x1, y1, x2, y2, o)`、`.text(x, y, str, o)` → 最后 `.draw()`（或在回调中 `.update(c => { ... })`）。
2. **矩阵 / 注意力热力图 `LabPlot.heatmap(el, matrix2D, opts)`**：
   - `opts`：`{ rowLabels, colLabels, decimals: 2, scheme: "seq" | "div", min, max, title, onClick(i,j,v) }`，支持 `-Infinity`（因果掩码自动显示 `−∞`）。返回 `{ update(M) }`。
3. **概率分布 / 指标对比柱状图 `LabPlot.bars(el, values, opts)`**：
   - `opts`：`{ labels, max, decimals: 2, highlight: idxOrArray, color: 1, hlColor: 2 }`。返回 `{ update(values, opts) }`。
4. **计算图 / 状态流转图 `LabPlot.graph(el, spec)`**：
   - `spec`：`{ width: 680, height: 220, nodes: [{id, label, sub, x, y, w, h, shape}], edges: [{id, from, to, label, curve, dx, dy}] }`（两节点间有多条边时设 `id` 与正负 `curve: 36 / -36` 画弧线！）。
   - 控制器：`g.apply({ label:{...}, sub:{...}, elabel:{...}, highlight:["n1"], done:["n2"], edges:[["a","b"]] })` 或 `g.reset()`。

### 4.3 数值工具 `LabMath` 与金标准比对 `Lab.check`
- `LabMath` 提供：`linspace`, `zeros`, `eye`, `dot`, `norm`, `T`, `matmul`, `matvec`, `sigmoid`, `tanh`, `relu`, `softmax(v, temp)`, `softmaxRows`, `causalMask`, `logsumexp`, `numGrad(f, x)`。
- 校验：`Lab.check("dw", jsDw, undefined, { tol: 1e-6, badge: "#sec-title" })` 会自动读取 `<script id="lab-golden">` 中的 `"dw"`，在页面底部生成校验面板并写入 `html[data-lab-checks]` 供 `study.py learn check --browser` 断言。
