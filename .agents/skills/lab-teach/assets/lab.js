/* =====================================================================
   lab.js — AI Lab 交互式课程页运行时（lab-teach skill 共享组件）
   用法（放在 </body> 前，先于课程内联脚本）：
     <script src="{{ASSETS}}/lab.js"></script>
     <script src="{{ASSETS}}/lab-math.js"></script>   <!-- 可选：数值工具 -->
     <script src="{{ASSETS}}/lab-plot.js"></script>   <!-- 可选：SVG 图表 -->
     <script> Lab.ready(() => { ... }) </script>
   自动完成：主题切换 · 目录与滚动高亮 · 阅读进度 · KaTeX 公式 · 代码高亮/行号/复制 ·
            逐步演示 .lab-stepper · 标签页 .lab-tabs · 代码讲解 .code-walk ·
            答案折叠 details.reveal · mermaid · Python 金标准校验面板
   API 文档：../references/html-lesson.md
   ===================================================================== */
(function () {
  "use strict";
  if (window.Lab) return;

  const ASSET_BASE = (function () {
    const s = document.currentScript && document.currentScript.src;
    return s ? s.replace(/[^/]*$/, "") : "";
  })();
  const MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";

  const readyQueue = [];
  const checks = [];
  let isReady = false;
  let goldenCache = null;
  let errorCount = 0;

  window.addEventListener("error", (e) => {
    errorCount++;
    checks.push({ name: "JS 错误", pass: false, detail: String(e.message || e) });
    renderChecks();
  });

  // ---------------------------------------------------------------- utils
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const el = (tag, attrs = {}, html) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") n.className = v;
      else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    if (html !== undefined) n.innerHTML = html;
    return n;
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function loadScript(src) {
    return new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = src; s.onload = () => res(); s.onerror = () => rej(new Error("load fail " + src));
      document.head.appendChild(s);
    });
  }
  function loadCss(href, id) {
    let l = id && document.getElementById(id);
    if (!l) { l = document.createElement("link"); l.rel = "stylesheet"; if (id) l.id = id; document.head.appendChild(l); }
    l.href = href;
    return l;
  }

  function fmt(x, d = 4) {
    if (Array.isArray(x)) return "[" + x.map((v) => fmt(v, d)).join(", ") + "]";
    if (typeof x !== "number") return String(x);
    if (!isFinite(x)) return String(x);
    if (x !== 0 && (Math.abs(x) < 1e-3 || Math.abs(x) >= 1e5)) return x.toExponential(Math.max(1, d - 1));
    return String(+x.toFixed(d));
  }

  // ---------------------------------------------------------------- theme
  function currentTheme() { return document.documentElement.getAttribute("data-theme") || "light"; }
  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("lab-theme", t); } catch (_) {}
    loadCss(ASSET_BASE + "vendor/hljs/" + (t === "dark" ? "github-dark" : "github") + ".min.css", "lab-hljs-theme");
    document.dispatchEvent(new CustomEvent("lab:theme", { detail: t }));
  }
  (function initTheme() {
    let t = null;
    try { t = localStorage.getItem("lab-theme"); } catch (_) {}
    if (!t) t = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", t);
  })();

  // ---------------------------------------------------------------- toolbar / progress
  function initChrome() {
    document.body.prepend(el("div", { id: "lab-progress" }));
    const bar = el("div", { class: "lab-toolbar" });
    bar.appendChild(el("button", { title: "切换深色/浅色", onclick: () => applyTheme(currentTheme() === "dark" ? "light" : "dark") }, "🌓"));
    if ($$("details.reveal").length) {
      let open = false;
      const b = el("button", { title: "展开/收起全部答案与选读" }, "展开全部");
      b.addEventListener("click", () => {
        open = !open;
        $$("details.reveal").forEach((d) => (d.open = open));
        b.textContent = open ? "收起全部" : "展开全部";
      });
      bar.appendChild(b);
    }
    bar.appendChild(el("button", { title: "回到顶部", onclick: () => scrollTo({ top: 0 }) }, "↑"));
    document.body.appendChild(bar);
    const prog = $("#lab-progress");
    const onScroll = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      prog.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    };
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---------------------------------------------------------------- TOC
  function slug(s) {
    return s.trim().toLowerCase().replace(/[\s·:：,，。()（）/\\?？!！'"`$]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "sec";
  }
  function initToc() {
    const toc = $("#lab-toc");
    const main = $(".lab-main") || document.body;
    const heads = $$("h2, h3", main).filter((h) => !h.closest(".lab-stepper, .callout, details, .card, .ref-grid"));
    const used = new Set();
    heads.forEach((h) => {
      if (!h.id) {
        let id = slug(h.textContent), i = 2;
        while (used.has(id) || document.getElementById(id)) id = slug(h.textContent) + "-" + i++;
        h.id = id;
      }
      used.add(h.id);
    });
    if (!toc || !heads.length) return;
    toc.innerHTML = "";
    toc.appendChild(el("div", { class: "toc-title" }, "本课目录"));
    const links = heads.map((h) => {
      const numEl = $(".num", h);
      const text = numEl
        ? numEl.textContent.trim() + " · " + h.textContent.slice(numEl.textContent.length).trim()
        : h.textContent.trim();
      const a = el("a", { href: "#" + h.id, class: h.tagName.toLowerCase() }, esc(text));
      toc.appendChild(a);
      return a;
    });
    if (!("IntersectionObserver" in window)) return;
    const map = new Map(heads.map((h, i) => [h, links[i]]));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((a) => a.classList.remove("active"));
          map.get(e.target).classList.add("active");
        }
      });
    }, { rootMargin: "0px 0px -70% 0px" });
    heads.forEach((h) => io.observe(h));
  }

  // ---------------------------------------------------------------- code blocks
  // 把 hljs 输出按行切分，并在跨行 <span> 处正确闭合/重开
  function splitHighlighted(html) {
    const lines = [];
    const stack = [];
    let cur = "";
    const re = /(<span[^>]*>)|(<\/span>)|(\n)|([^<\n]+|<(?!\/?span)[^>]*>)/g;
    let m;
    while ((m = re.exec(html))) {
      if (m[1]) { stack.push(m[1]); cur += m[1]; }
      else if (m[2]) { stack.pop(); cur += m[2]; }
      else if (m[3]) { cur += "</span>".repeat(stack.length); lines.push(cur); cur = stack.join(""); }
      else cur += m[4];
    }
    lines.push(cur);
    if (lines.length > 1 && lines[lines.length - 1].replace(/<[^>]+>/g, "") === "") lines.pop();
    return lines;
  }
  function parseRanges(spec) {
    const set = new Set();
    String(spec || "").split(",").forEach((part) => {
      const [a, b] = part.split("-").map((x) => parseInt(x, 10));
      if (isNaN(a)) return;
      for (let i = a; i <= (isNaN(b) ? a : b); i++) set.add(i);
    });
    return set;
  }
  function initCode() {
    $$("pre > code").forEach((code) => {
      const pre = code.parentElement;
      if (pre.classList.contains("mermaid") || code.classList.contains("language-mermaid")) return;
      if (!/language-|lang-/.test(code.className)) code.classList.add("language-python");
      if (!code.dataset.raw) code.dataset.raw = code.textContent.replace(/\n$/, "");
      if (window.hljs && !code.dataset.highlighted) { try { hljs.highlightElement(code); } catch (_) {} }
      const numbered = pre.hasAttribute("data-start") || pre.classList.contains("numbered") || pre.closest(".code-walk");
      if (numbered) {
        const start = parseInt(pre.getAttribute("data-start") || "1", 10);
        const hl = parseRanges(pre.getAttribute("data-hl"));
        code.innerHTML = splitHighlighted(code.innerHTML)
          .map((ln, i) => `<span class="line${hl.has(start + i) ? " hl" : ""}" data-n="${start + i}">${ln || " "}</span>`)
          .join("");
        code.classList.add("numbered");
      }
      const file = pre.getAttribute("data-file");
      const head = el("div", { class: "code-head" });
      const href = pre.getAttribute("data-href");
      head.appendChild(el("span", {}, file ? (href ? `<a href="${esc(href)}">${esc(file)}</a>` : esc(file)) : esc((code.className.match(/language-(\w+)/) || [, ""])[1])));
      const copy = el("button", { class: "copy-btn", type: "button" }, "复制");
      copy.addEventListener("click", () => {
        const text = code.dataset.raw || code.innerText;
        (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(
          () => { copy.textContent = "已复制 ✓"; setTimeout(() => (copy.textContent = "复制"), 1200); },
          () => { copy.textContent = "请手动复制"; }
        );
      });
      head.appendChild(copy);
      pre.prepend(head);
    });
  }

  // ---------------------------------------------------------------- code-walk
  function initCodeWalk() {
    $$(".code-walk").forEach((walk) => {
      const pre = $("pre", walk);
      const items = $$("ol.walk > li", walk);
      if (!pre || !items.length) return;
      const dim = walk.hasAttribute("data-dim");
      items.forEach((li) => {
        const tag = el("span", { class: "lines" }, li.dataset.lines ? "L" + li.dataset.lines : "");
        li.appendChild(tag);
        li.addEventListener("click", () => activate(li));
      });
      function activate(li) {
        items.forEach((x) => x.classList.toggle("active", x === li));
        const set = parseRanges(li.dataset.lines);
        let first = null;
        $$(".line", pre).forEach((ln) => {
          const on = set.has(parseInt(ln.dataset.n, 10));
          ln.classList.toggle("hl", on);
          ln.classList.toggle("dim", dim && set.size > 0 && !on);
          if (on && !first) first = ln;
        });
        if (first) pre.scrollTo({ top: Math.max(0, first.offsetTop - 60), behavior: "smooth" });
        walk.dispatchEvent(new CustomEvent("lab:walk", { detail: { index: items.indexOf(li), item: li } }));
      }
      activate(items[0]);
    });
  }

  // ---------------------------------------------------------------- stepper
  const steppers = new Map();
  function makeStepper(root) {
    if (steppers.has(root)) return steppers.get(root);
    const steps = $$(":scope > .step", root);
    const accumulate = root.dataset.mode === "accumulate";
    const head = el("div", { class: "stepper-head" });
    head.appendChild(el("div", { class: "stepper-title" }, esc(root.dataset.title || "逐步演示")));
    const dots = el("div", { class: "dots" });
    head.appendChild(dots);
    const foot = el("div", { class: "stepper-foot" });
    const prev = el("button", { class: "lab-btn", type: "button" }, "← 上一步");
    const next = el("button", { class: "lab-btn primary", type: "button" }, "下一步 →");
    foot.append(prev, el("span", { class: "hint" }, "也可用 ← → 键"), next);
    root.prepend(head);
    root.appendChild(foot);
    root.tabIndex = 0;
    steps.forEach((s, i) => {
      if (s.dataset.title && !$(".step-label", s)) s.prepend(el("div", { class: "step-label" }, `STEP ${i + 1} · ${esc(s.dataset.title)}`));
      dots.appendChild(el("button", { class: "dot", type: "button", title: s.dataset.title || "", onclick: () => go(i) }, String(i + 1)));
    });
    const listeners = [];
    const ctl = { index: 0, total: steps.length, go, next: () => go(ctl.index + 1), prev: () => go(ctl.index - 1), on: (fn) => { listeners.push(fn); fn(ctl.index, steps[ctl.index]); return ctl; } };
    function go(i) {
      i = Math.max(0, Math.min(steps.length - 1, i));
      ctl.index = i;
      steps.forEach((s, j) => s.classList.toggle("active", accumulate ? j <= i : j === i));
      $$(".dot", dots).forEach((d, j) => { d.classList.toggle("current", j === i); d.classList.toggle("done", j < i); });
      prev.disabled = i === 0;
      next.disabled = i === steps.length - 1;
      listeners.forEach((fn) => fn(i, steps[i]));
      root.dispatchEvent(new CustomEvent("lab:step", { detail: { index: i, step: steps[i] } }));
    }
    prev.addEventListener("click", ctl.prev);
    next.addEventListener("click", ctl.next);
    root.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { ctl.next(); e.preventDefault(); }
      if (e.key === "ArrowLeft") { ctl.prev(); e.preventDefault(); }
    });
    root.addEventListener("pointerenter", () => root.focus({ preventScroll: true }));
    steppers.set(root, ctl);
    go(0);
    return ctl;
  }

  // ---------------------------------------------------------------- tabs
  function initTabs() {
    $$(".lab-tabs").forEach((box) => {
      const tabs = $$(":scope > .tab", box);
      const bar = el("div", { class: "tab-bar" });
      const group = box.dataset.group;
      const btns = tabs.map((t, i) => {
        const b = el("button", { type: "button" }, esc(t.dataset.label || "Tab " + (i + 1)));
        b.addEventListener("click", () => {
          if (group) $$(`.lab-tabs[data-group="${group}"]`).forEach((o) => o._labSelect && o._labSelect(t.dataset.label));
          else select(t.dataset.label);
        });
        bar.appendChild(b);
        return b;
      });
      box.prepend(bar);
      function select(label) {
        let idx = tabs.findIndex((t) => t.dataset.label === label);
        if (idx < 0) idx = 0;
        tabs.forEach((t, i) => t.classList.toggle("active", i === idx));
        btns.forEach((b, i) => b.classList.toggle("active", i === idx));
      }
      box._labSelect = select;
      select(tabs[0] && tabs[0].dataset.label);
    });
  }

  // ---------------------------------------------------------------- reveal
  function initReveal() {
    $$("details.reveal").forEach((d) => {
      const kids = Array.from(d.children).filter((c) => c.tagName !== "SUMMARY");
      if (kids.length !== 1 || !kids[0].matches("div")) {
        const wrap = el("div", { class: "answer" });
        kids.forEach((k) => wrap.appendChild(k));
        d.appendChild(wrap);
      }
    });
  }

  // ---------------------------------------------------------------- math
  function renderMath(root = document.body) {
    if (!window.renderMathInElement) return;
    renderMathInElement(root, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false },
        { left: "$", right: "$", display: false },
      ],
      ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
      ignoredClasses: ["no-math"],
      throwOnError: false,
      trust: true,
      strict: "ignore",
    });
  }
  function tex(latex, display = false) {
    if (window.katex) {
      try { return katex.renderToString(latex, { displayMode: display, throwOnError: false, trust: true, strict: "ignore" }); } catch (_) {}
    }
    return esc(display ? `$$${latex}$$` : `$${latex}$`);
  }

  // ---------------------------------------------------------------- mermaid
  async function initMermaid() {
    const nodes = $$("pre.mermaid, div.mermaid");
    if (!nodes.length) return;
    nodes.forEach((n) => { if (!n.dataset.src) n.dataset.src = n.textContent; });
    try {
      if (!window.mermaid) await loadScript(MERMAID_CDN);
      mermaid.initialize({ startOnLoad: false, theme: currentTheme() === "dark" ? "dark" : "neutral", securityLevel: "loose", fontFamily: "inherit" });
      await mermaid.run({ nodes });
    } catch (e) {
      nodes.forEach((n) => n.insertAdjacentHTML("beforebegin", '<p class="small muted">（离线：mermaid 图无法渲染，下面是源码）</p>'));
    }
  }

  // ---------------------------------------------------------------- golden checks
  function parseGolden() {
    const g = document.getElementById("lab-golden");
    if (!g) return {};
    try { return JSON.parse(g.textContent || "{}"); } catch (e) {
      checks.push({ name: "lab-golden JSON", pass: false, detail: e.message });
      return {};
    }
  }
  function close(a, b, tol) {
    if (Array.isArray(a) || Array.isArray(b)) {
      if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
      return a.every((v, i) => close(v, b[i], tol));
    }
    if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= tol * (1 + Math.abs(b));
    return a === b;
  }
  /** Lab.check(name, actual, expected = Lab.golden[name], {tol, badge}) — JS 计算结果与 Python 金标准比对 */
  function check(name, actual, expected, opts = {}) {
    if (expected === undefined) expected = window.Lab.golden[name];
    const tol = opts.tol !== undefined ? opts.tol : 1e-6;
    const missing = expected === undefined;
    const pass = !missing && close(actual, expected, tol);
    const rec = { name, pass, detail: missing ? "golden 中缺少该键" : `js=${fmt(actual, 6)} py=${fmt(expected, 6)}` };
    const idx = checks.findIndex((c) => c.name === name);
    if (idx >= 0) checks[idx] = rec; else checks.push(rec);
    if (opts.badge) {
      const target = typeof opts.badge === "string" ? $(opts.badge) : opts.badge;
      if (target) {
        let b = $(".check-badge", target);
        if (!b) { b = el("span", { class: "check-badge" }); target.appendChild(b); }
        b.className = "check-badge " + (pass ? "pass" : "fail");
        b.textContent = pass ? "✓ 与 Python 一致" : "✗ 与 Python 不一致";
        b.title = rec.detail;
      }
    }
    renderChecks();
    return pass;
  }
  function renderChecks() {
    const pass = checks.filter((c) => c.pass).length;
    const fail = checks.length - pass;
    document.documentElement.setAttribute("data-lab-checks", `pass=${pass};fail=${fail};errors=${errorCount}`);
    if (!document.body || !checks.length) return;
    let box = $("#lab-checks");
    if (!box) {
      box = el("aside", { id: "lab-checks" });
      const host = $(".lab-footer") || $(".lab-main") || document.body;
      host.classList && host.classList.contains("lab-footer") ? host.before(box) : host.appendChild(box);
    }
    box.innerHTML = `<div class="ck-head">🔬 数值校验：${pass}/${checks.length} 项与 Python 金标准一致${fail ? " · ⚠️ 有不一致，请告诉 AI 老师" : ""}</div>` +
      checks.map((c) => `<div class="ck ${c.pass ? "pass" : "fail"}">${c.pass ? "✓" : "✗"} ${esc(c.name)} <span class="muted">${esc(c.detail || "")}</span></div>`).join("");
  }

  // ---------------------------------------------------------------- playground
  /**
   * Lab.playground(el, { title, params:[{name,label,min,max,step,value,fmt}],
   *   selects:[{name,label,options:[[value,text],...],value}], buttons:[{label,onClick(p,ctl)}],
   *   render(p, out, ctl), caption })
   */
  function playground(target, spec) {
    const root = typeof target === "string" ? $(target) : target;
    root.classList.add("lab-playground");
    root.innerHTML = "";
    if (spec.title) root.appendChild(el("div", { class: "pg-title" }, esc(spec.title)));
    const controls = el("div", { class: "pg-controls" });
    const p = {};
    const outputs = {};
    (spec.params || []).forEach((q) => {
      p[q.name] = q.value;
      const box = el("div", { class: "pg-control" });
      const id = "pg-" + Math.random().toString(36).slice(2, 8);
      const label = el("label", { for: id }, q.label || q.name);
      const out = el("output", {}, (q.fmt || fmt)(q.value));
      const input = el("input", { id, type: "range", min: q.min, max: q.max, step: q.step || (q.max - q.min) / 100, value: q.value });
      input.addEventListener("input", () => { p[q.name] = parseFloat(input.value); out.textContent = (q.fmt || fmt)(p[q.name]); update(); });
      outputs[q.name] = { input, out, q };
      box.append(label, out, input);
      controls.appendChild(box);
    });
    (spec.selects || []).forEach((q) => {
      p[q.name] = q.value !== undefined ? q.value : q.options[0][0];
      const box = el("div", { class: "pg-control" });
      const sel = el("select", {});
      q.options.forEach(([v, t]) => { const o = el("option", { value: v }, esc(t)); if (String(v) === String(p[q.name])) o.selected = true; sel.appendChild(o); });
      sel.addEventListener("change", () => { p[q.name] = isNaN(+sel.value) ? sel.value : +sel.value; update(); });
      box.append(el("label", {}, q.label || q.name), el("span"), sel);
      controls.appendChild(box);
    });
    if (controls.children.length) root.appendChild(controls);
    const ctl = { params: p, out: null, set, rerender: update };
    if (spec.buttons && spec.buttons.length) {
      const bb = el("div", { class: "pg-buttons" });
      spec.buttons.forEach((b) => bb.appendChild(el("button", { class: "lab-btn" + (b.primary ? " primary" : ""), type: "button", onclick: () => b.onClick(p, ctl) }, esc(b.label))));
      root.appendChild(bb);
    }
    const out = el("div", { class: "pg-out" });
    root.appendChild(out);
    ctl.out = out;
    if (spec.caption) root.appendChild(el("div", { class: "caption" }, spec.caption));
    function set(name, v) {
      p[name] = v;
      if (outputs[name]) { outputs[name].input.value = v; outputs[name].out.textContent = (outputs[name].q.fmt || fmt)(v); }
      update();
    }
    function update() { spec.render && spec.render(p, out, ctl); renderMath(out); }
    renderMath(root);
    update();
    return ctl;
  }
  /** Lab.readout(container, {"标签": 值 或 HTML}, digits) — KV 数值读数网格（可重复调用复用容器） */
  function readout(container, kv, d = 4) {
    let box = $(":scope > .pg-readout", container);
    if (!box) { box = el("div", { class: "pg-readout" }); container.appendChild(box); }
    box.innerHTML = Object.entries(kv).map(([k, v]) => `<div class="kv"><div class="k">${k}</div><div class="v">${typeof v === "number" || Array.isArray(v) ? fmt(v, d) : v}</div></div>`).join("");
    renderMath(box);
    return box;
  }

  // ---------------------------------------------------------------- boot
  async function boot() {
    initChrome();
    initReveal();
    initToc();
    const vend = ASSET_BASE + "vendor/";
    loadCss(vend + "katex/katex.min.css", "lab-katex");
    applyTheme(currentTheme());
    const jobs = [];
    if (!window.katex) jobs.push(loadScript(vend + "katex/katex.min.js").then(() => loadScript(vend + "katex/auto-render.min.js")));
    if (!window.hljs && $("pre > code")) jobs.push(loadScript(vend + "hljs/highlight.min.js"));
    await Promise.allSettled(jobs);
    renderMath();
    initCode();
    initCodeWalk();
    initTabs();
    $$(".lab-stepper").forEach(makeStepper);
    initMermaid();
    isReady = true;
    document.documentElement.setAttribute("data-lab-ready", "1");
    renderChecks();
    for (const fn of readyQueue.splice(0)) {
      try { fn(); } catch (e) { console.error(e); errorCount++; checks.push({ name: "Lab.ready 回调异常", pass: false, detail: e.message }); renderChecks(); }
    }
  }

  window.Lab = {
    version: "1.0",
    assetBase: ASSET_BASE,
    get golden() { return goldenCache || (goldenCache = parseGolden()); },
    ready(fn) { isReady ? fn() : readyQueue.push(fn); },
    $, $$, el, esc, fmt, tex,
    math: renderMath,
    check,
    playground,
    readout,
    stepper: (sel) => makeStepper(typeof sel === "string" ? $(sel) : sel),
    onStep: (sel, fn) => Lab.ready(() => Lab.stepper(sel).on(fn)),
    theme: currentTheme,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
