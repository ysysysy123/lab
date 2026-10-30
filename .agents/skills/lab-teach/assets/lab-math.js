/* =====================================================================
   lab-math.js — 交互实验用的小型数值工具（无依赖，行为对齐 NumPy 常用函数）
   约定：向量 = number[]，矩阵 = number[][]（行优先）。
   注意：浏览器里的数值只用于演示；写进课程的关键数字必须来自 Python 金标准
        （见 references/sources-and-verification.md「正确性协议」），并用 Lab.check 比对。
   ===================================================================== */
(function () {
  "use strict";
  const M = {};

  M.range = (n) => Array.from({ length: n }, (_, i) => i);
  M.linspace = (a, b, n = 100) => (n === 1 ? [a] : M.range(n).map((i) => a + ((b - a) * i) / (n - 1)));
  M.zeros = (r, c) => (c === undefined ? new Array(r).fill(0) : M.range(r).map(() => new Array(c).fill(0)));
  M.eye = (n) => M.range(n).map((i) => M.range(n).map((j) => (i === j ? 1 : 0)));
  M.shape = (A) => (Array.isArray(A[0]) ? [A.length, A[0].length] : [A.length]);

  M.sum = (v) => v.reduce((s, x) => s + x, 0);
  M.mean = (v) => M.sum(v) / v.length;
  M.std = (v) => { const m = M.mean(v); return Math.sqrt(M.mean(v.map((x) => (x - m) ** 2))); };
  M.max = (v) => Math.max(...v);
  M.min = (v) => Math.min(...v);
  M.argmax = (v) => v.reduce((bi, x, i) => (x > v[bi] ? i : bi), 0);
  M.dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  M.norm = (v) => Math.sqrt(M.dot(v, v));
  M.round = (x, d = 4) => (Array.isArray(x) ? x.map((y) => M.round(y, d)) : +x.toFixed(d));

  M.T = (A) => A[0].map((_, j) => A.map((row) => row[j]));
  M.matmul = (A, B) => {
    const Bt = M.T(B);
    return A.map((row) => Bt.map((col) => M.dot(row, col)));
  };
  M.matvec = (A, v) => A.map((row) => M.dot(row, v));
  M.map = (A, f) => (Array.isArray(A) ? A.map((x) => M.map(x, f)) : f(A));
  M.add = (A, B) => (Array.isArray(A) ? A.map((x, i) => M.add(x, Array.isArray(B) ? B[i] : B)) : A + B);
  M.sub = (A, B) => (Array.isArray(A) ? A.map((x, i) => M.sub(x, Array.isArray(B) ? B[i] : B)) : A - B);
  M.mul = (A, B) => (Array.isArray(A) ? A.map((x, i) => M.mul(x, Array.isArray(B) ? B[i] : B)) : A * B);
  M.scale = (A, k) => M.map(A, (x) => x * k);

  M.sigmoid = (x) => (x >= 0 ? 1 / (1 + Math.exp(-x)) : Math.exp(x) / (1 + Math.exp(x)));
  M.tanh = Math.tanh;
  M.relu = (x) => Math.max(0, x);
  M.logsumexp = (v) => { const m = M.max(v); return m + Math.log(M.sum(v.map((x) => Math.exp(x - m)))); };
  M.softmax = (v, temp = 1) => {
    const z = v.map((x) => x / temp);
    const m = M.max(z);
    const e = z.map((x) => Math.exp(x - m));
    const s = M.sum(e);
    return e.map((x) => x / s);
  };
  M.softmaxRows = (A, temp = 1) => A.map((r) => M.softmax(r, temp));
  /** 下三角因果掩码：j>i 置为 -Infinity */
  M.causalMask = (A) => A.map((r, i) => r.map((x, j) => (j > i ? -Infinity : x)));

  /** 中心差分数值梯度：f(x:number[]) -> number */
  M.numGrad = (f, x, eps = 1e-6) =>
    x.map((_, i) => {
      const xp = x.slice(), xm = x.slice();
      xp[i] += eps; xm[i] -= eps;
      return (f(xp) - f(xm)) / (2 * eps);
    });

  /** 可复现随机数：mulberry32 + Box-Muller（与 NumPy 序列不同！需要对齐 Python 时请把数据写进 golden） */
  M.rng = (seed = 42) => {
    let a = seed >>> 0;
    const random = () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const randn = () => {
      let u = 0, v = 0;
      while (u === 0) u = random();
      while (v === 0) v = random();
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    };
    return { random, randn, uniform: (lo, hi) => lo + (hi - lo) * random(), normal: (mu = 0, s = 1) => mu + s * randn() };
  };

  window.LabMath = M;
})();
