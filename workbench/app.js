(() => {
  'use strict';

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const plain = (s) => String(s ?? '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*|`/g, '');
  const root = document.getElementById('appRoot');

  // 16 节课程元数据（前 10 节对应仓库真实 HTML 交互课，后 6 节对应 P2-P5 导读）
  const LESSONS_META = [
    { id: 'b01', taskKey: 'lesson:w01-自动微分与P1:1', category: 'base', source: 'lab HTML', title: '标量计算图与 Value.backward()', time: 20, desc: '理解反向传播为什么要按逆拓扑顺序执行，为什么梯度从 1 开始，以及分支梯度为什么必须累加。', point: '反向传播不是“倒着做一遍前向”，而是沿计算图逐层应用链式法则。', steps: ['识别计算图的父子依赖与拓扑顺序', '在一个分叉图中观察 += 累加梯度', '与真实 micro_autograd 代码逐段对应'], src: '/files/学习/w01-自动微分与P1/lessons/0001-scalar-autograd-chain.html', code: '/files/concepts/w01_micro_autograd.py' },
    { id: 'b02', taskKey: 'lesson:w01-自动微分与P1:2', category: 'base', source: 'lab HTML', title: 'Softmax + 交叉熵梯度 p − y', time: 20, desc: '用小数字例子串起分类概率、损失函数与梯度，理解 softmax 与交叉熵为何方便组合。', point: '对 logits 求导，Softmax + 交叉熵可以化简为 p − y。', steps: ['从两类概率出发写出交叉熵', '沿求导规则推出 p − y', '检查数值稳定与极端 logits'], src: '/files/学习/w01-自动微分与P1/lessons/0002-softmax-cross-entropy-grad.html' },
    { id: 'b03', taskKey: 'lesson:w01-自动微分与P1:3', category: 'base', source: 'lab HTML', title: 'NumPy MLP 的矩阵反向传播', time: 25, desc: '通过 Shape 对齐理解 dW=AᵀdZ，连接标量自动微分与批量训练。', point: '先对齐维度，再写矩阵反向传播，比死记梯度公式更稳健。', steps: ['标记批量维与隐藏层维度', '在 NumPy 中检查 dW、dA 的 shape', '连接 MNIST 两层 MLP 实现'], src: '/files/学习/w01-自动微分与P1/lessons/0003-numpy-matrix-bp-shapes.html', code: '/files/projects/p1-tiny-llm/src/w01_mlp_mnist.py' },
    { id: 'b04', taskKey: 'lesson:w01-自动微分与P1:4', category: 'base', source: 'lab HTML', title: 'Log-Sum-Exp 与 PyTorch CrossEntropy', time: 20, desc: '理解为什么减去最大 logit 可以防止数值溢出，以及 PyTorch 的交叉熵计算。', point: '数值稳定是实现正确性的一部分，不只是优化技巧。', steps: ['观察大 logit 下 exp 的数值风险', '解释为什么平移 logits 不改变 Softmax', '对照 PyTorch API 和 MNIST 任务'], src: '/files/学习/w01-自动微分与P1/lessons/0004-logsumexp-pytorch-mnist.html', code: '/files/projects/p1-tiny-llm/src/w01_mlp_mnist.py' },
    { id: 'b05', taskKey: 'lesson:w01-自动微分与P1:5', category: 'base', source: 'lab HTML', title: 'Keshav 三遍论文阅读法', time: 15, desc: '快速识别问题、方法、证据与局限，降低无效精读成本。', point: '读论文先判断它是否值得深入，再花时间核验核心方法和结果。', steps: ['第一遍看问题与贡献', '第二遍看核心方法与实验', '第三遍检查假设、设计与局限'], src: '/files/学习/w01-自动微分与P1/lessons/0005-how-to-read-a-paper.html' },
    { id: 't01', taskKey: 'lesson:w03-Transformer与现代LLM架构:1', category: 'llm', source: 'lab HTML', title: '缩放点积注意力 SDPA', time: 25, desc: '理解 QKᵀ/√dₖ、Softmax 权重与值向量加权，关联“软检索”直觉。', point: 'Attention 用查询与键的匹配分数，为值向量分配数据依赖的权重。', steps: ['用 3 个 token、2 维向量计算注意力得分', '解释除以 √dₖ 的方差动机', '进入交互实验拖动 Softmax 参数'], src: '/files/学习/w03-Transformer与现代LLM架构/lessons/0001-scaled-dot-product-attention.html' },
    { id: 't02', taskKey: 'lesson:w03-Transformer与现代LLM架构:2', category: 'llm', source: 'lab HTML', title: '因果掩码与多头注意力', time: 25, desc: '弄清未来 token 为什么要屏蔽、mask 的注入位置和多头 Shape 转换。', point: '因果注意力限制信息流向；多头注意力则并行处理不同子空间。', steps: ['标记不可见的未来位置', '检查 (B,T,C) 到 (B,H,T,d) 的变化', '定位掩码与 Softmax 的先后关系'], src: '/files/学习/w03-Transformer与现代LLM架构/lessons/0002-causal-mask-and-mha.html' },
    { id: 't03', taskKey: 'lesson:w03-Transformer与现代LLM架构:3', category: 'llm', source: 'lab HTML', title: 'RoPE：相对位置的旋转表示', time: 25, desc: '用二维旋转直观理解位置编码，以及相对位置差如何进入 QK 内积。', point: 'RoPE 把位置变为旋转角度，使查询和键的内积显式依赖相对位移。', steps: ['先理解二维旋转矩阵', '推导 RₘᵀRₙ=Rₙ₋ₘ', '连接注意力源码的奇偶通道处理'], src: '/files/学习/w03-Transformer与现代LLM架构/lessons/0003-rope-rotary-position-embedding.html' },
    { id: 't04', taskKey: 'lesson:w03-Transformer与现代LLM架构:4', category: 'llm', source: 'lab HTML', title: '残差连接、Pre-Norm 与 RMSNorm', time: 25, desc: '理解深层网络的梯度路径，以及 RMSNorm 与 LayerNorm 的结构差异。', point: '残差提供直接的信息和梯度路径，归一化影响训练动态与数值稳定。', steps: ['展开 y=x+F(x) 的梯度', '比较 Pre-Norm 和 Post-Norm', '找出现代 LLM 中 RMSNorm 的作用'], src: '/files/学习/w03-Transformer与现代LLM架构/lessons/0004-residual-rmsnorm-prenorm.html' },
    { id: 't05', taskKey: 'lesson:w03-Transformer与现代LLM架构:5', category: 'llm', source: 'lab HTML', title: 'SwiGLU、GQA 与 KV Cache', time: 25, desc: '从门控前馈层和 KV 头共享出发，理解参数与推理显存成本。', point: '推理优化需要清楚区分模型参数量、KV Cache 和计算吞吐。', steps: ['拆解 SwiGLU 门控路径', '计算 GQA/MHA 的 KV 头数量差异', '联系 P1 训练与部署任务'], src: '/files/学习/w03-Transformer与现代LLM架构/lessons/0005-swiglu-and-gqa-kv-cache.html' },
    { id: 'a01', category: 'agent', source: '项目导读', title: 'ReAct：让模型通过工具形成闭环', time: 20, desc: '结合 P2 已有的 react_loop_starter.py，理解状态、工具调用、观察和熔断。', point: 'Agent 的核心不只是生成文本，而是把决策与外部环境反馈连接起来。', steps: ['查看 P2 的 ReAct 源码', '用状态机梳理 Thought/Action/Observation', '确定最大步数与参数校验点'], src: '/files/projects/p2-scratch-agent/README.md', code: '/files/projects/p2-scratch-agent/src/react_loop_starter.py' },
    { id: 'a02', category: 'agent', source: '项目导读', title: '混合检索与 RRF 融合', time: 20, desc: '以 P2 的 RAG 里程碑为上下文，区分 BM25、Dense Retrieval、Reranker 的职责。', point: '不同检索器的排序偏好不同；融合能否有效必须靠公开指标验证。', steps: ['辨别词法匹配与向量语义匹配', '理解倒数秩融合为什么只使用排名', '设计 Recall@5 的最小基线对比'], src: '/files/projects/p2-scratch-agent/README.md' },
    { id: 'a03', category: 'agent', source: '项目导读', title: 'MCP 与 Coding Agent 自纠错', time: 20, desc: '从工具接口到 Pytest 反馈循环，学习如何安全运行、记录并评估 Agent 行为。', point: '“自己修复”不是成功保证；必须比较单次生成和多轮修复的实际结果。', steps: ['画出 Planner→Coder→Runner→Feedback', '区分工具协议与决策策略', '检查评测中重试次数与预算是否公平'], src: '/files/projects/p2-scratch-agent/README.md' },
    { id: 'r01', category: 'robot', source: '项目导读', title: '2D IK：雅可比与阻尼伪逆', time: 20, desc: '以 P4 真实玩具脚本为起点，理解末端误差、雅可比和阻尼最小二乘更新。', point: '逆运动学把“想让末端去哪”转化成关节角应如何变化。', steps: ['查看 P4 的 ik_2d_toy.py', '用交互实验观察末端位置误差', '理解接近奇异位形时阻尼的价值'], src: '/files/projects/p4-robot-learning/README.md', code: '/files/projects/p4-robot-learning/src/ik_2d_toy.py' },
    { id: 'r02', category: 'robot', source: '项目导读', title: '模仿学习：ACT 与 Diffusion Policy', time: 25, desc: '从行为克隆的多峰动作问题出发，区分 ACT 的动作分块与 Diffusion Policy 的生成式策略。', point: '不同策略的归纳偏置不同，性能差异需要在可复现任务中对比。', steps: ['对比单步行为克隆与多模态轨迹', '理解 Action Chunking 的作用', '阅读 PushT/ALOHA 的实验定义'], src: '/files/projects/p4-robot-learning/README.md' },
    { id: 'r03', category: 'robot', source: '项目导读', title: 'VLA 与分层具身智能体', time: 25, desc: '关联 P4 的 VLA 与 P5 的闭环 Capstone，理解高层规划、技能策略和执行后状态验证。', point: '长任务的可靠性既取决于低层动作策略，也取决于错误检测与重规划。', steps: ['区分 VLM/LLM 规划器与 VLA 策略', '阅读 P5 系统架构与接口', '设计开环/闭环的公平成功率对比'], src: '/files/projects/p5-embodied-capstone/README.md' }
  ];

  const LOCAL_KEY = 'ai-lab:studio:v2';
  const loadLocal = () => {
    try { return JSON.parse(localStorage.getItem(LOCAL_KEY) || '{}') || {}; }
    catch { return {}; }
  };
  let local = loadLocal();
  local.ideas ||= [];
  local.extraLessons ||= {};
  local.timer ||= { duration: 15, remaining: 15 * 60000, endAt: null, status: 'idle' };

  function saveLocal() {
    try { localStorage.setItem(LOCAL_KEY, JSON.stringify(local)); } catch {}
  }

  let data = null;
  let page = 'home';
  let activeLessonId = 't01';
  let lessonFilter = 'all';
  let showHomeIframe = false;
  let showLessonIframe = true;
  let projectTab = 'plan';
  let cardFilter = 'due';
  let activeCardIdx = 0;
  let cardAnswerShown = false;
  let activeDemo = 'attention';
  let reactPos = 0;
  let q1 = 0.35, q2 = 0.65;

  let toastTimer;
  function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
  }

  function isLessonDone(l) {
    if (l.taskKey && data?.tasks?.[l.taskKey]) return !!data.tasks[l.taskKey].done;
    return !!local.extraLessons[l.id];
  }

  async function apiPost(endpoint, payload) {
    const dot = document.getElementById('gitDot');
    const txt = document.getElementById('gitStatusText');
    if (dot) dot.classList.add('syncing');
    if (txt) txt.textContent = '正在保存并同步 GitHub…';
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || '操作失败');
    data = json;
    updateChrome();
    render();
    return json;
  }

  function updateChrome() {
    if (!data) return;
    document.getElementById('dateText').textContent = new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    }).format(new Date(data.date + 'T12:00:00'));

    const dueCards = (data.cards || []).filter((c) => c.is_due);
    const doneLessons = LESSONS_META.filter((l) => isLessonDone(l)).length;
    const lcDone = (data.leetcode || []).filter((x) => x.done).length;
    const lcTotal = (data.leetcode || []).length || 51;

    document.getElementById('navLessonBadge').textContent = `${doneLessons}/${LESSONS_META.length}`;
    document.getElementById('navPlanBadge').textContent = `W${String(data.active).padStart(2, '0')}`;
    document.getElementById('navLcBadge').textContent = `${lcDone}/${lcTotal}`;
    const cardBadge = document.getElementById('navCardBadge');
    cardBadge.textContent = dueCards.length ? `${dueCards.length}到期` : '已清零';
    cardBadge.classList.toggle('warn', dueCards.length > 0);

    const g = data.git || {};
    const dot = document.getElementById('gitDot');
    const txt = document.getElementById('gitStatusText');
    if (dot) dot.classList.toggle('syncing', !!g.running);
    if (txt) txt.textContent = g.last_time ? `${g.last_msg} · ${g.last_time}` : `自动同步就绪 · ${(g.head || '').slice(0, 7)}`;
    const sideGit = document.getElementById('sidebarGitHead');
    if (sideGit) sideGit.textContent = `最新提交: ${g.head || '本地仓库'}`;
  }

  function currentPlanTask() {
    if (!data) return null;
    const week = data.weeks.find((w) => w.number === data.active) || data.weeks[0];
    if (!week) return null;
    for (const id of week.tasks) {
      const t = data.tasks[id];
      if (t && !t.done) return t;
    }
    return null;
  }

  function currentNextLesson() {
    return LESSONS_META.find((l) => !isLessonDone(l)) || LESSONS_META[0];
  }

  function currentLcTask() {
    if (!data?.leetcode) return null;
    return data.leetcode.find((item) => !item.done) || data.leetcode[0];
  }

  function lastTomorrowCue() {
    if (!data?.history) return '';
    if (data.daily?.tomorrow) return data.daily.tomorrow;
    const prev = data.history.find((h) => h.date < data.date && h.tomorrow);
    return prev ? `${prev.tomorrow} (${prev.date})` : '';
  }

  // ==================== 页面 1: 今日驾驶舱 (ADHD 零决策首页) ====================
  function renderHome() {
    const planTasks = Object.values(data.tasks).filter((t) => t.kind === '周计划');
    const planDone = planTasks.filter((t) => t.done).length;
    const doneLessons = LESSONS_META.filter((l) => isLessonDone(l)).length;
    const lcDone = (data.leetcode || []).filter((x) => x.done).length;
    const lcTotal = (data.leetcode || []).length || 51;
    const dueCards = (data.cards || []).filter((c) => c.is_due);
    const activeWeekObj = data.weeks.find((w) => w.number === data.active) || { number: 0, title: '切换周', tasks: [] };

    const mainTask = currentPlanTask();
    const nextLesson = currentNextLesson();
    const todayLc = currentLcTask();
    const cue = lastTomorrowCue();
    const curDueCard = dueCards[0] || null;

    return `
      <div class="hero">
        <div class="hero-content">
          <div class="eyebrow">W${String(activeWeekObj.number).padStart(2, '0')} · ${esc(activeWeekObj.title)}</div>
          <h1>今天不用翻文件，按顺序做完这 3 张卡就收工。</h1>
          <p>${cue ? `🧭 <strong>上次留下的「今天第一件事」：</strong>${esc(cue)}` : '① 翻完今日到期复习卡（10分钟） → ② 推进下方唯一主块任务 → ③ 打卡 1 道力扣题。每次勾选都会自动保存到本地 Markdown 并同步 GitHub。'}</p>
          <div class="hero-actions">
            <button class="btn primary" id="heroStartMain">🚀 开始今日唯一主块 →</button>
            <button class="btn ghost" id="heroOpenLesson">📖 打开下一节交互课 (${esc(nextLesson.title.slice(0, 12))}…)</button>
            <button class="btn ghost" id="heroStart2Min">⏱️ 先试 2 分钟点火</button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="orbit">
            <div class="orbit-center">W${String(activeWeekObj.number).padStart(2, '0')}<small style="font-size:10px;font-weight:500">今日3步</small></div>
            <div class="orbit-node n1" title="Step 1 复习卡">🧠</div>
            <div class="orbit-node n2" title="Step 2 主线">🎯</div>
            <div class="orbit-node n3" title="Step 3 力扣">💻</div>
          </div>
        </div>
      </div>

      <div class="stat-grid">
        <div class="card stat">
          <div class="stat-label">10周主线计划 (PLAN.md)</div>
          <div class="value">${planDone} / ${planTasks.length}</div>
          <div class="desc">M1 手写GPT (12/20) · M2 简历v1 (1/24)</div>
          <div class="line"><i style="width:${planTasks.length ? Math.round(100 * planDone / planTasks.length) : 0}%"></i></div>
        </div>
        <div class="card stat">
          <div class="stat-label">今日待复习卡 (学习/cards/)</div>
          <div class="value" style="color:${dueCards.length ? '#cb7917' : '#0c936f'}">${dueCards.length} <span style="font-size:15px;font-weight:600;color:#78849b">/ ${(data.cards || []).length} 张</span></div>
          <div class="desc">${dueCards.length ? '每天开头 10 分钟翻完防遗忘' : '🎉 今日复习卡已全部清零！'}</div>
          <div class="line"><i style="width:${(data.cards || []).length ? Math.round(100 * ((data.cards || []).length - dueCards.length) / (data.cards || []).length) : 100}%;background:#0c936f"></i></div>
        </div>
        <div class="card stat">
          <div class="stat-label">每日力扣打卡 (Hot100)</div>
          <div class="value">${lcDone} / ${lcTotal}</div>
          <div class="desc">每天 1 题 · 20 分钟无思路直接看题解</div>
          <div class="line"><i style="width:${Math.round(100 * lcDone / lcTotal)}%"></i></div>
        </div>
        <div class="card stat">
          <div class="stat-label">交互式课程 (学习/)</div>
          <div class="value">${doneLessons} / ${LESSONS_META.length}</div>
          <div class="desc">W01 已完成 5/5 · 下一课 SDPA 注意力</div>
          <div class="line"><i style="width:${Math.round(100 * doneLessons / LESSONS_META.length)}%"></i></div>
        </div>
      </div>

      <div class="two-col">
        <div>
          <div class="section-title">
            <h2>🎯 今日三件套执行清单（一眼看到今天做什么）</h2>
            <span class="pill green">勾选即自动写回文件并 push GitHub</span>
          </div>

          <!-- Step 1: 间隔复习卡 -->
          <div class="step-card ${dueCards.length === 0 ? 'done-step' : 'active-step'}">
            <div class="step-header">
              <span class="step-badge ${dueCards.length === 0 ? 'green' : 'amber'}">STEP 01 · 唤醒大脑（10–15 分钟）</span>
              <span class="hint">剩余今日到期：<strong>${dueCards.length}</strong> 张</span>
            </div>
            ${curDueCard ? `
              <div class="step-title">间隔复习卡自测（先在心里想答案，再点开核对）</div>
              <div class="flashcard-box">
                <div class="flashcard-q">❓ Q: ${esc(curDueCard.q)}</div>
                <div class="hint">来源：<code>${esc(curDueCard.file)}</code> · 当前间隔：${curDueCard.interval} 天</div>
                ${cardAnswerShown ? `
                  <div class="flashcard-a">💡 <strong>A:</strong> ${esc(curDueCard.a)}</div>
                  <label class="form-label" for="homeCardEdit">觉得拗口？直接改成你自己的大白话（选填）：</label>
                  <textarea id="homeCardEdit" class="field" rows="2">${esc(curDueCard.a)}</textarea>
                ` : ''}
              </div>
              <div class="step-actions">
                ${!cardAnswerShown ? `
                  <button class="btn primary small" id="homeRevealCard">👀 显示答案</button>
                ` : `
                  <button class="btn success small" data-grade-card="${curDueCard.index}" data-pass="1">✅ 记住了（推进到下一间隔）</button>
                  <button class="btn danger small" data-grade-card="${curDueCard.index}" data-pass="0">🔄 没记住（明天再测一次）</button>
                `}
                <button class="btn small" data-goto="cards">查看全部 ${(data.cards || []).length} 张卡 →</button>
              </div>
            ` : `
              <div class="step-title" style="color:#0c936f">✓ 今日到期的复习卡已经全部刷完！</div>
              <p class="step-desc">记忆曲线已更新并写回 <code>学习/cards/</code>。你可以直接进入下面的 Step 02 主线任务。</p>
            `}
          </div>

          <!-- Step 2: 今日唯一主线任务 -->
          <div class="step-card active-step" id="mainTaskCard">
            <div class="step-header">
              <span class="step-badge">STEP 02 · 今日唯一核心主块（全天只盯这一件事）</span>
              <a class="mini-link" href="/files/PLAN.md" target="_blank" rel="noopener">查看 PLAN.md ↗</a>
            </div>
            ${mainTask ? `
              <label class="check-row" style="border:0;padding:4px 0 10px">
                <input type="checkbox" data-toggle-task="${esc(mainTask.id)}" ${mainTask.done ? 'checked' : ''} />
                <span class="step-title" style="margin:0">${esc(plain(mainTask.title))}</span>
              </label>
            ` : `<div class="step-title">🎉 本周计划任务已全部完成！</div>`}
            <p class="step-desc">
              💡 <strong>怎么开始：</strong>
              先打开代码文件 <code>concepts/w02_micrograd.py</code> 补完 3 个小函数并运行测试；或者点下方按钮直接在页面内展开下一节交互式 HTML 课程《${esc(nextLesson.title)}》。
            </p>
            <div class="step-actions">
              <button class="btn primary small" id="toggleHomeCourseBtn">${showHomeIframe ? '▲ 收起页内课程' : '📖 页内直接展开交互课：' + esc(nextLesson.title.slice(0, 14))}</button>
              <a class="btn small" href="/files/concepts/w02_micrograd.py" target="_blank" rel="noopener">📂 查看 w02_micrograd.py ↗</a>
              <button class="btn small" id="copyAiPromptBtn">📋 复制 AI 助教带学指令</button>
            </div>
            ${showHomeIframe ? `
              <div class="iframe-wrap">
                <div class="iframe-bar">
                  <span>📘 ${esc(nextLesson.title)}</span>
                  <div style="display:flex;gap:10px;align-items:center">
                    ${nextLesson.taskKey ? `<button class="btn success small" data-toggle-task="${esc(nextLesson.taskKey)}" data-target-done="1">✓ 标记本课已学完</button>` : ''}
                    <a class="mini-link" href="${esc(nextLesson.src)}" target="_blank" rel="noopener">新标签页全屏打开 ↗</a>
                  </div>
                </div>
                <iframe class="course-iframe" src="${esc(nextLesson.src)}" title="${esc(nextLesson.title)}"></iframe>
              </div>
            ` : ''}

            <details style="margin-top:14px;border-top:1px solid var(--line);padding-top:10px">
              <summary class="hint" style="cursor:pointer;font-weight:700">查看本周 (W${String(activeWeekObj.number).padStart(2, '0')}) 其余任务 (${activeWeekObj.tasks.filter((id) => data.tasks[id]?.done).length}/${activeWeekObj.tasks.length})</summary>
              <div style="margin-top:8px">
                ${activeWeekObj.tasks.map((id) => {
                  const t = data.tasks[id];
                  if (!t) return '';
                  return `<label class="check-row ${t.done ? 'done' : ''}"><input type="checkbox" data-toggle-task="${esc(t.id)}" ${t.done ? 'checked' : ''}><span>${esc(plain(t.title))}</span></label>`;
                }).join('')}
              </div>
            </details>
          </div>

          <!-- Step 3: 每日力扣 1 题打卡 -->
          <div class="step-card">
            <div class="step-header">
              <span class="step-badge green">STEP 03 · 每日力扣 Hot100 打卡（每天 1 题 · 20分钟熔断）</span>
              <button class="btn small" data-goto="leetcode">打开完整 51 题打卡墙 →</button>
            </div>
            ${todayLc ? `
              <div class="step-title">今日打卡题：${esc(plain(todayLc.title))}</div>
              <p class="step-desc">
                所属专题：<strong>${esc(todayLc.section)}</strong> ·
                ${todayLc.script_exists
                  ? `本地练习文件已就绪：<code>${esc(todayLc.script_rel)}</code>（终端运行 <code>python3 ${esc(todayLc.script_rel)}</code> 自测）`
                  : `点击下方「⚡ 一键生成刷题脚本」自动在 <code>leetcode/</code> 下创建带 <code>assert</code> 的练习文件`}
              </p>
              <div class="step-actions">
                ${todayLc.slug ? `<button class="btn primary small" data-lc-init="${esc(todayLc.slug)}">⚡ ${todayLc.script_exists ? '查看刷题脚本 (' + esc(todayLc.script_rel) + ')' : '一键生成刷题脚本 (' + esc(todayLc.script_rel) + ')'}</button>` : ''}
                <button class="btn success small" data-toggle-task="${esc(todayLc.id)}" data-target-done="1">✓ 我已跑通，打卡完成本题！</button>
              </div>
            ` : `<div class="step-title">🎉 Hot100 全部 51 题已通关！</div>`}
          </div>

          <!-- Step 4: 今日 1 分钟收尾 -->
          <div class="card panel">
            <div class="section-title">
              <h3>📝 STEP 04 · 收尾留痕（给明天留一句「第一件事」，下次打开直接接上）</h3>
              <span class="pill">${esc(data.daily?.status || '未打卡')}</span>
            </div>
            <label class="form-label" for="dailyTomorrow">🧭 明天坐下第一件事先做什么？（最重要！）</label>
            <input id="dailyTomorrow" class="field" type="text" placeholder="例如：运行 w02_micrograd.py 看 tanh 梯度，然后看 SDPA 第一课" value="${esc(data.daily?.tomorrow || '')}" />
            <div class="grid2">
              <div>
                <label class="form-label" for="dailyNotes">💡 今天学会了什么（一句话即可）</label>
                <textarea id="dailyNotes" class="field" rows="2" placeholder="例如：搞懂了中心差分为什么是 O(h^2)">${esc(data.daily?.notes || '')}</textarea>
              </div>
              <div>
                <label class="form-label" for="dailyBlocker">🚧 卡住的问题（超过2天自动熔断跳过）</label>
                <textarea id="dailyBlocker" class="field" rows="2" placeholder="没有可留空">${esc(data.daily?.blocker || '')}</textarea>
              </div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:14px;flex-wrap:wrap">
              <label class="hint">今日投入分钟数：<input id="dailyMinutes" type="number" min="0" max="1440" value="${esc(data.daily?.minutes || '')}" style="width:70px;padding:5px 8px;border:1px solid var(--line);border-radius:7px" /> 分钟</label>
              <div style="display:flex;gap:8px">
                <button class="btn primary" id="saveDailyBtn">💾 保存今日记录并自动同步 GitHub</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏：番茄钟 + ADHD 走神暂存盒 + 3 条路线快览 -->
        <div>
          <div class="card panel">
            <div class="section-title">
              <h3>⏱️ 专注计时器（防启动困难）</h3>
              <span class="hint" id="timerStatusText">先试 2 分钟也没关系</span>
            </div>
            <div class="timer-presets">
              ${[2, 15, 25, 45].map((m) => `<button data-timer-preset="${m}" class="${local.timer.duration === m ? 'on' : ''}">${m === 2 ? '2m 点火' : m + ' 分钟'}</button>`).join('')}
            </div>
            <div class="timer-clock" id="timerClock">15:00</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
              <button class="btn primary" id="timerToggleBtn">开始专注</button>
              <button class="btn" id="timerResetBtn">重置</button>
            </div>
          </div>

          <div class="card panel">
            <div class="section-title">
              <h3>💡 ADHD 走神想法暂存盒</h3>
              <span class="pill">${local.ideas.length} 条</span>
            </div>
            <p class="hint" style="margin:0 0 8px">学习时突然想到别的事？先丢进这里按回车，别切走当前窗口！</p>
            <div style="display:flex;gap:6px">
              <input id="ideaInput" class="field" type="text" placeholder="输入突然想到的事，按 Enter 暂存…" />
              <button class="btn small primary" id="ideaAddBtn">暂存</button>
            </div>
            <div style="margin-top:10px;max-height:180px;overflow:auto">
              ${local.ideas.map((item, idx) => `
                <div class="check-row" style="padding:7px 0;justify-content:space-between">
                  <span style="font-size:12px">${esc(item.text)}</span>
                  <button class="btn small danger" style="padding:2px 7px;min-height:24px" data-idea-del="${idx}">×</button>
                </div>
              `).join('') || '<div class="hint" style="padding:10px 0">暂无走神念头，继续保持专注！</div>'}
            </div>
          </div>

          <div class="card panel">
            <h3>🗺️ 三条项目路线快捷入口</h3>
            <div class="check-row" style="justify-content:space-between;align-items:center">
              <div><strong>01 · LLM 训练与架构</strong><br><span class="hint">P1 · TinyLLM (BPE → GPT → QLoRA)</span></div>
              <button class="btn small" data-open-proj="llm">进入 →</button>
            </div>
            <div class="check-row" style="justify-content:space-between;align-items:center">
              <div><strong>02 · Agent 工程与 RAG</strong><br><span class="hint">P2 · ReAct + BM25/Dense RRF</span></div>
              <button class="btn small" data-open-proj="agent">进入 →</button>
            </div>
            <div class="check-row" style="justify-content:space-between;align-items:center">
              <div><strong>03 · 具身智能与 VLA</strong><br><span class="hint">P4/P5 · 2D IK → ACT/DP → VLA</span></div>
              <button class="btn small" data-open-proj="robot">进入 →</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // ==================== 页面 2: 课程中心 ====================
  function renderLessonsPage() {
    const filtered = LESSONS_META.filter((l) => lessonFilter === 'all' || l.category === lessonFilter);
    if (!filtered.some((l) => l.id === activeLessonId)) activeLessonId = filtered[0]?.id || 'b01';
    const cur = LESSONS_META.find((l) => l.id === activeLessonId) || LESSONS_META[0];
    const done = isLessonDone(cur);
    const catLabel = { base: '基础 W01', llm: 'LLM W03', agent: 'Agent P2', robot: '具身 P4/P5' };

    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">COURSE LIBRARY</div>
          <h1>交互式课程中心</h1>
          <p>点击任意课程即可在右侧直接内嵌阅读交互式 HTML 课程，学完一键勾选直接写回仓库 <code>计划.md</code>。</p>
        </div>
        <div style="display:flex;gap:8px">
          <a class="btn" href="/files/%E5%AD%A6%E4%B9%A0/index.html" target="_blank" rel="noopener">打开本地学习地图 ↗</a>
          <a class="btn" href="https://ysysysy123.github.io/ai-tutorial-site/index.html" target="_blank" rel="noopener">在线教程站 ↗</a>
        </div>
      </div>

      <div class="lesson-grid">
        <div class="card lesson-browser">
          <div class="filterbar">
            ${[['all', '全部 (16)'], ['base', '基础 (5)'], ['llm', 'LLM (5)'], ['agent', 'Agent (3)'], ['robot', '具身 (3)']].map(([k, label]) =>
              `<button data-lesson-filter="${k}" class="${lessonFilter === k ? 'on' : ''}">${label}</button>`
            ).join('')}
          </div>
          <div class="lesson-list">
            ${filtered.map((l, i) => {
              const d = isLessonDone(l);
              return `
                <button class="lesson-item ${l.id === cur.id ? 'active' : ''}" data-select-lesson="${l.id}">
                  <span class="lesson-index ${d ? 'done' : ''}">${d ? '✓' : String(i + 1).padStart(2, '0')}</span>
                  <span>
                    <strong>${esc(l.title)}</strong>
                    <small>${catLabel[l.category]} · ${l.time} 分钟 · ${esc(l.source)}</small>
                  </span>
                </button>
              `;
            }).join('')}
          </div>
        </div>

        <div class="card lesson-detail">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
            <div class="eyebrow">${esc(cur.source)} · 预计 ${cur.time} 分钟</div>
            <span class="pill ${done ? 'green' : ''}">${done ? '✓ 已学完' : '待学习'}</span>
          </div>
          <h2>${esc(cur.title)}</h2>
          <p>${esc(cur.desc)}</p>
          <div class="quote"><strong>📌 本课最重要的一句话</strong><br>${esc(cur.point)}</div>
          <h4>建议按这三步学习</h4>
          <ul>${cur.steps.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>
          <div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">
            <button class="btn primary" id="toggleLessonIframeBtn">${showLessonIframe ? '▲ 收起页内课程视图' : '📖 在页内展开课程内容'}</button>
            <button class="btn ${done ? '' : 'success'}" id="markLessonDoneBtn">${done ? '撤销已学完标记' : '✓ 标记本课已学完（同步 Git）'}</button>
            <a class="btn" href="${esc(cur.src)}" target="_blank" rel="noopener">新窗口全屏打开 ↗</a>
            ${cur.code ? `<a class="btn" href="${esc(cur.code)}" target="_blank" rel="noopener">查看对应源码 ↗</a>` : ''}
          </div>
          ${showLessonIframe ? `
            <div class="iframe-wrap">
              <div class="iframe-bar">
                <span>正在阅读：${esc(cur.title)}</span>
                <a class="mini-link" href="${esc(cur.src)}" target="_blank" rel="noopener">全屏阅读 ↗</a>
              </div>
              <iframe class="course-iframe" src="${esc(cur.src)}" title="${esc(cur.title)}"></iframe>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  // ==================== 页面 3: 10周计划与实战项目 ====================
  const PROJECT_TRACKS = {
    llm: {
      name: 'LLM · 模型训练与架构 (P1 TinyLLM)',
      desc: '从标量自动微分、Attention、手写 BPE 与 GPT（12/20 M1），到 MiniMind 现代架构（RoPE/GQA/SwiGLU）、SFT 与 Qwen 4-bit QLoRA 结构化微调。',
      links: [['查看 P1 README', '/files/projects/p1-tiny-llm/README.md'], ['查看 MNIST 对照脚本', '/files/projects/p1-tiny-llm/src/w01_mlp_mnist.py'], ['查看 BPE 骨架', '/files/projects/p1-tiny-llm/src/bpe_starter.py']],
      weeks: [0, 1, 2, 3, 4, 5, 6, 7]
    },
    agent: {
      name: 'Agent · 零框架 ReAct 与混合检索 RAG (P2 + P3)',
      desc: '手写 ReAct 工具调用与容错循环，搭建 BM25 + Dense + RRF 混合检索知识库（01/24 产出 M2 简历 v1），投递后按需拓展 P3 Agentic RL (GRPO)。',
      links: [['查看 P2 README', '/files/projects/p2-scratch-agent/README.md'], ['查看 ReAct 源码', '/files/projects/p2-scratch-agent/src/react_loop_starter.py'], ['查看 P3 Agentic-RL 计划', '/files/projects/p3-agentic-rl/README.md']],
      weeks: [8, 9, 10]
    },
    robot: {
      name: '具身智能 · 运动学、模仿学习与 VLA (P4 + P5)',
      desc: '前 10 周每 3 周周六半天轻量体验（2D IK 阻尼伪逆 → MuJoCo Franka → LeRobot Diffusion Policy 推理）；简历 v1 投出后可作为主攻分支深入。',
      links: [['查看 P4 README', '/files/projects/p4-robot-learning/README.md'], ['查看 2D IK 脚本', '/files/projects/p4-robot-learning/src/ik_2d_toy.py'], ['查看 P5 Capstone', '/files/projects/p5-embodied-capstone/README.md']],
      weeks: [3, 6, 8]
    }
  };

  function renderProjectsPage() {
    let bodyHtml = '';
    if (projectTab === 'plan') {
      bodyHtml = data.weeks.map((w) => {
        const doneCount = w.tasks.filter((id) => data.tasks[id]?.done).length;
        const pct = w.tasks.length ? Math.round(100 * doneCount / w.tasks.length) : 0;
        return `
          <div class="card stage">
            <div class="stage-top">
              <h3>W${String(w.number).padStart(2, '0')} · ${esc(w.title)} ${w.number === data.active ? '<span class="pill amber" style="margin-left:8px">当前聚焦周</span>' : ''}</h3>
              <div class="progress-small"><div class="rail"><i style="width:${pct}%"></i></div>${doneCount}/${w.tasks.length}</div>
            </div>
            ${w.tasks.map((id) => {
              const t = data.tasks[id];
              if (!t) return '';
              return `<label class="check-row ${t.done ? 'done' : ''}"><input type="checkbox" data-toggle-task="${esc(t.id)}" ${t.done ? 'checked' : ''}><span>${esc(plain(t.title))}</span></label>`;
            }).join('')}
          </div>
        `;
      }).join('');
    } else if (projectTab === 'papers') {
      const sections = {};
      (data.papers || []).forEach((p) => { (sections[p.section] ||= []).push(p); });
      bodyHtml = Object.entries(sections).map(([sec, items]) => {
        const d = items.filter((x) => x.done).length;
        return `
          <div class="card stage">
            <div class="stage-top">
              <h3>${esc(sec)}</h3>
              <div class="progress-small"><div class="rail"><i style="width:${Math.round(100 * d / items.length)}%"></i></div>${d}/${items.length}</div>
            </div>
            ${items.map((p) => `<label class="check-row ${p.done ? 'done' : ''}"><input type="checkbox" data-toggle-task="${esc(p.id)}" ${p.done ? 'checked' : ''}><span>${esc(plain(p.title))}</span></label>`).join('')}
          </div>
        `;
      }).join('');
    } else {
      const tr = PROJECT_TRACKS[projectTab];
      const relWeeks = data.weeks.filter((w) => tr.weeks.includes(w.number));
      bodyHtml = `
        <div class="card panel">
          <h2>${esc(tr.name)}</h2>
          <p class="muted">${esc(tr.desc)}</p>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            ${tr.links.map(([label, href]) => `<a class="btn small" href="${esc(href)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`).join('')}
          </div>
        </div>
        ${relWeeks.map((w) => `
          <div class="card stage">
            <div class="stage-top"><h3>关联周次：W${String(w.number).padStart(2, '0')} · ${esc(w.title)}</h3></div>
            ${w.tasks.map((id) => {
              const t = data.tasks[id];
              return `<label class="check-row ${t.done ? 'done' : ''}"><input type="checkbox" data-toggle-task="${esc(t.id)}" ${t.done ? 'checked' : ''}><span>${esc(plain(t.title))}</span></label>`;
            }).join('')}
          </div>
        `).join('')}
      `;
    }

    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">ROADMAP & PROJECTS</div>
          <h1>10 周主线计划与实战项目</h1>
          <p>所有勾选项直接对应 <code>PLAN.md</code> 与 <code>papers/READING_LIST.md</code>，点击复选框即实时存盘并推送到 GitHub。</p>
        </div>
        <a class="btn" href="/files/PLAN.md" target="_blank" rel="noopener">查看原始 PLAN.md ↗</a>
      </div>
      <div class="project-tabs">
        <button data-proj-tab="plan" class="${projectTab === 'plan' ? 'on' : ''}">🗓️ W00–W10 全部周计划</button>
        <button data-proj-tab="llm" class="${projectTab === 'llm' ? 'on' : ''}">01 · LLM (P1)</button>
        <button data-proj-tab="agent" class="${projectTab === 'agent' ? 'on' : ''}">02 · Agent & RAG (P2/P3)</button>
        <button data-proj-tab="robot" class="${projectTab === 'robot' ? 'on' : ''}">03 · 具身智能 (P4/P5)</button>
        <button data-proj-tab="papers" class="${projectTab === 'papers' ? 'on' : ''}">📚 30篇论文清单 (${(data.papers || []).filter((x) => x.done).length}/30)</button>
      </div>
      ${bodyHtml}
    `;
  }

  // ==================== 页面 4: 力扣 Hot100 打卡墙 ====================
  function renderLeetcodePage() {
    const list = data.leetcode || [];
    const done = list.filter((x) => x.done).length;
    const todayLc = currentLcTask();
    const groups = {};
    list.forEach((item) => { (groups[item.section] ||= []).push(item); });

    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">LEETCODE HOT 100 TRACKER</div>
          <h1>力扣 Hot100 每日打卡墙（${done} / ${list.length}）</h1>
          <p>无痛刷题规矩：每天 1 题，20 分钟没思路直接看题解，理解后点击「生成脚本」在本地带 <code>assert</code> 跑通即可打勾！</p>
        </div>
        <a class="btn" href="/files/leetcode/hot100_tracker.md" target="_blank" rel="noopener">查看 hot100_tracker.md ↗</a>
      </div>

      ${todayLc ? `
        <div class="step-card active-step">
          <div class="step-header">
            <span class="step-badge green">🎯 今日推荐打卡题（按顺序第 ${done + 1} 题）</span>
            <span class="hint">${esc(todayLc.section)}</span>
          </div>
          <div class="step-title">${esc(plain(todayLc.title))}</div>
          <div class="step-actions">
            ${todayLc.slug ? `<button class="btn primary small" data-lc-init="${esc(todayLc.slug)}">⚡ ${todayLc.script_exists ? '打开已生成脚本 (' + esc(todayLc.script_rel) + ')' : '一键生成本地练习脚本 (' + esc(todayLc.script_rel) + ')'}</button>` : ''}
            <button class="btn success small" data-toggle-task="${esc(todayLc.id)}" data-target-done="1">✓ 我已跑通，打卡完成本题</button>
          </div>
        </div>
      ` : ''}

      ${Object.entries(groups).map(([sec, items]) => {
        const d = items.filter((x) => x.done).length;
        return `
          <div class="card stage">
            <div class="stage-top">
              <h3>${esc(sec)}</h3>
              <div class="progress-small"><div class="rail"><i style="width:${Math.round(100 * d / items.length)}%"></i></div>${d}/${items.length}</div>
            </div>
            ${items.map((item) => `
              <div class="check-row ${item.done ? 'done' : ''}" style="justify-content:space-between;align-items:center">
                <label style="display:flex;gap:10px;align-items:center;cursor:pointer;flex:1">
                  <input type="checkbox" data-toggle-task="${esc(item.id)}" ${item.done ? 'checked' : ''} />
                  <span>${esc(plain(item.title))}</span>
                </label>
                ${item.slug ? `<button class="btn small" data-lc-init="${esc(item.slug)}">${item.script_exists ? '📄 查看 ' + esc(item.slug) + '.py' : '⚡ 生成脚本'}</button>` : ''}
              </div>
            `).join('')}
          </div>
        `;
      }).join('')}
    `;
  }

  // ==================== 页面 5: 间隔复习卡 ====================
  function renderCardsPage() {
    const allCards = data.cards || [];
    const dueCards = allCards.filter((c) => c.is_due);
    const shown = cardFilter === 'due' ? dueCards : allCards;
    if (activeCardIdx >= shown.length) activeCardIdx = 0;
    const cur = shown[activeCardIdx] || null;

    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">SPACED REPETITION CARDS</div>
          <h1>间隔复习卡（今日到期 ${dueCards.length} / 总计 ${allCards.length} 张）</h1>
          <p>按 1 → 3 → 7 → 14 → 30 → 60 天间隔排期。如果某张卡背起来拗口，直接在下方把答案改成你自己的大白话！</p>
        </div>
        <a class="btn" href="/files/%E5%AD%A6%E4%B9%A0/cards/w01-autograd-mnist.md" target="_blank" rel="noopener">打开原始卡片 Markdown ↗</a>
      </div>

      <div class="project-tabs">
        <button data-card-filter="due" class="${cardFilter === 'due' ? 'on' : ''}">⏰ 今日到期 (${dueCards.length})</button>
        <button data-card-filter="all" class="${cardFilter === 'all' ? 'on' : ''}">🗂️ 全部复习卡 (${allCards.length})</button>
      </div>

      ${cur ? `
        <div class="card panel">
          <div class="step-header">
            <span class="step-badge">卡片 ${activeCardIdx + 1} / ${shown.length}</span>
            <span class="hint">文件：<code>${esc(cur.file)}</code> · 下次到期：${esc(cur.due)} · 当前间隔：${cur.interval} 天</span>
          </div>
          <div class="flashcard-box" style="margin:14px 0">
            <div class="flashcard-q" style="font-size:17px">❓ Q: ${esc(cur.q)}</div>
            ${cardAnswerShown ? `
              <div class="flashcard-a" style="font-size:14px">${esc(cur.a)}</div>
              <label class="form-label" for="deckCardEdit">✏️ 用你自己的话改写答案（保存评分时自动写入 Markdown）：</label>
              <textarea id="deckCardEdit" class="field" rows="3">${esc(cur.a)}</textarea>
            ` : `<p class="hint" style="margin:12px 0 0">先合上资料在脑海里过一遍答案，再点击下方「显示答案」。</p>`}
          </div>
          <div class="step-actions">
            ${!cardAnswerShown ? `
              <button class="btn primary" id="deckRevealBtn">👀 显示答案</button>
            ` : `
              <button class="btn success" data-grade-deck="${cur.index}" data-pass="1">✅ 记住了（推进间隔）</button>
              <button class="btn danger" data-grade-deck="${cur.index}" data-pass="0">🔄 没记住（重置为明天复习）</button>
            `}
            <button class="btn" id="prevCardBtn" ${activeCardIdx <= 0 ? 'disabled' : ''}>← 上一张</button>
            <button class="btn" id="nextCardBtn" ${activeCardIdx >= shown.length - 1 ? 'disabled' : ''}>下一张 →</button>
          </div>
        </div>
      ` : `<div class="card panel empty">🎉 当前筛选下没有待复习卡片！可切换到「全部复习卡」随时抽查。</div>`}
    `;
  }

  // ==================== 页面 6: 原理交互实验 ====================
  function renderDemosPage() {
    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">INTERACTIVE LAB</div>
          <h1>原理交互实验沙盒</h1>
          <p>先动手拖动参数观察直觉变化，再回到真实项目源码。</p>
        </div>
      </div>
      <div class="demo-tabs">
        <button data-demo-tab="attention" class="${activeDemo === 'attention' ? 'on' : ''}">01 · Attention 权重与温度缩放</button>
        <button data-demo-tab="react" class="${activeDemo === 'react' ? 'on' : ''}">02 · ReAct Agent 循环状态机</button>
        <button data-demo-tab="ik" class="${activeDemo === 'ik' ? 'on' : ''}">03 · 机器人 2D 阻尼伪逆 IK</button>
      </div>

      <div style="display:${activeDemo === 'attention' ? 'block' : 'none'}">
        <div class="card demo-card">
          <h2>缩放与 Softmax 如何改变注意力分布？</h2>
          <p class="muted">调节两个 Key 的匹配得分与温度 τ（对应 √dₖ 缩放），观察 Softmax 权重何时退化为极端 one-hot（梯度饱和）。</p>
          <div class="demo-layout">
            <div>
              <label class="sliderr"><span class="range-title"><span>证据 A 得分</span><output id="scoreAVal">2.0</output></span><input type="range" id="scoreA" min="-3" max="5" step="0.1" value="2"></label>
              <label class="sliderr"><span class="range-title"><span>证据 B 得分</span><output id="scoreBVal">0.0</output></span><input type="range" id="scoreB" min="-3" max="5" step="0.1" value="0"></label>
              <label class="sliderr"><span class="range-title"><span>缩放温度 τ (对应 √dₖ)</span><output id="tempVal">1.0</output></span><input type="range" id="temp" min="0.2" max="3" step="0.1" value="1"></label>
              <div class="formula">pᵢ = exp(sᵢ / τ) / ∑ⱼ exp(sⱼ / τ)<br>当 τ 过小（或不除以 √dₖ 导致内积方差过大）时，最大值占满 100%，其余位置梯度趋近 0。</div>
            </div>
            <div>
              <div class="bars">
                <div><label>证据 A 权重</label><span class="trackbar"><i id="barA" style="width:88%"></i></span><output id="probA">88.1%</output></div>
                <div><label>证据 B 权重</label><span class="trackbar"><i id="barB" style="width:12%"></i></span><output id="probB">11.9%</output></div>
              </div>
              <div class="code">scores = [a, b]\nweights = softmax(scores / tau)\noutput = weights @ values</div>
              <p class="hint" style="margin-top:12px">对应课程：<a class="mini-link" href="#" id="demoToSdpa">打开《缩放点积自注意力 SDPA》HTML 课 →</a></p>
            </div>
          </div>
        </div>
      </div>

      <div style="display:${activeDemo === 'react' ? 'block' : 'none'}">
        <div class="card demo-card">
          <h2>Agent 为什么需要“思考—行动—观察”闭环？</h2>
          <p class="muted">点击“下一步”观察 ` + '<code>react_loop_starter.py</code>' + ` 中的状态流转与工具反馈。</p>
          <div class="agent-flow" id="reactNodes">
            <div class="node ${reactPos === 0 ? 'active' : ''}">① Thought 思考</div>
            <div class="node ${reactPos === 1 ? 'active' : ''}">② Action 调工具</div>
            <div class="node ${reactPos === 2 ? 'active' : ''}">③ Observation 观察</div>
            <div class="node ${reactPos === 3 ? 'active' : ''}">④ 最终回答 / 重规划</div>
          </div>
          <div class="formula" id="reactExplain" style="margin:18px 0"></div>
          <div style="display:flex;gap:8px">
            <button id="reactNext" class="btn primary">下一步 →</button>
            <button id="reactReset" class="btn">重置</button>
            <a class="btn" href="/files/projects/p2-scratch-agent/src/react_loop_starter.py" target="_blank" rel="noopener">查看 react_loop_starter.py ↗</a>
          </div>
        </div>
      </div>

      <div style="display:${activeDemo === 'ik' ? 'block' : 'none'}">
        <div class="card demo-card">
          <h2>阻尼最小二乘 IK：让双连杆机械臂平滑靠近目标</h2>
          <p class="muted">对应 P4 <code>ik_2d_toy.py</code>。点击“执行一步 DLS”按雅可比阻尼伪逆更新关节角。</p>
          <div class="demo-layout">
            <div>
              <canvas id="ikCanvas" class="robot-canvas" width="480" height="320"></canvas>
              <div class="hint" id="ikStatus" style="margin-top:8px">等待执行</div>
            </div>
            <div>
              <label class="sliderr"><span class="range-title"><span>目标 X</span><output id="targetXText">1.20</output></span><input type="range" id="targetX" min="-1.8" max="1.8" value="1.2" step="0.05"></label>
              <label class="sliderr"><span class="range-title"><span>目标 Y</span><output id="targetYText">0.80</output></span><input type="range" id="targetY" min="-1.8" max="1.8" value="0.8" step="0.05"></label>
              <label class="sliderr"><span class="range-title"><span>阻尼系数 λ</span><output id="lambdaText">0.20</output></span><input type="range" id="lambda" min="0.01" max="1" value="0.2" step="0.01"></label>
              <div class="formula">Δq = Jᵀ (JJᵀ + λ²I)⁻¹ e<br>阻尼项 λ²I 防止机械臂完全伸直（奇异位形）时矩阵不可逆导致关节速度爆炸。</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
                <button class="btn primary" id="ikStep">执行一步 DLS</button>
                <button class="btn" id="ikTen">连续迭代 10 步</button>
                <button class="btn" id="ikReset">重置姿态</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // ==================== 页面 7: 学习记录与同步 ====================
  function renderJournalPage() {
    const g = data.git || {};
    return `
      <div class="page-head">
        <div>
          <div class="eyebrow">HISTORY & GIT SYNC</div>
          <h1>学习日志与 GitHub 自动同步</h1>
          <p>你在工作台里的所有勾选和打卡都会实时写入 <code>daily/</code>、<code>PLAN.md</code>、<code>leetcode/</code> 并自动同步至远程 GitHub。</p>
        </div>
        <button class="btn primary" id="journalSyncBtn">🔄 立即触发 Git Commit & Push</button>
      </div>

      <div class="card panel">
        <h3>🟢 远程同步状态</h3>
        <p class="muted" style="margin:0 0 8px">远程仓库：<code>https://github.com/ysysysy123/lab.git</code> (分支 <code>main</code>)</p>
        <div class="formula">
          <strong>当前 HEAD：</strong>${esc(g.head || '未知')}<br>
          <strong>最近自动同步：</strong>${esc(g.last_msg || '就绪')} ${g.last_time ? `(${esc(g.last_time)})` : ''}
        </div>
      </div>

      <div class="card panel">
        <h3>📅 最近每日打卡日志（daily/*.md）</h3>
        ${(data.history || []).map((h) => `
          <div class="note-card">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong>${esc(h.date)} · <span class="pill ${h.status === '已打卡' ? 'green' : ''}">${esc(h.status)}</span></strong>
              <a class="mini-link" href="${esc(h.url)}" target="_blank" rel="noopener">查看原始 Markdown ↗</a>
            </div>
            ${h.tomorrow ? `<p style="margin:6px 0 2px">🧭 <strong>留给次日的第一件事：</strong>${esc(h.tomorrow)}</p>` : ''}
            ${h.notes ? `<p style="margin:4px 0">💡 <strong>收获：</strong>${esc(h.notes)}</p>` : ''}
            ${h.blocker ? `<p style="margin:4px 0;color:#b34745">🚧 <strong>卡点：</strong>${esc(h.blocker)}</p>` : ''}
          </div>
        `).join('') || '<div class="empty">暂无打卡日志</div>'}
      </div>
    `;
  }

  // ==================== 交互绑定与渲染调度 ====================
  function bindInteractiveDemos() {
    if (page !== 'demos') return;
    if (activeDemo === 'attention') {
      const updateAttn = () => {
        const a = +document.getElementById('scoreA').value;
        const b = +document.getElementById('scoreB').value;
        const t = +document.getElementById('temp').value;
        const m = Math.max(a / t, b / t);
        const ea = Math.exp(a / t - m), eb = Math.exp(b / t - m);
        const p = ea / (ea + eb);
        document.getElementById('scoreAVal').textContent = a.toFixed(1);
        document.getElementById('scoreBVal').textContent = b.toFixed(1);
        document.getElementById('tempVal').textContent = t.toFixed(1);
        document.getElementById('barA').style.width = (p * 100) + '%';
        document.getElementById('barB').style.width = ((1 - p) * 100) + '%';
        document.getElementById('probA').textContent = (p * 100).toFixed(1) + '%';
        document.getElementById('probB').textContent = ((1 - p) * 100).toFixed(1) + '%';
      };
      ['scoreA', 'scoreB', 'temp'].forEach((id) => document.getElementById(id)?.addEventListener('input', updateAttn));
      updateAttn();
      document.getElementById('demoToSdpa')?.addEventListener('click', (e) => {
        e.preventDefault();
        activeLessonId = 't01';
        page = 'lessons';
        render();
      });
    } else if (activeDemo === 'react') {
      const texts = [
        '① Thought：用户问“谁提出了 ReAct？” Agent 先判断是否需要检索可靠资料，而不是直接凭空瞎猜。',
        '② Action：Agent 生成结构化工具调用 JSON，运行时校验工具名、参数格式与 max_steps 预算。',
        '③ Observation：执行本地检索或 Python 沙盒，将返回结果作为 Observation 追加进消息历史。',
        '④ Answer：Agent 根据真实证据输出最终答案；若工具报错则根据错误信息修正参数重试。'
      ];
      document.getElementById('reactExplain').textContent = texts[reactPos];
      document.getElementById('reactNext').onclick = () => { reactPos = (reactPos + 1) % 4; render(); };
      document.getElementById('reactReset').onclick = () => { reactPos = 0; render(); };
    } else if (activeDemo === 'ik') {
      const cv = document.getElementById('ikCanvas');
      if (!cv) return;
      const ctx = cv.getContext('2d');
      const W = cv.width, H = cv.height, scale = 72, center = [W / 2, H * 0.82];
      const pos = (a1, a2) => [Math.cos(a1) + Math.cos(a1 + a2), Math.sin(a1) + Math.sin(a1 + a2)];
      const drawIK = () => {
        const tx = +document.getElementById('targetX').value;
        const ty = +document.getElementById('targetY').value;
        const lam = +document.getElementById('lambda').value;
        document.getElementById('targetXText').textContent = tx.toFixed(2);
        document.getElementById('targetYText').textContent = ty.toFixed(2);
        document.getElementById('lambdaText').textContent = lam.toFixed(2);
        const world = (x, y) => [center[0] + x * scale, center[1] - y * scale];
        const p1 = [Math.cos(q1), Math.sin(q1)], p2 = pos(q1, q2);
        const u0 = world(0, 0), u1 = world(...p1), u2 = world(...p2), ut = world(tx, ty);
        ctx.clearRect(0, 0, W, H);
        ctx.strokeStyle = '#e8ebf1'; ctx.lineWidth = 1;
        for (let x = 0; x < W; x += scale / 2) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
        for (let y = 0; y < H; y += scale / 2) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
        ctx.strokeStyle = '#a5acd4'; ctx.setLineDash([5, 5]);
        ctx.beginPath(); ctx.moveTo(u2[0], u2[1]); ctx.lineTo(ut[0], ut[1]); ctx.stroke();
        ctx.setLineDash([]); ctx.lineWidth = 13; ctx.lineCap = 'round';
        ctx.strokeStyle = '#827bed'; ctx.beginPath(); ctx.moveTo(...u0); ctx.lineTo(...u1); ctx.stroke();
        ctx.strokeStyle = '#3a95bd'; ctx.beginPath(); ctx.moveTo(...u1); ctx.lineTo(...u2); ctx.stroke();
        [[u0, '#25314f', 10], [u1, '#fff', 8], [u2, '#5654dc', 9]].forEach(([p, c, r]) => {
          ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, Math.PI * 2); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = '#5363b1'; ctx.lineWidth = 2; ctx.stroke();
        });
        ctx.beginPath(); ctx.arc(ut[0], ut[1], 9, 0, Math.PI * 2); ctx.strokeStyle = '#0c9675'; ctx.lineWidth = 3; ctx.stroke();
        const err = Math.hypot(p2[0] - tx, p2[1] - ty);
        document.getElementById('ikStatus').textContent = `末端 (${p2[0].toFixed(2)}, ${p2[1].toFixed(2)}) · 目标 (${tx.toFixed(2)}, ${ty.toFixed(2)}) · 距离误差 ${err.toFixed(4)}`;
      };
      const dlsStep = () => {
        const [px, py] = pos(q1, q2);
        const ex = +document.getElementById('targetX').value - px;
        const ey = +document.getElementById('targetY').value - py;
        const lam = +document.getElementById('lambda').value;
        const j11 = -Math.sin(q1) - Math.sin(q1 + q2), j12 = -Math.sin(q1 + q2);
        const j21 = Math.cos(q1) + Math.cos(q1 + q2), j22 = Math.cos(q1 + q2);
        const a = j11 * j11 + j12 * j12 + lam * lam, b = j11 * j21 + j12 * j22, c = j21 * j21 + j22 * j22 + lam * lam;
        const det = a * c - b * b;
        if (det < 1e-12) return;
        const vx = (c * ex - b * ey) / det, vy = (-b * ex + a * ey) / det;
        const clamp = (x) => Math.max(-0.28, Math.min(0.28, x));
        q1 += clamp(j11 * vx + j21 * vy);
        q2 += clamp(j12 * vx + j22 * vy);
      };
      ['targetX', 'targetY', 'lambda'].forEach((id) => document.getElementById(id)?.addEventListener('input', drawIK));
      document.getElementById('ikStep').onclick = () => { dlsStep(); drawIK(); };
      document.getElementById('ikTen').onclick = () => { for (let i = 0; i < 10; i++) dlsStep(); drawIK(); };
      document.getElementById('ikReset').onclick = () => { q1 = 0.35; q2 = 0.65; drawIK(); };
      drawIK();
    }
  }

  function render() {
    if (!data) return;
    document.querySelectorAll('.nav button[data-page]').forEach((b) => b.classList.toggle('active', b.dataset.page === page));
    if (page === 'home') root.innerHTML = renderHome();
    else if (page === 'lessons') root.innerHTML = renderLessonsPage();
    else if (page === 'projects') root.innerHTML = renderProjectsPage();
    else if (page === 'leetcode') root.innerHTML = renderLeetcodePage();
    else if (page === 'cards') root.innerHTML = renderCardsPage();
    else if (page === 'demos') root.innerHTML = renderDemosPage();
    else if (page === 'journal') root.innerHTML = renderJournalPage();
    updateTimerUI();
    bindInteractiveDemos();
  }

  // ==================== 番茄钟逻辑 ====================
  function remainingMs() {
    return local.timer.endAt ? Math.max(0, local.timer.endAt - Date.now()) : local.timer.remaining;
  }
  function updateTimerUI() {
    const t = local.timer;
    if (t.status === 'running' && remainingMs() <= 0) {
      t.status = 'finished'; t.endAt = null; t.remaining = 0; saveLocal();
      toast('⏰ 专注计时结束！休息一下或打勾今日进度吧');
    }
    const sec = Math.ceil(remainingMs() / 1000);
    const clockEl = document.getElementById('timerClock');
    if (clockEl) clockEl.textContent = `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
    const btn = document.getElementById('timerToggleBtn');
    if (btn) btn.textContent = t.status === 'running' ? '⏸ 暂停专注' : t.status === 'paused' ? '▶ 继续专注' : '▶ 开始专注';
    const st = document.getElementById('timerStatusText');
    if (st) st.textContent = t.status === 'running' ? '专注中…别切窗口' : t.status === 'finished' ? '🎉 本轮完成！' : '先试 2 分钟也没关系';
  }
  function startTimer(mins) {
    if (mins) local.timer.duration = mins;
    local.timer.remaining = local.timer.duration * 60000;
    local.timer.endAt = Date.now() + local.timer.remaining;
    local.timer.status = 'running';
    saveLocal();
    updateTimerUI();
  }

  // ==================== 全局事件委托 ====================
  document.addEventListener('click', async (e) => {
    const navBtn = e.target.closest('[data-page]');
    if (navBtn) {
      page = navBtn.dataset.page;
      document.getElementById('sidebar').classList.remove('open');
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    const gotoBtn = e.target.closest('[data-goto]');
    if (gotoBtn) {
      page = gotoBtn.dataset.goto;
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    const openProj = e.target.closest('[data-open-proj]');
    if (openProj) {
      projectTab = openProj.dataset.openProj;
      page = 'projects';
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    if (e.target.id === 'menuToggle') {
      document.getElementById('sidebar').classList.toggle('open');
      return;
    }

    if (e.target.id === 'syncNowBtn' || e.target.id === 'journalSyncBtn') {
      try {
        toast('🔄 正在同步到远程 GitHub…');
        await apiPost('/api/sync', { reason: 'chore(workbench): manual sync to GitHub' });
        toast('🟢 已成功同步至 GitHub (origin/main)！');
      } catch (err) { toast('❌ 同步失败: ' + err.message); }
      return;
    }

    if (e.target.id === 'heroStartMain') {
      document.getElementById('mainTaskCard')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    if (e.target.id === 'heroOpenLesson') {
      showHomeIframe = true;
      render();
      document.getElementById('mainTaskCard')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (e.target.id === 'heroStart2Min') {
      startTimer(2);
      toast('⏱️ 2 分钟点火计时已开启！只看眼前这一步');
      return;
    }
    if (e.target.id === 'toggleHomeCourseBtn') {
      showHomeIframe = !showHomeIframe;
      render();
      return;
    }
    if (e.target.id === 'copyAiPromptBtn') {
      const t = currentPlanTask();
      const text = `请结合 lab/PLAN.md 带我推进今日唯一主线任务：${t ? plain(t.title) : '当前任务'}。先给我 3 句话直觉，再带我跑通代码并做三级验收。`;
      try {
        await navigator.clipboard.writeText(text);
        toast('📋 已复制 AI 助教指令，直接粘贴到对话框即可！');
      } catch { toast('复制失败，请手动复制任务标题'); }
      return;
    }

    // 复习卡显隐与打分
    if (e.target.id === 'homeRevealCard' || e.target.id === 'deckRevealBtn') {
      cardAnswerShown = true;
      render();
      return;
    }
    const gradeCardBtn = e.target.closest('[data-grade-card]');
    if (gradeCardBtn) {
      const idx = Number(gradeCardBtn.dataset.gradeCard);
      const passed = gradeCardBtn.dataset.pass === '1';
      const newA = document.getElementById('homeCardEdit')?.value || '';
      cardAnswerShown = false;
      await apiPost('/api/review', { index: idx, passed, new_a: newA });
      toast(passed ? '✅ 已记住！到期日已推进并同步 GitHub' : '🔄 已排期明天重新复习');
      return;
    }
    const gradeDeckBtn = e.target.closest('[data-grade-deck]');
    if (gradeDeckBtn) {
      const idx = Number(gradeDeckBtn.dataset.gradeDeck);
      const passed = gradeDeckBtn.dataset.pass === '1';
      const newA = document.getElementById('deckCardEdit')?.value || '';
      cardAnswerShown = false;
      await apiPost('/api/review', { index: idx, passed, new_a: newA });
      toast(passed ? '✅ 已记住！到期日已推进并同步 GitHub' : '🔄 已重置为明天复习');
      return;
    }
    if (e.target.id === 'prevCardBtn') { activeCardIdx = Math.max(0, activeCardIdx - 1); cardAnswerShown = false; render(); return; }
    if (e.target.id === 'nextCardBtn') { activeCardIdx += 1; cardAnswerShown = false; render(); return; }

    // 一键切换完成状态按钮 (如“打卡完成本题”)
    const toggleBtn = e.target.closest('button[data-toggle-task]');
    if (toggleBtn) {
      const id = toggleBtn.dataset.toggleTask;
      const done = toggleBtn.dataset.targetDone === '1';
      await apiPost('/api/toggle', { id, done });
      toast('🎉 已打卡完成并自动同步至 GitHub！');
      return;
    }

    // 一键初始化/查看力扣脚本
    const lcInitBtn = e.target.closest('[data-lc-init]');
    if (lcInitBtn) {
      const slug = lcInitBtn.dataset.lcInit;
      await apiPost('/api/lc-init', { slug });
      window.open(`/files/leetcode/${encodeURIComponent(slug)}.py`, '_blank', 'noopener');
      toast(`⚡ 已就绪 leetcode/${slug}.py（已同步 GitHub）`);
      return;
    }

    // 保存每日收尾日志
    if (e.target.id === 'saveDailyBtn') {
      const tomorrow = document.getElementById('dailyTomorrow')?.value || '';
      const notes = document.getElementById('dailyNotes')?.value || '';
      const blocker = document.getElementById('dailyBlocker')?.value || '';
      const minutes = document.getElementById('dailyMinutes')?.value || '';
      const mainT = currentPlanTask();
      const selected = mainT ? [mainT.id] : [];
      await apiPost('/api/save', {
        date: data.date,
        selected,
        changes: {},
        tomorrow,
        notes,
        blocker,
        minutes,
        checkin: true
      });
      toast('💾 今日记录已写入 daily/ 并自动同步 GitHub！');
      return;
    }

    // 番茄钟按钮
    const presetBtn = e.target.closest('[data-timer-preset]');
    if (presetBtn) {
      const m = Number(presetBtn.dataset.timerPreset);
      local.timer = { duration: m, remaining: m * 60000, endAt: null, status: 'idle' };
      saveLocal();
      render();
      return;
    }
    if (e.target.id === 'timerToggleBtn') {
      const t = local.timer;
      if (t.status === 'running') { t.remaining = remainingMs(); t.endAt = null; t.status = 'paused'; }
      else if (t.status === 'paused') { t.endAt = Date.now() + t.remaining; t.status = 'running'; }
      else { startTimer(t.duration); return; }
      saveLocal();
      updateTimerUI();
      return;
    }
    if (e.target.id === 'timerResetBtn') {
      local.timer = { duration: local.timer.duration, remaining: local.timer.duration * 60000, endAt: null, status: 'idle' };
      saveLocal();
      updateTimerUI();
      return;
    }

    // ADHD 想法暂存盒
    if (e.target.id === 'ideaAddBtn') {
      const inp = document.getElementById('ideaInput');
      if (inp && inp.value.trim()) {
        local.ideas.unshift({ text: inp.value.trim(), at: new Date().toLocaleTimeString('zh-CN') });
        saveLocal();
        render();
        toast('💡 已暂存到想法盒，继续眼前的事吧');
      }
      return;
    }
    const ideaDel = e.target.closest('[data-idea-del]');
    if (ideaDel) {
      local.ideas.splice(Number(ideaDel.dataset.ideaDel), 1);
      saveLocal();
      render();
      return;
    }

    // 课程中心筛选与切换
    const lf = e.target.closest('[data-lesson-filter]');
    if (lf) { lessonFilter = lf.dataset.lessonFilter; render(); return; }
    const sl = e.target.closest('[data-select-lesson]');
    if (sl) { activeLessonId = sl.dataset.selectLesson; render(); return; }
    if (e.target.id === 'toggleLessonIframeBtn') { showLessonIframe = !showLessonIframe; render(); return; }
    if (e.target.id === 'markLessonDoneBtn') {
      const cur = LESSONS_META.find((l) => l.id === activeLessonId);
      if (!cur) return;
      const nextDone = !isLessonDone(cur);
      if (cur.taskKey && data.tasks[cur.taskKey]) {
        await apiPost('/api/toggle', { id: cur.taskKey, done: nextDone });
      } else {
        local.extraLessons[cur.id] = nextDone;
        saveLocal();
        render();
      }
      toast(nextDone ? '✓ 已标记课程学完并同步 GitHub' : '已撤销课程完成标记');
      return;
    }

    // 项目页/复习卡/实验页 Tab 切换
    const pt = e.target.closest('[data-proj-tab]');
    if (pt) { projectTab = pt.dataset.projTab; render(); return; }
    const cf = e.target.closest('[data-card-filter]');
    if (cf) { cardFilter = cf.dataset.cardFilter; activeCardIdx = 0; cardAnswerShown = false; render(); return; }
    const dt = e.target.closest('[data-demo-tab]');
    if (dt) { activeDemo = dt.dataset.demoTab; render(); return; }
  });

  // 复选框即点即存
  document.addEventListener('change', async (e) => {
    const cb = e.target.closest('input[type="checkbox"][data-toggle-task]');
    if (cb) {
      const id = cb.dataset.toggleTask;
      const done = cb.checked;
      try {
        await apiPost('/api/toggle', { id, done });
        toast(done ? '✓ 已完成并自动同步 GitHub' : '已取消勾选并同步');
      } catch (err) {
        cb.checked = !done;
        toast('❌ 保存失败: ' + err.message);
      }
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.target.id === 'ideaInput' && e.key === 'Enter' && !e.isComposing) {
      e.preventDefault();
      document.getElementById('ideaAddBtn')?.click();
    }
  });

  setInterval(updateTimerUI, 1000);

  fetch('/api/state')
    .then((r) => r.json())
    .then((res) => {
      data = res;
      updateChrome();
      render();
    })
    .catch((err) => {
      root.innerHTML = `<div class="card panel empty">读取本地服务失败：${esc(err.message)}</div>`;
    });
})();
