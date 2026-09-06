const $ = s => document.querySelector(s);
const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = v => Number.isFinite(v) ? v.toLocaleString('en-ZA', {maximumFractionDigits:2}) : '—';
const when = v => v ? (Number.isNaN(Date.parse(v)) ? v : new Date(v).toLocaleString('en-ZA')) : 'Not supplied';
let instruments = [], newsSnapshot = null, feedBusy = false, selectionVersion = 0;
let chartPoll = null, newsPoll = null;
async function api(url, options = {}) {
  const response = await fetch(url, {...options, signal: AbortSignal.timeout(15000)});
  const data = await response.json();
  if (!response.ok) throw Error(data.error || data.reason || `Request failed (${response.status})`);
  return data;
}
const post = (url, body = {}) => api(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
function kv(name, value) { return `<div class="kv"><span>${esc(name)}</span><span>${esc(value)}</span></div>`; }
function component(c) {
  if (!c) return 'Not run';
  const d = c.data || {};
  return `<span class="state">${esc(c.state)}</span>${kv('Source',c.source)}${kv('Source time',c.source_timestamp)}${kv('Retrieved',c.retrieved_at)}${c.reason ? kv('Note',c.reason) : ''}` +
    Object.entries(d).filter(([key]) => !['recent_prices','metrics','items','macro'].includes(key)).slice(0,8).map(([key,value])=>kv(key,typeof value === 'number' ? num(value) : value)).join('') +
    Object.entries(d.metrics || {}).map(([key,value]) => kv(key,num(value))).join('') +
    (d.items || []).map(item => `<p>${esc(item.headline)} <small>${esc(item.llm_used ? 'AI' : 'Keywords')}</small></p>`).join('');
}
function render(run) {
  $('#notice').textContent = `Run ${run.run_id} · ${run.overall_state} · ${when(run.completed_at)}`;
  $('#action').textContent = run.decision.action.toUpperCase();
  $('#reason').textContent = run.decision.reason;
  $('#score').textContent = Number(run.decision.score).toFixed(3);
  $('#market').innerHTML = component(run.components.market);
  $('#technical-result').innerHTML = component(run.components.technical);
  $('#news-result').innerHTML = component(run.components.news);
  const gates = run.gates;
  $('#gate-summary').textContent = `Buy ${gates.buy} · Sell ${gates.sell} · Neutral ${gates.neutral} · Unavailable ${gates.unavailable}`;
  $('#gates').innerHTML = gates.results.map(g => `<div class="gate ${g.outcome.includes('BUY')?'buy':g.outcome.includes('SELL')?'sell':g.outcome==='UNAVAILABLE'?'unavailable':''}"><b>${esc(g.gate.replaceAll('_',' '))}</b><small>${esc(g.category)} · ${esc(g.outcome)}</small><small>${esc(g.source)}</small></div>`).join('');
}
function drawChart(target, result, title) {
  const node = $(target), data = result.data, bars = data?.bars || [];
  if (!bars.length) {
    node.innerHTML = `<div class="chart-empty">${esc(title)} · ${esc(result.state)}<br>${esc(result.error || 'Waiting for timestamped public price history…')}</div>`;
    return;
  }
  const width = 650, height = 225, left = 68, right = 15, top = 18, bottom = 32;
  const values = bars.map(b=>b.close), minimum = Math.min(...values), maximum = Math.max(...values);
  const pad = (maximum - minimum) * .1 || maximum * .01 || 1;
  const low = minimum - pad, high = maximum + pad;
  const x = i => left + i / Math.max(1, bars.length - 1) * (width - left - right);
  const y = price => top + (high - price) / (high - low) * (height - top - bottom);
  const points = bars.map((bar,i) => `${x(i)},${y(bar.close)}`).join(' ');
  let axes = '';
  for (let i=0;i<4;i++) {
    const value = low + (high-low)*i/3, yy = y(value);
    axes += `<line x1="${left}" x2="${width-right}" y1="${yy}" y2="${yy}" stroke="#273749"/><text x="${left-8}" y="${yy+4}" text-anchor="end">${esc(num(value))}</text>`;
  }
  const label = bar => data.interval === '5m' ? when(bar.timestamp) : bar.timestamp.slice(0,10);
  node.innerHTML = `<div class="chart-meta"><span class="state">${esc(result.state)} · ${esc(result.data_state)}</span> ${esc(data.symbol)} · ${esc(data.currency)} · ${esc(data.interval)} bars<br>Bar: ${esc(label(bars.at(-1)))} · Retrieved: ${esc(when(result.last_success))}<br>${esc(result.error || result.note)}</div>
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)} closing-price chart in ${esc(data.currency)}"><title>${esc(title)}: ${esc(label(bars[0]))} to ${esc(label(bars.at(-1)))}</title>${axes}<polyline points="${points}" fill="none" stroke="#46a6ff" stroke-width="2.5"/><circle cx="${x(bars.length-1)}" cy="${y(bars.at(-1).close)}" r="3" fill="#46a6ff"/><text x="${left}" y="${height-6}">${esc(label(bars[0]))}</text><text x="${width-right}" y="${height-6}" text-anchor="end">${esc(label(bars.at(-1)))}</text></svg>
    <div class="chart-readout">Latest ${esc(num(bars.at(-1).close))} ${esc(data.currency)} · ${esc(num(data.change_pct))}% over selected period · hover for a dated value</div>`;
  node.querySelector('svg').onpointermove = event => {
    const box = event.currentTarget.getBoundingClientRect();
    const pos = ((event.clientX - box.left) / box.width * width - left) / (width - left - right);
    const bar = bars[Math.max(0, Math.min(bars.length-1, Math.round(pos*(bars.length-1))))];
    node.querySelector('.chart-readout').textContent = `${label(bar)} · Close ${num(bar.close)} ${data.currency} · Volume ${num(bar.volume)}`;
  };
}
function showNews(result) {
  newsSnapshot = result;
  const report = result.data || {}, all = report.items || [];
  const selected = instruments.find(i=>i.instrument_id === $('#instrument').value);
  const items = $('#news-filter').value === 'selected' ? all.filter(i=>i.assets.some(a=>a.name === selected?.research_symbol)) : all;
  $('#news-status').textContent = `${result.state}${result.refreshing ? ' · Refresh in progress' : ''} · ${report.analysis_method || 'Fetching headlines and analysing sentiment'} · Last scan: ${when(result.last_success)}. ${result.error || ''} ${Object.entries(report.sources || {}).map(([s,v])=>`${s}: ${v}`).join(' · ')}`;
  $('#macro-summary').innerHTML = Object.entries(report.macro || {}).filter(([,v])=>v.mentions).map(([name,v])=>`<span class="macro-card ${v.score>0?'buy':v.score<0?'sell':''}">${esc(name)} ${esc(num(v.score))} · ${v.mentions} mentions</span>`).join('');
  $('#headlines').innerHTML = items.length ? items.map(item => {
    let link = '';
    try { const u = new URL(item.url); if (['http:','https:'].includes(u.protocol)) link = u.href; } catch {}
    const title = link ? `<a href="${esc(link)}" target="_blank" rel="noopener noreferrer">${esc(item.headline)} ↗</a>` : esc(item.headline);
    return `<article class="headline"><span class="tag ${item.score>0?'buy':item.score<0?'sell':''}">${esc(item.sentiment)} · ${esc(num(item.score))}</span><span class="tag">${item.llm_used ? 'AI analysed' : 'Keyword fallback'}</span><h4>${title}</h4><p>${esc(item.summary)}</p><small>${esc(item.source)} · ${esc(item.timestamp_kind || 'published')}: ${esc(when(item.timestamp))}</small><div>${item.assets.map(a=>`<span class="tag">${esc(a.name)} ${a.direction>0?'↑':a.direction<0?'↓':'↔'}</span>`).join('')}</div></article>`;
  }).join('') : `<p class="muted">${result.state === 'LOADING' ? 'Fetching public headlines. AI analysis runs in the background.' : 'No headlines available for this filter. Source status is shown above.'}</p>`;
}
async function refreshCharts() {
  clearTimeout(chartPoll);
  const symbol = $('#instrument').value, period = $('#chart-period').value, version = selectionVersion;
  let pending = false;
  if (!symbol) return;
  await Promise.allSettled([['#stock-chart',symbol],['#index-chart','JSE']].map(async ([target,id])=>{
    try {
      const result = await api(`/api/feed/market/${id}?period=${period}`);
      pending ||= result.refreshing;
      if (version === selectionVersion) drawChart(target,result,id);
    } catch (error) { if (version === selectionVersion) drawChart(target,{state:'UNAVAILABLE',error:error.message},id); }
  }));
  // Finish an explicitly requested load even when periodic refresh is paused.
  if (pending && version === selectionVersion) chartPoll = setTimeout(refreshCharts,2000);
}
async function refreshNews() {
  clearTimeout(newsPoll);
  try {
    const result = await api('/api/feed/news');
    showNews(result);
    if (result.refreshing) newsPoll = setTimeout(refreshNews,2000);
  }
  catch (error) { $('#news-status').textContent = `News refresh failed: ${error.message}. Previously displayed items may be stale.`; }
}
async function refreshOpportunities() {
  $('#opportunity-status').textContent = 'Scanning broad public universe and combining available evidence…';
  try {
    const result = await api('/api/opportunities'), data = result.data || {};
    $('#opportunity-status').textContent = `${result.state} · scanned ${data.scanned || 0} of ${data.universe_size || 0} · ${data.method || ''} · ${when(result.last_success)}`;
    $('#opportunities').innerHTML = (data.opportunities || []).length ? `<table><tr><th>Share</th><th>Combined</th><th>20d</th><th>RSI</th><th>News</th><th>Evidence</th></tr>${data.opportunities.map(row=>`<tr><td><b>${esc(row.symbol)}</b><br><small>${esc(row.name)}</small></td><td>${esc(num(row.combined_score))}</td><td>${esc(num(row.momentum_20d_pct))}%</td><td>${esc(num(row.rsi_14))}</td><td>${esc(row.news_mentions || 0)} mentions</td><td>${esc(row.state)}<br><small>${esc((row.evidence || []).join(' · '))}</small></td></tr>`).join('')}</table>` : '<p class="muted">No current candidates with sufficient public data.</p>';
  } catch (error) { $('#opportunity-status').textContent = `Discovery failed: ${error.message}`; }
}
async function refreshQuotes() {
  await Promise.allSettled(instruments.map(async item=>{
    const card = $(`#quote-${item.instrument_id}`);
    try {
      const result = await api(`/api/feed/market/${item.instrument_id}?period=1d`), data = result.data;
      card.innerHTML = `${esc(item.display_symbol)}<strong>${esc(num(data?.price))} <small>${esc(data?.currency || '')}</small></strong><small>${esc(result.state)} · ${esc(result.data_state)}</small><small>${esc(data ? when(data.source_timestamp) : result.error || 'Fetching…')}</small>`;
    } catch { card.innerHTML = `${esc(item.display_symbol)}<strong>Unavailable</strong><small>Refresh failed</small>`; }
  }));
}
async function refreshFeeds() {
  if (feedBusy) return;
  feedBusy = true;
  try {
    await Promise.allSettled([refreshCharts(),refreshNews(),refreshQuotes()]);
    $('#feed-notice').textContent = `Checked ${new Date().toLocaleTimeString('en-ZA')} · Price refresh up to 60 seconds; daily history/news up to 5 minutes. See each source's result and timestamp.`;
  } finally { feedBusy = false; }
}
function selectedChanged() {
  selectionVersion++;
  $('#chart-title').textContent = `${$('#instrument').value} · Price history`;
  $('#stock-chart').innerHTML = '<div class="chart-empty">Loading selected chart…</div>';
  document.querySelectorAll('.quote').forEach(q=>q.classList.toggle('selected',q.dataset.instrument === $('#instrument').value));
  refreshCharts();
  if (newsSnapshot) showNews(newsSnapshot);
}
function action(selector, handler) {
  $(selector).onclick = async () => {
    const button = $(selector); button.disabled = true;
    try { await handler(); } catch(error) { $('#notice').textContent = `Unable to complete request: ${error.message}`; }
    finally { button.disabled = false; }
  };
}
document.querySelectorAll('nav button').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('.tab').forEach(tab=>tab.classList.remove('active'));
  $('#'+button.dataset.tab).classList.add('active');
});
action('#run',async()=>render(await post(`/api/analysis/${$('#instrument').value}`,{horizon:$('#horizon').value,provider:$('#provider').value,allow_network:true})));
action('#technical',async()=>$('#technical-result').innerHTML=component(await post(`/api/analysis/${$('#instrument').value}/technical`)));
action('#news',async()=>{await refreshNews(); $('#news-result').innerHTML=component(await post(`/api/analysis/${$('#instrument').value}/news`,{allow_network:true}));});
action('#scan',async()=>{
  const result=await post('/api/scan/market',{horizon:$('#horizon').value});
  $('#scan-result').innerHTML=`<p class="muted">Historical technical benchmark · see market pulse above for current public prices.</p><table><tr><th>Instrument</th><th>Decision</th><th>Score</th><th>State</th></tr>${result.runs.map(r=>`<tr><td>${esc(r.instrument.display_symbol)}</td><td>${esc(r.decision.action.toUpperCase())}</td><td>${esc(r.decision.score)}</td><td>${esc(r.overall_state)}</td></tr>`).join('')}</table>`;
});
action('#research-load',async()=>$('#research-result').textContent=JSON.stringify(await api(`/api/research/${$('#instrument').value}`),null,2));
action('#refresh-feeds',refreshFeeds);
action('#refresh-news',refreshNews);
action('#refresh-opportunities',refreshOpportunities);
$('#instrument').onchange=selectedChanged;
$('#chart-period').onchange=()=>{selectionVersion++; refreshCharts();};
$('#news-filter').onchange=()=>{if(newsSnapshot) showNews(newsSnapshot);};
$('#auto-refresh').onchange=()=>{if($('#auto-refresh').checked) refreshFeeds();};
(async()=>{
  const [status,universe]=await Promise.all([api('/api/system/status'),api('/api/instruments')]);
  instruments=universe.instruments;
  $('#system-pill').textContent='PUBLIC FEEDS · RESEARCH ONLY';
  $('#system-result').textContent=JSON.stringify(status,null,2);
  $('#instrument').innerHTML=instruments.map(i=>`<option value="${i.instrument_id}">${esc(i.display_symbol)} · ${esc(i.name)}</option>`).join('');
  $('#quotes').innerHTML=instruments.map(i=>`<button class="quote" id="quote-${i.instrument_id}" data-instrument="${i.instrument_id}">${esc(i.display_symbol)}<strong>Connecting…</strong></button>`).join('');
  document.querySelectorAll('.quote').forEach(card=>card.onclick=()=>{$('#instrument').value=card.dataset.instrument; selectedChanged();});
  selectedChanged();
  await refreshFeeds();
  await refreshOpportunities();
  setInterval(()=>{if($('#auto-refresh').checked && !document.hidden) refreshFeeds();},10000);
})().catch(error=>{$('#system-pill').textContent='SYSTEM UNAVAILABLE';$('#feed-notice').textContent=error.message;});
