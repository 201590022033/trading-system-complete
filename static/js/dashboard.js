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
function canonicalList(items, emptyText) {
  return items?.length ? `<ul>${items.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>` : `<p class="muted">${esc(emptyText)}</p>`;
}
function renderCanonicalCard(item) {
  const regime = item.regime_context || {}, divergence = item.divergence_summary || {}, evidence = item.feature_evidence_summary || {};
  return `<article class="panel canonical-card" data-opportunity-id="${esc(item.opportunity_id)}">
    <div class="row"><div><span class="canonical-rank">Rank ${esc(item.rank)}</span><h3>${esc(item.instrument_id)} · ${esc(item.direction)}</h3><span class="canonical-status">${esc(item.eligibility_status)}</span></div><div><div class="canonical-score">${esc(item.ranking_score == null ? 'Not scored' : `${num(item.ranking_score)} / 100`)}</div><small>Opportunity Score</small></div></div>
    ${kv('Horizon',item.horizon_id)}${kv('Suitability',item.suitability_status)}${kv('Execution suitability',item.execution_suitability)}${kv('Data grade',item.data_grade)}${kv('Regime',regime.trend || regime.availability)}${kv('Divergence',divergence.state)}${kv('Evidence',`${evidence.learned_count ?? '—'} learned · ${evidence.sample_count ?? item.sample_count ?? '—'} samples`)}
    <h4>Why it ranks</h4>${canonicalList(item.reasons,'No ranking reasons supplied.')}
    <h4>Uncertainty and blockers</h4>${canonicalList([...(item.uncertainty || []),...(item.blockers || [])],'None reported by the canonical API.')}
    <details><summary>Policy, risk and provenance</summary><div class="canonical-detail" role="region" aria-label="Policy and risk detail for ${esc(item.instrument_id)}"><p class="muted">Load detail to preserve authoritative upstream state.</p></div></details>
  </article>`;
}
async function canonicalFetch(url) {
  const response=await fetch(url,{signal:AbortSignal.timeout(15000)}),data=await response.json();
  if (!response.ok && response.status !== 409) throw Error(data.error?.message || `Canonical service unavailable (${response.status})`);
  return data;
}
async function loadCanonicalDetail(card) {
  const id=encodeURIComponent(card.dataset.opportunityId),node=card.querySelector('.canonical-detail');
  node.textContent='Loading policy and risk state…';
  try {
    const [policyResult,riskResult,intentResult]=await Promise.allSettled([canonicalFetch(`/api/v1/opportunities/${id}/policy`),canonicalFetch(`/api/v1/opportunities/${id}/risk`),canonicalFetch(`/api/v1/opportunities/${id}/intent`)]);
    const policy=policyResult.value?.policy,risk=riskResult.value?.risk,intent=intentResult.value?.intent;
    node.innerHTML=`<h4>TradePolicy</h4>${kv('Direction',policy?.direction)}${kv('Entry timing',policy?.entry?.timing)}${kv('Entry reference',policy?.entry?.reference)}${kv('Stop status',policy?.stop?.status)}${kv('Stop price',policy?.stop?.price == null ? 'Unresolved' : policy.stop.price)}${kv('Target status',policy?.target?.status)}${kv('Time exit',policy?.target?.time_exit)}${kv('Invalidation',policy?.invalidation?.condition)}
      <h4>Risk</h4>${kv('Risk status',risk?.status || intent?.risk?.status || 'Unavailable')}${kv('Approved size',risk?.approved_position_size == null ? 'Not available' : risk.approved_position_size)}${kv('Approved loss budget',risk?.approved_loss_budget == null ? 'Not available' : risk.approved_loss_budget)}${kv('Intent readiness',intent?.execution_readiness || 'Not available')}${canonicalList([...(risk?.blockers || []),...(risk?.rejection_reasons || []),...(intent?.blockers || [])],'No risk blockers reported.')}
      <h4>Provenance</h4><pre>${esc(JSON.stringify(intent?.provenance || policy?.provenance || {},null,2))}</pre>`;
  } catch(error) { node.innerHTML=`<p class="unavailable">Detail unavailable: ${esc(error.message)}</p>`; }
}
async function refreshCanonicalOpportunities() {
  const status=$('#canonical-status'),cards=$('#canonical-cards');status.textContent='Refreshing canonical ranking…';
  try {
    const result=await canonicalFetch('/api/v1/opportunities?limit=5'),items=result.opportunities;
    if (!Array.isArray(items)) throw Error('Malformed canonical response');
    status.textContent=`${items.length} canonical research opportunit${items.length===1?'y':'ies'} available.`;
    cards.innerHTML=items.length ? items.map(renderCanonicalCard).join('') : '<div class="panel canonical-empty"><h3>No canonical opportunities available yet.</h3><p class="muted">Canonical ranking data has not yet been populated. Legacy recommendations are not substituted.</p></div>';
    cards.querySelectorAll('details').forEach(detail=>detail.addEventListener('toggle',()=>{if(detail.open&&!detail.dataset.loaded){detail.dataset.loaded='true';loadCanonicalDetail(detail.closest('.canonical-card'));}}));
  } catch(error) { status.textContent='Canonical opportunity service is unavailable.';cards.innerHTML=`<div class="panel canonical-empty canonical-error"><h3>Unable to load canonical opportunities.</h3><p class="muted">${esc(error.message)} No recommendation has been substituted.</p></div>`; }
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
    await Promise.allSettled([refreshCharts(),refreshNews(),refreshQuotes(),refreshTicker()]);
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
  if (!$(selector)) return;
  $(selector).onclick = async () => {
    const button = $(selector); button.disabled = true;
    try { await handler(); } catch(error) { $('#notice').textContent = `Unable to complete request: ${error.message}`; }
    finally { button.disabled = false; }
  };
}
async function refreshSources() {
  const result = await api('/api/market-intelligence/sources');
  $('#sources').innerHTML = (result.sources || []).map(s => `<label class="source-row"><input type="checkbox" data-source="${esc(s.source_id)}" ${s.enabled ? 'checked' : ''}> <b>${esc(s.source_name)}</b><small>${esc(s.status)} · ${esc(s.access_mode)} · ${esc(s.url || '')}</small></label>`).join('') || '<p class="muted">No configured sources.</p>';
  document.querySelectorAll('[data-source]').forEach(box => box.onchange = async () => { await post(`/api/market-intelligence/sources/${encodeURIComponent(box.dataset.source)}`, {enabled: box.checked}); });
}
function renderIntelligence(data) {
  const n=data.narrative;
  $('#intelligence-state').textContent=n ? `Snapshot generated ${when(n.generated_at)} · provider ${n.provider || 'not supplied'}` : 'No current narrative is available; no market intelligence has been substituted.';
  $('#narrative').innerHTML=n ? `<h3>What is happening?</h3><p>${esc(n.summary)}</p>` : '';
  $('#themes').innerHTML=n?.themes?.length ? `<h3>Key themes</h3>${n.themes.map(t=>`<article class="theme-card"><b>${esc(t.theme)}</b><span>${esc(t.direction > 0 ? 'Positive' : t.direction < 0 ? 'Negative' : 'Neutral')} · confidence ${esc(t.confidence)} · ${esc(t.expected_horizon)}</span></article>`).join('')}` : '<p class="muted">No structured themes currently available.</p>';
  const entries=data.selections || n?.candidates || [];
  $('#ai-watchlist').innerHTML=entries.length ? `<h3>Watch / investigate</h3>${entries.map(x=>`<article class="watch-card"><b>${esc(x.display_symbol || x.instrument_id)}</b><span>${x.pinned ? '📌 Pinned' : '✦ AI-selected'}</span><p>${esc(x.reason || 'No explanation supplied.')}</p><small>${esc(x.theme || 'No theme')} · confidence ${esc(x.confidence)} · review ${esc(when(x.review_at))}</small></article>`).join('')}` : '<p class="muted">No AI watchlist candidates are available.</p>';
}
async function refreshIntelligence() { try { renderIntelligence(await api('/api/market-intelligence')); } catch(e) { $('#intelligence-state').textContent=`Market intelligence unavailable: ${e.message}`; } }
async function refreshTicker() {
  try { const result=await api('/api/market-intelligence/ticker'); if (!result.items?.length) { $('#quotes').innerHTML='<p class="muted">No pinned or AI-selected market instruments are currently available.</p>'; return; }
    $('#quotes').innerHTML=result.items.map(i=>`<button class="quote" data-instrument="${esc(i.instrument_id)}"><b>${esc(i.display_symbol)}</b><small>${i.pinned?'📌 Pinned':'✦ AI-selected'} · ${esc(i.reason)}</small><small>Watch / investigate · confidence ${esc(i.confidence)}</small></button>`).join('');
    document.querySelectorAll('.quote').forEach(card=>card.onclick=()=>{ $('#instrument').value=card.dataset.instrument; selectedChanged(); });
  } catch(e) { $('#quotes').innerHTML='<p class="muted">Ticker unavailable; no market data has been substituted.</p>'; }
}
function renderPortfolio(rows) {
  $('#portfolio-table').innerHTML = rows.length ? `<table><tr>${Object.keys(rows[0]).map(k=>`<th>${esc(k)}</th>`).join('')}</tr>${rows.map(r=>`<tr>${Object.keys(rows[0]).map(k=>`<td>${esc(r[k])}</td>`).join('')}</tr>`).join('')}</table>` : '<p class="muted">No portfolio snapshot loaded.</p>';
}
function renderLearningStatus(data) {
  const windows = ['24h','3d','7d'];
  const metric = (name,label) => `<div class="learning-metric"><b>${esc(label)}</b>${windows.map(w=>`<span>${esc(w)}: ${esc(data[name]?.[w] ?? 0)}</span>`).join('')}</div>`;
  const latest = Object.entries(data.latest_timestamps || {}).map(([name,value])=>`<div class="kv"><span>${esc(name.replaceAll('_',' '))}</span><span>${esc(value || '—')}</span></div>`).join('');
  const worker = data.worker_status || {};
  $('#learning-status').innerHTML = `<div class="learning-grid">${metric('observations','Observations')}${metric('shadow_decisions','Shadow decisions')}${metric('labelled_outcomes','Labelled outcomes')}${metric('adaptive_updates','Adaptive updates')}</div><div class="kv"><span>Pending outcomes</span><span>${esc(data.pending_outcomes ?? 0)}</span></div><div class="kv"><span>Worker</span><span>${esc(worker.status || 'UNKNOWN')}</span></div><div class="kv"><span>Database</span><span>${esc(data.database_backend || 'UNKNOWN')} · ${esc(data.database_state || 'UNKNOWN')}</span></div><details><summary>Latest timestamps</summary>${latest || '<p class="muted">No persisted events yet.</p>'}</details>`;
}
async function refreshLearningStatus() { try { renderLearningStatus(await api('/api/learning/status')); } catch(e) { $('#learning-status').textContent=`Learning status unavailable: ${e.message}`; } }
async function loadPortfolio() { const result = await api('/api/portfolio'); renderPortfolio(result.rows || []); }
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
action('#refresh-canonical',refreshCanonicalOpportunities);
action('#load-technical-intelligence',async()=>{ const r=await api(`/api/technical-intelligence/${encodeURIComponent($('#instrument').value)}`); $('#technical-flow').innerHTML=r.flow.map(n=>`<div class="flow-node"><b>${esc(n.label)}</b><span>${esc(n.state)}</span></div>`).join(''); $('#indicator-inventory').innerHTML=`<h3>Indicators</h3><table><tr><th>Indicator</th><th>State</th><th>Value</th><th>Signal</th><th>Reason</th></tr>${r.indicators.map(i=>`<tr><td>${esc(i.name)}</td><td>${esc(i.state)}</td><td>${esc(i.value)}</td><td>${esc(i.signal)}</td><td>${esc(i.reason || '')}</td></tr>`).join('')}</table>`; });
action('#reload-sources',refreshSources);
action('#reload-intelligence',refreshIntelligence);
action('#refresh-learning-status',refreshLearningStatus);
action('#import-portfolio',async()=>{ const result=await post('/api/portfolio/csv',{csv:$('#portfolio-csv').value}); $('#portfolio-status').textContent=`Imported ${result.count} position(s) · CSV snapshot only`; renderPortfolio(result.rows); });
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
  await Promise.allSettled([refreshSources(), refreshIntelligence(), refreshTicker(), loadPortfolio(), refreshLearningStatus()]);
  await refreshCanonicalOpportunities();
  await refreshOpportunities();
  setInterval(()=>{if($('#auto-refresh').checked && !document.hidden) refreshFeeds();},10000);
})().catch(error=>{$('#system-pill').textContent='SYSTEM UNAVAILABLE';$('#feed-notice').textContent=error.message;});
