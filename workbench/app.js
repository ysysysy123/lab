let data, draft, view = 'today', dirty = false, saving = false;
const app = document.querySelector('#app');
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const plain = value => String(value ?? '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*|`/g, '');
const title = value => esc(plain(value));
const taskDone = task => Object.hasOwn(draft.changes, task.id) ? draft.changes[task.id] : task.done;
const activeWeek = () => data.weeks.find(w => w.number === data.active);
const lessons = () => data.topics.flatMap(t => t.tasks.map(id => data.tasks[id]));
const nextLesson = () => lessons().find(t => !taskDone(t));
const taskFor = item => data.tasks[item.id] || {...item, kind: '历史任务'};
function toast(message, error = false) {
  const el = document.querySelector('#toast');
  el.textContent = message; el.className = 'visible' + (error ? ' error' : '');
  clearTimeout(toast.timer); toast.timer = setTimeout(() => el.className = '', 4500);
}
function accept(next) {
  data = next;
  draft = {date: next.date, selected: next.daily.selected.map(t => t.id), changes: {},
    notes: next.daily.notes, blocker: next.daily.blocker, tomorrow: next.daily.tomorrow, minutes: next.daily.minutes};
  dirty = false;
  document.querySelector('#course-map').href = next.map;
}
async function load() {
  const response = await fetch('/api/state');
  if (!response.ok) throw new Error('读取计划失败，请重新打开工作台。');
  accept(await response.json()); render();
}
function pageHeader(label, subtitle) {
  const day = new Date(data.date + 'T12:00:00');
  const monthDay = day.toLocaleDateString('zh-CN', {month:'long', day:'numeric'});
  const weekday = day.toLocaleDateString('zh-CN', {weekday:'long'});
  return `<div class="topline"><span>MY LEARNING SPACE / ${view === 'today' ? 'TODAY' : view === 'roadmap' ? 'ROADMAP' : 'JOURNAL'}</span><span>LLM → AGENT → 具身智能</span></div>
    <header class="page-title"><div><h1>${label}</h1><p class="subtitle">${subtitle}</p></div><div class="date-block"><strong>${monthDay}</strong>${weekday} · ${data.date.slice(0,4)}</div></header>`;
}
function taskRow(item, index) {
  const task = taskFor(item), done = taskDone(task);
  return `<div class="task ${done ? 'completed' : ''}"><input type="checkbox" id="task-${index}" data-check="${esc(task.id)}" ${done ? 'checked' : ''} ${!data.tasks[task.id] ? 'disabled' : ''}>
    <div class="task-content"><label class="task-title" for="task-${index}">${title(task.title)}</label>
    <div class="task-meta"><span class="badge">${esc(task.kind)}</span>${task.url ? `<a href="${esc(task.url)}" target="_blank" rel="noopener">${task.kind === '课程' ? '打开课程' : '查看计划'} ↗</a>` : '<span>课程页待生成 · 可用续学指令开始</span>'}</div></div>
    <button class="remove" data-remove="${esc(task.id)}" aria-label="从今日计划移除" title="从今日计划移除">×</button></div>`;
}
function today() {
  const week = activeWeek(), next = nextLesson();
  const selected = draft.selected.map(id => data.tasks[id] || data.daily.selected.find(t => t.id === id)).filter(Boolean);
  const done = selected.filter(t => taskDone(t)).length;
  const candidates = [...(next ? [next] : []), ...week.tasks.map(id => data.tasks[id])]
    .filter((t,i,all) => !taskDone(t) && !draft.selected.includes(t.id) && all.findIndex(a => a.id === t.id) === i);
  const weekDone = week.tasks.filter(id => taskDone(data.tasks[id])).length;
  return pageHeader('今天，从这里开始。', '先完成一件具体的事，再留下一句今天的收获。') + `<div class="layout"><div>
    <section class="hero"><div class="eyebrow">YOUR NEXT STEP · 接着学什么</div><span class="badge outline">${next ? '第 ' + next.number + ' 课 · 按计划继续' : '当前周待办'}</span>
    <h2>${next ? title(next.title) : '推进本周的项目与论文'}</h2><p>${next ? esc(plain(next.mastery || '按课程逐步理解，完成后在下方勾选并保存。')) : '从下方待办池选择今天要推进的内容。'}</p><div class="actions">
    ${next?.url ? `<a class="button light" href="${esc(next.url)}" target="_blank" rel="noopener">进入课程 ↗</a>` : ''}
    <button class="button ${next?.url ? 'ghost-light' : 'light'}" data-copy>复制续学指令</button><a class="button ghost-light" href="#checkin">去打卡 ↓</a></div></section>
    <section class="panel"><div class="panel-heading"><h2>今日计划</h2><div class="count">${done}<small> / ${selected.length} 已完成</small></div></div>
    <p class="caption">默认先排一课。按今天的精力，从待办池再加 1–2 项即可。</p>
    ${selected.length ? selected.map(taskRow).join('') : '<p class="empty">今天还没有安排任务，从待办池加入一项吧。</p>'}
    <details class="pool" ${selected.length ? '' : 'open'}><summary>＋ 从本周待办池加入 ${candidates.length ? `（${candidates.length} 项）` : ''}</summary>
    ${candidates.length ? candidates.map(t => `<div class="pool-item"><div><span>${esc(t.kind)}</span><p>${title(t.title)}</p></div><button class="button small" data-add="${esc(t.id)}">加入今天</button></div>`).join('') : '<p class="empty">当前待办已加入，完成后会接续下一项。</p>'}</details></section>
    <section class="panel" id="checkin"><div class="form-top"><h2>今日打卡 <span class="badge ${data.daily.status === '已打卡' ? '' : 'orange'}">${esc(data.daily.status)}</span></h2><label class="minutes">今天投入 <input type="number" min="0" max="1440" name="minutes" value="${esc(draft.minutes)}" placeholder="45" aria-label="今日学习分钟数"> 分钟</label></div>
    <label class="field">今天学会了什么？<span>一句话也可以</span><textarea name="notes" placeholder="例如：弄清了 backward 中为什么需要 +=，并验证了节点复用的梯度。">${esc(draft.notes)}</textarea></label>
    <label class="field">卡在哪里？<span>可留空</span><textarea name="blocker" rows="2" placeholder="写下具体卡点，下次可以直接带着问题继续。">${esc(draft.blocker)}</textarea></label>
    <label class="field">下次从哪里继续？<span>给明天的自己留个入口</span><textarea name="tomorrow" rows="2" placeholder="例如：从第 2 课 Softmax 与交叉熵开始，先推通 p − y。">${esc(draft.tomorrow)}</textarea></label>
    <div class="save-row"><p>保存到 daily/${data.date}.md<br>勾选完成会同步课程计划 / 周计划。</p><div class="actions"><button class="button" data-save="draft" ${saving ? 'disabled' : ''}>保存进度</button><button class="button primary" data-save="checkin" ${saving ? 'disabled' : ''}>${saving ? '正在保存…' : data.daily.status === '已打卡' ? '更新今日打卡 ✓' : '保存并打卡 ✓'}</button></div></div></section>
    <p class="footer-note">打卡：选任务 → 学习 → 勾选完成 → 写一句收获 → 保存并打卡。未完成的计划项会继续保留。<br>日期按 ${esc(data.timezone)} 计算。工作台不自动把学习记录推断为已完成。</p>
    </div><aside class="right-column">
    <section class="panel side-panel"><div class="side-label">THIS WEEK · 当前阶段</div><div class="week-title">W${String(week.number).padStart(2,'0')} · ${esc(week.title)}</div><div class="progress-track"><span style="width:${week.tasks.length ? weekDone/week.tasks.length*100 : 0}%"></span></div><div class="stat-row"><span>本周已完成 ${weekDone} / ${week.tasks.length}</span><button class="link-button" data-go="roadmap">完整路线 ↗</button></div></section>
    <section class="panel side-panel"><div class="panel-heading"><h2>接下来还要学</h2></div>${lessons().filter(t => !taskDone(t)).slice(0,4).map(t => `<div class="next-item"><span class="step-num">${String(t.number).padStart(2,'0')}</span><div><p>${title(t.title)}</p>${t.url ? `<a class="caption" href="${esc(t.url)}" target="_blank" rel="noopener">查看课程 ↗</a>` : '<small>课程待生成 · 用续学指令开始</small>'}</div></div>`).join('') || '<p class="empty">当前课程计划已完成，继续推进周任务。</p>'}
    ${data.topics.filter(t => t.review_due).map(t => `<div class="review">${t.review_due <= data.date ? '建议复习' : '下次复习'} · ${esc(t.review_due)}<br><a href="${esc(t.plan)}" target="_blank" rel="noopener">${esc(t.title)}</a></div>`).join('')}</section>
    <section class="panel side-panel tip"><h3>怎么用这张工作台？</h3><p>打开先看今日计划；学习结束勾选任务，写下收获再打卡。不会的地方记下来，明天接着解决。</p></section>
    ${previousCue()}
    ${data.latest ? `<section class="panel side-panel"><div class="side-label">上次学习留下的线索</div><div class="record-text">${title(data.latest.text.split('**Evidence**')[0])}</div><a class="caption" href="${esc(data.latest.url)}" target="_blank" rel="noopener">查看完整学习记录 ↗</a></section>` : ''}
    </aside></div>`;
}
function previousCue() {
  const previous = data.history.find(h => h.date < data.date && (h.tomorrow || h.notes));
  return previous ? `<section class="panel side-panel"><div class="side-label">上次留给今天的线索 · ${esc(previous.date)}</div><p class="caption">${esc(previous.tomorrow || previous.notes)}</p><a class="caption" target="_blank" href="${esc(previous.url)}" rel="noopener">回看记录 ↗</a></section>` : '';
}
function roadmap() {
  return pageHeader('知道下一步，也看得见全程。', '当前阶段按未完成任务确定；完成后再推进下一阶段。') +
    `<div class="week-grid">${data.weeks.map(w => {
      const done = w.tasks.filter(id => taskDone(data.tasks[id])).length;
      return `<section class="panel"><div class="week-card-heading"><h2>W${String(w.number).padStart(2,'0')} · ${esc(w.title)}</h2><span class="badge ${w.number === data.active ? 'orange' : ''}">${w.number === data.active ? '当前阶段' : `${done}/${w.tasks.length}`}</span></div><div class="progress-track"><span style="width:${w.tasks.length ? done/w.tasks.length*100 : 0}%"></span></div>
      ${w.tasks.map(id => {const t = data.tasks[id];return `<div class="week-task"><span class="mark">${taskDone(t) ? '✓' : '○'}</span><p>${title(t.title)}</p>${!taskDone(t) ? `<button class="button small" data-add="${esc(id)}" ${draft.selected.includes(id) ? 'disabled' : ''}>${draft.selected.includes(id) ? '已加入' : '加入今天'}</button>` : ''}</div>`;}).join('')}</section>`;
    }).join('')}</div>`;
}
function historyView() {
  return pageHeader('每次学习，都留得下痕迹。', '打卡和原有日志都保存在本地 daily/，可以随仓库同步。') + `<section class="panel"><div class="panel-heading"><h2>最近 30 条学习日志</h2><span class="caption">${data.history.filter(h => h.status === '已打卡').length} 条已打卡</span></div>
    ${data.history.map(h => `<article class="history-item"><strong>${esc(h.date)}</strong><div class="log-text"><span class="badge ${h.status !== '已打卡' ? 'orange' : ''}">${esc(h.status)}</span>${h.minutes ? `<span class="caption"> · ${esc(h.minutes)} 分钟</span>` : ''}<p>${esc(h.notes || '查看原始日志，接上上次的学习记录。')}</p></div><a class="button small" href="${esc(h.url)}" target="_blank" rel="noopener">查看日志 ↗</a></article>`).join('') || '<p class="empty">还没有日志。今天保存第一条打卡后，会显示在这里。</p>'}</section>`;
}
function render() {
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  app.innerHTML = view === 'today' ? today() : view === 'roadmap' ? roadmap() : historyView();
}
document.addEventListener('click', async event => {
  const button = event.target.closest('button');
  if (!button || !data) return;
  const action = button.dataset;
  if (action.view || action.go) {view = action.view || action.go; render(); window.scrollTo(0,0);}
  if (action.add) {
    if (!draft.selected.includes(action.add)) draft.selected.push(action.add);
    dirty = true; render(); toast('已加入今日计划，记得保存。');
  }
  if (action.remove) {
    draft.selected = draft.selected.filter(id => id !== action.remove);
    delete draft.changes[action.remove]; dirty = true; render();
  }
  if ('copy' in action) {
    const next = nextLesson();
    const prompt = next ? `请继续 lab 的 ${next.topic} 第 ${next.number} 课：${plain(next.title)}。先读取计划和最近学习记录，接上已有进度，讲透这一课并更新课程页面。` : `请读取 lab/ROADMAP_16W.md 和最近 daily 日志，带我推进 W${data.active} 第一个未完成任务。`;
    try {await navigator.clipboard.writeText(prompt); toast('已复制，粘贴到 Codex 即可开始续学。');}
    catch {toast('复制未成功，请在 Codex 中说“继续当前课程”。', true);}
  }
  if (action.save) {
    saving = true; render();
    try {
      const response = await fetch('/api/save', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...draft, checkin:action.save === 'checkin'})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '保存失败');
      accept(result); toast(action.save === 'checkin' ? `今日已打卡 ✓ 已保存到 daily/${data.date}.md` : '进度已保存，计划与日志已同步。');
    } catch (error) {toast(error.message, true);}
    finally {saving = false; render();}
  }
});
app.addEventListener('change', event => {
  if (event.target.dataset.check) {draft.changes[event.target.dataset.check] = event.target.checked; dirty = true; render();}
});
app.addEventListener('input', event => {
  if (event.target.name && draft) {draft[event.target.name] = event.target.value; dirty = true;}
});
window.addEventListener('beforeunload', event => {if (dirty) {event.preventDefault();event.returnValue = '';}});
load().catch(error => {app.innerHTML = `<div class="error-box">${esc(error.message)}</div>`;});
