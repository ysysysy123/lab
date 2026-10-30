/* =====================================================================
   lab-plot.js — 零依赖 SVG 图表（主题感知、可重绘、适合滑块联动）
   API（详见 ../references/html-lesson.md）：
     const c = LabPlot.chart(el, {x:[-4,4], y:"auto", xLabel, yLabel, height:320});
     c.fn(Math.tanh, {label:"tanh", color:1}).line(xs, ys).scatter(xs, ys).vline(0).point(1, .76, {label:"x"}).draw();
     c.update(c => { c.fn(...); });           // 清空后重画（滑块回调里用）
     LabPlot.heatmap(el, M, {rowLabels, colLabels, decimals:2, scheme:"seq"|"div"}) -> {update(M)}
     LabPlot.bars(el, values, {labels, highlight}) -> {update(values)}
     LabPlot.graph(el, {nodes:[{id,label,sub,x,y}], edges:[{from,to,label}]}) -> 计算图/流程图控制器
   颜色：color 可为 1..6（主题色板）、CSS 颜色、或 "var(--c-warn)"。
   ===================================================================== */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const registry = new Set();
  document.addEventListener("lab:theme", () => registry.forEach((r) => r()));

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const color = (c, i = 0) => {
    if (c === undefined || c === null) c = (i % 6) + 1;
    if (typeof c === "number") return css("--plot-" + c) || "#4f46e5";
    if (c.startsWith("var(")) return css(c.slice(4, -1)) || c;
    return c;
  };
  const S = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  const resolve = (el) => (typeof el === "string" ? document.querySelector(el) : el);
  const f2 = (x) => (Math.abs(x) < 1e-12 ? "0" : +x.toPrecision(4) + "");

  function niceTicks(lo, hi, count = 6) {
    if (!(hi > lo)) return [lo];
    const span = hi - lo;
    const step0 = span / count;
    const mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const err = step0 / mag;
    const step = (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1) * mag;
    const out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toPrecision(12));
    return out;
  }

  let tip;
  function tooltip(show, text, evt) {
    if (!tip) { tip = document.createElement("div"); tip.className = "lab-tooltip"; document.body.appendChild(tip); }
    tip.style.opacity = show ? 1 : 0;
    if (show) { tip.textContent = text; tip.style.left = evt.clientX + 12 + "px"; tip.style.top = evt.clientY + 12 + "px"; }
  }

  // ================================================================ chart
  function chart(target, opts = {}) {
    const host = resolve(target);
    const W = opts.width || 640, H = opts.height || 340;
    const m = Object.assign({ top: opts.title ? 30 : 14, right: 18, bottom: opts.xLabel ? 44 : 28, left: opts.yLabel ? 56 : 44 }, opts.margin || {});
    let layers = [];
    const api = {};
    let svg;

    function extent() {
      let xs = [], ys = [];
      layers.forEach((L) => { if (L.xs) xs = xs.concat(L.xs.filter(isFinite)); if (L.ys) ys = ys.concat(L.ys.filter(isFinite)); });
      const X = opts.x || (xs.length ? [Math.min(...xs), Math.max(...xs)] : [0, 1]);
      let Y = opts.y && opts.y !== "auto" ? opts.y : null;
      if (!Y) {
        const lo = ys.length ? Math.min(...ys) : 0, hi = ys.length ? Math.max(...ys) : 1;
        const pad = (hi - lo || Math.abs(hi) || 1) * 0.08;
        Y = [lo - pad, hi + pad];
        if (opts.yZero) Y = [Math.min(0, Y[0]), Math.max(0, Y[1])];
      }
      return { X, Y };
    }

    api.draw = function () {
      const { X, Y } = extent();
      const sx = (x) => m.left + ((x - X[0]) / (X[1] - X[0])) * (W - m.left - m.right);
      const sy = (y) => H - m.bottom - ((y - Y[0]) / (Y[1] - Y[0])) * (H - m.top - m.bottom);
      api.sx = sx; api.sy = sy;
      if (svg) svg.remove();
      svg = S("svg", { viewBox: `0 0 ${W} ${H}`, class: "lab-plot", role: "img" });
      const clipId = "clip" + Math.random().toString(36).slice(2, 8);
      S("rect", { x: m.left, y: m.top, width: W - m.left - m.right, height: H - m.top - m.bottom }, S("clipPath", { id: clipId }, S("defs", {}, svg)));
      const defs = svg.querySelector("defs");
      const mk = S("marker", { id: clipId + "a", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, defs);
      S("path", { d: "M0,0 L10,5 L0,10 z", fill: "context-stroke" }, mk);

      const g = S("g", { class: "grid" }, svg);
      const xt = niceTicks(X[0], X[1], opts.xTicks || 8), yt = niceTicks(Y[0], Y[1], opts.yTicks || 6);
      if (opts.grid !== false) {
        xt.forEach((t) => S("line", { x1: sx(t), x2: sx(t), y1: m.top, y2: H - m.bottom }, g));
        yt.forEach((t) => S("line", { x1: m.left, x2: W - m.right, y1: sy(t), y2: sy(t) }, g));
      }
      const ax = S("g", { class: "axis" }, svg);
      const y0 = Y[0] <= 0 && Y[1] >= 0 ? sy(0) : H - m.bottom;
      const x0 = X[0] <= 0 && X[1] >= 0 ? sx(0) : m.left;
      S("line", { x1: m.left, x2: W - m.right, y1: y0, y2: y0 }, ax);
      S("line", { x1: x0, x2: x0, y1: m.top, y2: H - m.bottom }, ax);
      xt.forEach((t) => { const n = S("text", { x: sx(t), y: H - m.bottom + 16, "text-anchor": "middle" }, svg); n.textContent = f2(t); });
      yt.forEach((t) => { const n = S("text", { x: m.left - 7, y: sy(t) + 4, "text-anchor": "end" }, svg); n.textContent = f2(t); });
      if (opts.xLabel) { const n = S("text", { x: (m.left + W - m.right) / 2, y: H - 6, "text-anchor": "middle", class: "label" }, svg); n.textContent = opts.xLabel; }
      if (opts.yLabel) { const n = S("text", { x: 14, y: (m.top + H - m.bottom) / 2, "text-anchor": "middle", class: "label", transform: `rotate(-90 14 ${(m.top + H - m.bottom) / 2})` }, svg); n.textContent = opts.yLabel; }
      if (opts.title) { const n = S("text", { x: W / 2, y: 18, "text-anchor": "middle", class: "label" }, svg); n.textContent = opts.title; }

      const plot = S("g", { "clip-path": `url(#${clipId})` }, svg);
      const over = S("g", {}, svg);
      const legend = [];
      layers.forEach((L, i) => {
        const c = color(L.color, i);
        if (L.label && L.type !== "point" && L.type !== "text") legend.push([L.label, c, L.dash]);
        if (L.type === "line") {
          let d = "", pen = false;
          L.xs.forEach((x, j) => {
            const y = L.ys[j];
            if (!isFinite(y) || !isFinite(x)) { pen = false; return; }
            d += (pen ? "L" : "M") + sx(x).toFixed(2) + "," + sy(y).toFixed(2);
            pen = true;
          });
          if (L.fill) S("path", { d: d + `L${sx(L.xs[L.xs.length - 1])},${y0}L${sx(L.xs[0])},${y0}Z`, fill: c, opacity: 0.12, stroke: "none" }, plot);
          S("path", { d, fill: "none", stroke: c, "stroke-width": L.width || 2.4, "stroke-dasharray": L.dash ? "6 5" : null, "stroke-linejoin": "round", "stroke-linecap": "round" }, plot);
        } else if (L.type === "scatter") {
          L.xs.forEach((x, j) => {
            const dot = S("circle", { cx: sx(x), cy: sy(L.ys[j]), r: L.r || 4, fill: L.colors ? color(L.colors[j]) : c, opacity: L.opacity || 0.9, stroke: "var(--surface)", "stroke-width": 1 }, plot);
            dot.addEventListener("mousemove", (e) => tooltip(true, `(${f2(x)}, ${f2(L.ys[j])})`, e));
            dot.addEventListener("mouseleave", () => tooltip(false));
          });
        } else if (L.type === "vline") {
          S("line", { x1: sx(L.v), x2: sx(L.v), y1: m.top, y2: H - m.bottom, stroke: c, "stroke-width": 1.5, "stroke-dasharray": L.dash === false ? null : "5 4" }, over);
          if (L.label) { const n = S("text", { x: sx(L.v) + 4, y: m.top + 12, class: "annot", fill: c }, over); n.textContent = L.label; n.style.fill = c; }
        } else if (L.type === "hline") {
          S("line", { x1: m.left, x2: W - m.right, y1: sy(L.v), y2: sy(L.v), stroke: c, "stroke-width": 1.5, "stroke-dasharray": L.dash === false ? null : "5 4" }, over);
          if (L.label) { const n = S("text", { x: W - m.right - 4, y: sy(L.v) - 5, "text-anchor": "end", class: "annot" }, over); n.textContent = L.label; n.style.fill = c; }
        } else if (L.type === "point") {
          S("circle", { cx: sx(L.xs[0]), cy: sy(L.ys[0]), r: L.r || 5.5, fill: c, stroke: "var(--surface)", "stroke-width": 2 }, over);
          if (L.label) { const n = S("text", { x: sx(L.xs[0]) + 9, y: sy(L.ys[0]) - 8, class: "annot" }, over); n.textContent = L.label; }
        } else if (L.type === "text") {
          const n = S("text", { x: sx(L.xs[0]), y: sy(L.ys[0]), class: "annot", "text-anchor": L.anchor || "start" }, over);
          n.textContent = L.text; if (L.color) n.style.fill = c;
        } else if (L.type === "arrow") {
          S("line", { x1: sx(L.xs[0]), y1: sy(L.ys[0]), x2: sx(L.xs[1]), y2: sy(L.ys[1]), stroke: c, "stroke-width": L.width || 2, "marker-end": `url(#${clipId}a)` }, over);
          if (L.label) { const n = S("text", { x: sx(L.xs[1]) + 6, y: sy(L.ys[1]) - 6, class: "annot" }, over); n.textContent = L.label; n.style.fill = c; }
        }
      });
      if (opts.legend !== false && legend.length) {
        const lg = S("g", { class: "legend" }, svg);
        let x = m.left + 10;
        legend.forEach(([label, c, dash]) => {
          S("line", { x1: x, x2: x + 18, y1: m.top + 10, y2: m.top + 10, stroke: c, "stroke-width": 3, "stroke-dasharray": dash ? "5 3" : null }, lg);
          const t = S("text", { x: x + 23, y: m.top + 14 }, lg);
          t.textContent = label;
          x += 34 + label.length * 7.5;
        });
      }
      host.appendChild(svg);
      return api;
    };

    const push = (L) => { layers.push(L); return api; };
    api.fn = (f, o = {}) => {
      const dom = o.domain || opts.x || [-1, 1];
      const xs = [], ys = [];
      const n = o.samples || 240;
      for (let i = 0; i <= n; i++) { const x = dom[0] + ((dom[1] - dom[0]) * i) / n; xs.push(x); ys.push(f(x)); }
      return push(Object.assign({ type: "line", xs, ys }, o));
    };
    api.line = (xs, ys, o = {}) => push(Object.assign({ type: "line", xs, ys }, o));
    api.scatter = (xs, ys, o = {}) => push(Object.assign({ type: "scatter", xs, ys }, o));
    api.vline = (v, o = {}) => push(Object.assign({ type: "vline", v }, o));
    api.hline = (v, o = {}) => push(Object.assign({ type: "hline", v }, o));
    api.point = (x, y, o = {}) => push(Object.assign({ type: "point", xs: [x], ys: [y] }, o));
    api.text = (x, y, text, o = {}) => push(Object.assign({ type: "text", xs: [x], ys: [y], text }, o));
    api.arrow = (x1, y1, x2, y2, o = {}) => push(Object.assign({ type: "arrow", xs: [x1, x2], ys: [y1, y2] }, o));
    api.clear = () => { layers = []; return api; };
    let lastFn = null;
    api.update = (fn) => { lastFn = fn; layers = []; fn(api); return api.draw(); };
    api.opts = opts;
    registry.add(() => (lastFn ? api.update(lastFn) : api.draw()));
    return api;
  }

  // ================================================================ heatmap
  function heatmap(target, M0, opts = {}) {
    const host = resolve(target);
    let M = M0, svg;
    const api = {};
    function draw() {
      const R = M.length, C = M[0].length;
      const cell = opts.cell || Math.min(56, Math.floor(560 / Math.max(C, 1)));
      const left = opts.rowLabels ? 70 : 10, top = opts.colLabels ? 34 : 10;
      const W = left + C * cell + 10, H = top + R * cell + (opts.title ? 26 : 10);
      const vals = M.flat().filter(isFinite);
      const lo = opts.min !== undefined ? opts.min : Math.min(...vals);
      const hi = opts.max !== undefined ? opts.max : Math.max(...vals);
      const div = opts.scheme === "div";
      const cA = color(opts.color || 1), cB = color(opts.colorNeg || 4);
      if (svg) svg.remove();
      svg = S("svg", { viewBox: `0 0 ${W} ${H}`, class: "lab-plot", style: `max-width:${W}px` });
      M.forEach((row, i) => row.forEach((v, j) => {
        let fill, op;
        if (!isFinite(v)) { fill = css("--surface-2"); op = 1; }
        else if (div) { const a = Math.max(Math.abs(lo), Math.abs(hi)) || 1; fill = v >= 0 ? cA : cB; op = 0.08 + 0.85 * Math.min(1, Math.abs(v) / a); }
        else { fill = cA; op = 0.06 + 0.88 * (hi > lo ? (v - lo) / (hi - lo) : 0.5); }
        const r = S("rect", { x: left + j * cell + 1, y: top + i * cell + 1, width: cell - 2, height: cell - 2, rx: 4, fill, "fill-opacity": op }, svg);
        const label = `${opts.rowLabels ? opts.rowLabels[i] : i} → ${opts.colLabels ? opts.colLabels[j] : j}: ${isFinite(v) ? f2(v) : v}`;
        r.addEventListener("mousemove", (e) => tooltip(true, label, e));
        r.addEventListener("mouseleave", () => tooltip(false));
        if (opts.onClick) r.addEventListener("click", () => opts.onClick(i, j, v));
        if (opts.showValues !== false && cell >= 30) {
          const t = S("text", { x: left + j * cell + cell / 2, y: top + i * cell + cell / 2 + 4, "text-anchor": "middle", class: "cell-text" }, svg);
          t.textContent = isFinite(v) ? v.toFixed(opts.decimals !== undefined ? opts.decimals : 2) : v === -Infinity ? "−∞" : "·";
          t.style.fill = op > 0.55 ? "#fff" : css("--text");
        }
      }));
      (opts.colLabels || []).forEach((l, j) => { const t = S("text", { x: left + j * cell + cell / 2, y: top - 10, "text-anchor": "middle", class: "label" }, svg); t.textContent = l; });
      (opts.rowLabels || []).forEach((l, i) => { const t = S("text", { x: left - 8, y: top + i * cell + cell / 2 + 4, "text-anchor": "end", class: "label" }, svg); t.textContent = l; });
      if (opts.title) { const t = S("text", { x: W / 2, y: H - 6, "text-anchor": "middle", class: "label" }, svg); t.textContent = opts.title; }
      host.appendChild(svg);
    }
    api.update = (M1) => { M = M1; draw(); return api; };
    registry.add(draw);
    draw();
    return api;
  }

  // ================================================================ bars
  function bars(target, values0, opts = {}) {
    const host = resolve(target);
    let values = values0, svg;
    const api = {};
    function draw() {
      const n = values.length;
      const W = opts.width || 640, H = opts.height || 260, m = { top: 16, right: 12, bottom: 34, left: 44 };
      const hi = opts.max !== undefined ? opts.max : Math.max(...values, 0) * 1.12 || 1;
      const lo = Math.min(0, ...values);
      const sy = (y) => H - m.bottom - ((y - lo) / (hi - lo)) * (H - m.top - m.bottom);
      const bw = (W - m.left - m.right) / n;
      if (svg) svg.remove();
      host.querySelectorAll("svg").forEach((s) => s.remove());
      svg = S("svg", { viewBox: `0 0 ${W} ${H}`, class: "lab-plot" });
      const g = S("g", { class: "grid" }, svg);
      niceTicks(lo, hi, 5).forEach((t) => {
        S("line", { x1: m.left, x2: W - m.right, y1: sy(t), y2: sy(t) }, g);
        const tx = S("text", { x: m.left - 6, y: sy(t) + 4, "text-anchor": "end" }, svg); tx.textContent = f2(t);
      });
      values.forEach((v, i) => {
        const hl = opts.highlight === i || (Array.isArray(opts.highlight) && opts.highlight.includes(i));
        const x = m.left + i * bw + bw * 0.15;
        S("rect", { x, y: Math.min(sy(v), sy(0)), width: bw * 0.7, height: Math.abs(sy(v) - sy(0)), rx: 4, fill: color(hl ? opts.hlColor || 2 : opts.color || 1), opacity: hl ? 1 : 0.85 }, svg);
        const t = S("text", { x: x + bw * 0.35, y: Math.min(sy(v), sy(0)) - 5, "text-anchor": "middle", class: "annot" }, svg);
        t.textContent = v.toFixed(opts.decimals !== undefined ? opts.decimals : 2);
        if (opts.labels) { const l = S("text", { x: x + bw * 0.35, y: H - m.bottom + 16, "text-anchor": "middle" }, svg); l.textContent = opts.labels[i]; }
      });
      host.appendChild(svg);
    }
    api.update = (v, o) => { values = v; if (o) Object.assign(opts, o); draw(); return api; };
    registry.add(draw);
    draw();
    return api;
  }

  // ================================================================ graph（计算图 / 流程图 / 状态机）
  function graph(target, spec) {
    const host = resolve(target);
    const W = spec.width || 640, H = spec.height || 260;
    let svg;
    const state = { label: {}, sub: {}, hl: new Set(), done: new Set(), ehl: new Set(), elabel: {} };
    const nodeById = Object.fromEntries(spec.nodes.map((n) => [n.id, n]));
    const ek = (a, b) => a + "→" + b;
    function draw() {
      if (svg) svg.remove();
      svg = S("svg", { viewBox: `0 0 ${W} ${H}`, class: "lab-plot" });
      const defs = S("defs", {}, svg);
      const mk = S("marker", { id: "gm" + spec.id, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" }, defs);
      S("path", { d: "M0,0 L10,5 L0,10 z", fill: css("--plot-axis") }, mk);
      const mk2 = S("marker", { id: "gmh" + spec.id, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" }, defs);
      S("path", { d: "M0,0 L10,5 L0,10 z", fill: css("--c-warn") }, mk2);
      (spec.edges || []).forEach((e) => {
        const a = nodeById[e.from], b = nodeById[e.to];
        const aw = (a.w || 96) / 2, bw = (b.w || 96) / 2;
        const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
        const ox = dx / len, oy = dy / len;
        const shrinkA = Math.min(aw / Math.abs(ox || 1e-9), (a.h || 46) / 2 / Math.abs(oy || 1e-9));
        const shrinkB = Math.min(bw / Math.abs(ox || 1e-9), (b.h || 46) / 2 / Math.abs(oy || 1e-9)) + 3;
        const x1 = a.x + ox * shrinkA, y1 = a.y + oy * shrinkA, x2 = b.x - ox * shrinkB, y2 = b.y - oy * shrinkB;
        const key = e.id || ek(e.from, e.to);
        const hl = state.ehl.has(key);
        if (e.curve) {
          const cx = (x1 + x2) / 2 - oy * e.curve, cy = (y1 + y2) / 2 + ox * e.curve;
          S("path", { d: `M${x1.toFixed(1)},${y1.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`, class: "edge" + (hl ? " hl" : ""), "marker-end": `url(#${hl ? "gmh" : "gm"}${spec.id})` }, svg);
        } else {
          S("line", { x1, y1, x2, y2, class: "edge" + (hl ? " hl" : ""), "marker-end": `url(#${hl ? "gmh" : "gm"}${spec.id})` }, svg);
        }
        const lab = state.elabel[key] !== undefined ? state.elabel[key] : e.label;
        if (lab) {
          const lx = (a.x + b.x) / 2 - (e.curve ? oy * e.curve * 0.55 : 0) + (e.dx || 0);
          const ly = (a.y + b.y) / 2 + (e.curve ? ox * e.curve * 0.55 : -7) + (e.dy || 0);
          const t = S("text", { x: lx, y: ly, "text-anchor": "middle", class: "edge-label" }, svg);
          t.textContent = lab;
        }
      });
      spec.nodes.forEach((n) => {
        const g = S("g", { class: "node" + (state.hl.has(n.id) ? " hl" : "") + (state.done.has(n.id) ? " done" : "") }, svg);
        const w = n.w || 96, h = n.h || 46;
        if (n.shape === "circle") S("circle", { cx: n.x, cy: n.y, r: h / 2 }, g);
        else S("rect", { x: n.x - w / 2, y: n.y - h / 2, width: w, height: h, rx: 10 }, g);
        const label = state.label[n.id] !== undefined ? state.label[n.id] : n.label;
        const sub = state.sub[n.id] !== undefined ? state.sub[n.id] : n.sub;
        const t = S("text", { x: n.x, y: n.y + (sub ? -3 : 4), "text-anchor": "middle" }, g); t.textContent = label;
        if (sub) { const s2 = S("text", { x: n.x, y: n.y + 13, "text-anchor": "middle", class: "sub" }, g); s2.textContent = sub; }
      });
      host.appendChild(svg);
    }
    spec.id = spec.id || Math.random().toString(36).slice(2, 7);
    const api = {
      set(id, { label, sub } = {}) { if (label !== undefined) state.label[id] = label; if (sub !== undefined) state.sub[id] = sub; draw(); return api; },
      highlight(ids = []) { state.hl = new Set(ids); draw(); return api; },
      done(ids = []) { state.done = new Set(ids); draw(); return api; },
      edges(pairs = []) { state.ehl = new Set(pairs.map((p) => (Array.isArray(p) ? ek(p[0], p[1]) : p))); draw(); return api; },
      edgeLabel(a, b, text) { if (text === undefined) state.elabel[a] = b; else state.elabel[ek(a, b)] = text; draw(); return api; },
      reset() { Object.assign(state, { label: {}, sub: {}, hl: new Set(), done: new Set(), ehl: new Set(), elabel: {} }); draw(); return api; },
      /** 批量设置：apply({sub:{x:"g=1"}, highlight:[...], done:[...], edges:[[a,b]], elabel:{"a→b":"..."}}) */
      apply(cfg = {}) {
        Object.entries(cfg.label || {}).forEach(([k, v]) => (state.label[k] = v));
        Object.entries(cfg.sub || {}).forEach(([k, v]) => (state.sub[k] = v));
        Object.entries(cfg.elabel || {}).forEach(([k, v]) => (state.elabel[k] = v));
        if (cfg.highlight) state.hl = new Set(cfg.highlight);
        if (cfg.done) state.done = new Set(cfg.done);
        if (cfg.edges) state.ehl = new Set(cfg.edges.map((p) => (Array.isArray(p) ? ek(p[0], p[1]) : p)));
        draw(); return api;
      },
    };
    registry.add(draw);
    draw();
    return api;
  }

  window.LabPlot = { chart, heatmap, bars, graph, niceTicks, color };
})();
