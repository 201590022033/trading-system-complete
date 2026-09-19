/* Portfolio is a read model of the worker ledger; controls persist server-side. */
let paperSnapshot = null, paperLoading = false;
const riskProfiles = ['conservative','balanced','aggressive'];
const money = value => Number.isFinite(value) ? 'R '+num(value) : '—';
const sentence = value => String(value || '').replaceAll('_',' ').toLowerCase().replace(/^./, c=>c.toUpperCase());
const emptyPaper = text => `<div class="portfolio-empty">${esc(text)}</div>`;
function paperTable(headings, rows) {
  return `<table><thead><tr>${headings.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(cell=>`<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
function equityPlot(points) {
  if (!points.length) return emptyPaper('The equity history starts with the first completed worker cycle.');
  const values=points.map(x=>x.equity),lo=Math.min(...values),hi=Math.max(...values),pad=Math.max(1,(hi-lo)*.15),width=700,height=180;
  const xy=points.map((p,i)=>`${20+i*660/Math.max(1,points.length-1)},${150-(p.equity-lo+pad)/(hi-lo+2*pad)*120}`).join(' ');
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Paper equity history"><line x1="20" y1="150" x2="680" y2="150" stroke="#283e50"/><polyline points="${xy}" fill="none" stroke="#64deba" stroke-width="3"/><text x="20" y="175">${esc(when(points[0].at))}</text><text x="680" y="175" text-anchor="end">${esc(money(values.at(-1)))}</text></svg>`;
}
function renderPaper(data) {
  paperSnapshot=data;
  const account=data.account,controls=data.controls || {},latest=data.recent_cycles?.[0];
  $('#paper-state').textContent=controls.paused?'Entries paused':sentence(data.state);
  $('#paper-status').textContent=account ? `${controls.paused?'New entries paused':data.state==='STALE'?'Paper cycle overdue':'Paper ledger available'} · Last cycle ${when(data.last_evaluated_at)} · ${data.totals?.cycle || 0} saved cycles` : 'Paper account unavailable: '+sentence(data.state)+'. The worker and database must be configured before trading.';
  $('#paper-status').classList.toggle('is-warning',!account || data.state==='STALE');
  $('#paper-metrics').innerHTML=[['Account value',money(account?.equity),'Simulated equity'],['Available cash',money(account?.available_cash),'Fully funded capital'],['Net performance',account ? money(account.equity-account.starting_cash) : '—','Includes fees and open positions'],['Open positions',account?.position_count ?? '—',`${data.totals?.fill || 0} recorded fills`]].map(([label,value,note])=>`<article class="portfolio-metric"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join('');
  $('#paper-equity').innerHTML=equityPlot(data.equity_history || []);
  const positions=(data.positions || []).map(p=>{const g=data.position_geometry?.[p.instrument_id] || {};return [p.execution_symbol,p.state,num(p.quantity),money(p.average_entry_price),money(p.last_mark),money(g.stop_price),money(g.target_price),money(p.unrealized_pnl)];});
  $('#paper-positions').innerHTML=positions.length ? paperTable(['Share','Side','Quantity','Entry','Current','Stop','Target','Open P&L'],positions) : emptyPaper('No open paper positions. The decision queue explains what the worker is waiting for.');
  const reasons=new Map((latest?.blocked || []).map(x=>[x.instrument_id,x.reason]));
  $('#paper-pending').innerHTML=data.pending?.length ? data.pending.map(p=>`<div class="decision-row"><div><b>${esc(p.instrument_id)}</b><small>Rank ${esc(p.rank)} · ${esc(p.direction)} · ${esc(when(p.evaluated_at))}</small></div><span class="status-chip">${esc(sentence(controls.paused?'PAUSED':p.state==='SHORT_BORROW_UNAVAILABLE'?p.state:reasons.get(p.instrument_id) || p.state))}</span></div>`).join('') : emptyPaper('No eligible proposals are queued yet. Check the latest data and canonical ranking.');
  if (latest?.unavailable?.length) $('#paper-pending').innerHTML+=`<p class="unavailable">Price unavailable: ${esc(latest.unavailable.join(', '))}</p>`;
  $('#paper-fills').innerHTML=data.recent_fills?.length ? paperTable(['Time','Share','Side','Quantity','Fill','Fee'],data.recent_fills.map(f=>[when(f.filled_at),f.instrument_id,f.direction,num(f.quantity),money(f.fill_price),money(f.transaction_cost)])) : emptyPaper('No fills yet. Only observed, risk-approved trades appear here.');
  $('#paper-outcomes').innerHTML=data.recent_outcomes?.length ? paperTable(['Closed','Share','Reason','Net result','Learning horizon'],data.recent_outcomes.map(o=>[when(o.exit_at),o.instrument_id,sentence(o.reason),money(o.net_pnl),o.horizon_id])) : emptyPaper('The first closed paper trade will create a durable outcome.');
  if(document.activeElement!==$('#paper-aggression')) $('#paper-aggression').value=Math.max(0,riskProfiles.indexOf(controls.aggression));
  $('#aggression-label').textContent=sentence(riskProfiles[Number($('#paper-aggression').value)]);
  $('#paper-risk-budget').innerHTML=kv('Risk requested per trade',data.effective_risk_fraction==null?'—':num(data.effective_risk_fraction*100)+'%')+kv('Hard per-trade limit',data.risk_limits?.max_risk_per_trade_fraction==null?'—':num(data.risk_limits.max_risk_per_trade_fraction*100)+'%');
  for(const id of ['#paper-aggression','#save-aggression','#pause-paper','#run-paper-cycle']) $(id).disabled=!data.control_access || !account;
  $('#pause-paper').textContent=controls.paused?'Resume entries':'Pause entries';
  $('#paper-unlock').hidden=!!data.control_access;
  const learning=data.learning || {};
  $('#paper-learning').innerHTML=kv('Closed outcomes',data.totals?.outcome || 0)+kv('Mature one-session outcomes',learning.eligible_outcomes || 0)+kv('Persisted news evidence',learning.persisted_news_records ?? '—')+`<p class="muted">${esc(sentence(learning.state || 'Waiting for worker'))}. ${esc(learning.minimum_samples || 30)} mature samples per instrument are required for learned strategy evidence.</p>`+Object.entries(learning.outcomes_by_instrument || {}).map(([key,n])=>`<label class="learning-progress">${esc(key)} · ${n} / ${learning.minimum_samples}<progress value="${n}" max="${learning.minimum_samples}"></progress></label>`).join('')+'<p class="muted">This measures strategy effectiveness. News AI performs analysis; it does not retrain its model weights.</p>';
  $('#paper-model').innerHTML=kv('Model',data.model || 'Not configured')+kv('Price source',data.data_provider || '—')+kv('Commission per fill',money(data.commission_per_fill))+kv('Slippage per share',money(data.slippage_per_unit))+`<p class="muted">Entries require a later completed market session. Checking again does not invent a new price or bypass a risk limit.</p>`;
}
async function refreshPaper() {
  if(paperLoading)return;paperLoading=true;
  try {renderPaper(await api('/api/paper/status'));}
  catch(e){$('#paper-state').textContent='Unavailable';$('#paper-status').textContent=e.message;}
  finally {paperLoading=false;}
}
async function paperAction(path,body) {
  try {await post(path,body);$('#paper-control-status').textContent='Saved. The worker uses these settings on its next cycle.';await refreshPaper();}
  catch(e){$('#paper-control-status').textContent=e.message;}
}
$('#refresh-paper').onclick=refreshPaper;
$('#paper-aggression').oninput=()=>{$('#aggression-label').textContent=sentence(riskProfiles[Number($('#paper-aggression').value)]);};
$('#save-aggression').onclick=()=>paperAction('/api/paper/controls',{aggression:riskProfiles[Number($('#paper-aggression').value)]});
$('#pause-paper').onclick=()=>paperAction('/api/paper/controls',{paused:!paperSnapshot?.controls?.paused});
$('#run-paper-cycle').onclick=()=>paperAction('/api/paper/cycle',{});
$('#paper-login').onsubmit=async e=>{e.preventDefault();try{await post('/api/paper/session',{key:$('#paper-key').value});$('#paper-key').value='';$('#paper-control-status').textContent='Portfolio controls unlocked.';await refreshPaper();}catch(error){$('#paper-control-status').textContent=error.message;}};
refreshPaper();
setInterval(()=>{if(!document.hidden)refreshPaper();},30000);
