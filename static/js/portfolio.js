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
  const brief=data.decision_brief,market=brief?.market;
  $('#canonical-market-context').textContent=brief?`Daily sampled market context: ${sentence(market?.state)} · completed-price brief ${when(brief.evaluated_at)}. ETF benchmarks are context only; Top 5 ranking is unchanged.`:'Daily market context is waiting for the worker.';
  if(!brief) $('#paper-brief').innerHTML=emptyPaper('No daily brief has been produced by the updated worker yet. This is not a trade signal.');
  else {
    const breadth=market?.sampled_share_breadth_20_sessions;
    const bench=market?.benchmarks || {};
    const context=Object.entries(bench).map(([key,value])=>`${key.replace('ETF_','')} ${num(value.return_20_sessions*100)}%`).join(' · ');
    const history=brief.benchmark_learning?.by_benchmark_and_market_state || {};
    const regimeChecks=Object.entries(history).map(([key,states])=>{
      const item=states[market?.state];
      return item?`${key.replace('ETF_','')}: ${item.nonoverlapping_sessions} independent periods, mean ${num(item.mean_gross_return*100)}% gross` : null;
    }).filter(Boolean).join(' · ');
    const ideas=(brief.ideas || []).map(x=>[x.symbol || x.instrument_id,`#${x.rank} · ${x.sector}`,sentence(x.state),x.reason,`R ${num(x.minimum_one_share_notional)}`]);
    $('#paper-brief').innerHTML=kv('Market context',sentence(market?.state || 'Unavailable'))+kv('Sampled share breadth',breadth==null?'—':`${num(breadth*100)}% of ${market.sampled_share_count}`)+kv('Listed ETF 20-session moves',context || 'Unavailable')+kv('Later market outcomes in this state',regimeChecks || 'Not mature yet')+`<p class="muted">Completed daily prices as of ${esc(when(brief.evaluated_at))}. This is a sampled market view, not the full JSE. ETF outcome comparisons are gross before spread and fees, and are not trade recommendations.</p>`+(ideas.length?`<div class="table-scroll">${paperTable(['Cash share','Legacy rank · sector','Review state','Why','One-share close proxy'],ideas)}</div>`:emptyPaper('No eligible review ideas in this daily brief.'))+`<p class="muted">Affordability uses R ${esc(num(brief.simulated_available_cash))} of simulated cash, not your connected account. Delayed closes are not executable quotes. Verify current price, spread, fees, available real cash and risk yourself; no live order is placed. The internal paper simulator still runs its legacy benchmark independently of this shadow brief.</p>`;
  }
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
  // Shared unlock visibility is controlled by the connected-account workspace.
  const learning=data.learning || {},panel=data.candidate_learning || {};
  const strategy=data.strategy_learning || {};
  const swingLearning=data.swing_technical_learning || {};
  const swingPolicy=data.swing_policy_shadow || {};
  const igData=data.ig_swing_data;
  const alphaData=data.alpha_vantage_data;
  const edge=panel.mean_selection_edge==null?'—':num(panel.mean_selection_edge*100)+'%';
  const conditions=Object.entries(panel.by_market_state || {}).map(([state,value])=>`<p class="muted">${esc(sentence(state))}: ${esc(value.nonoverlapping_sessions)} independent comparisons; selected net ${esc(num(value.mean_selected_net_return*100))}% vs other ${esc(num(value.mean_other_net_return*100))}% and cash 0%. ${esc(sentence(value.state))}.</p>`).join('');
  $('#paper-learning').innerHTML=kv('Candidate outcomes',panel.outcome_count ?? 0)+kv('Matched sessions',panel.paired_sessions ?? 0)+kv('Independent comparisons',`${panel.nonoverlapping_paired_sessions ?? 0} / ${panel.minimum_nonoverlapping_sessions ?? 30}`)+kv('Observed selection edge',edge)+conditions+`<p class="muted">${esc(sentence(panel.state || 'Waiting for candidate outcomes'))}. Each screened share is compared with unselected shares and cash from the same session after a three-session hold, using a later completed close as entry proxy and declared costs. This is shadow research, not a validated forecast or live order.</p>`+`<p class="muted">Legacy selected-only outcomes: ${esc(learning.eligible_outcomes || 0)}. Actual closed paper trades: ${esc(data.totals?.outcome || 0)}. News AI does not retrain its model weights.</p>`;
  $('#paper-learning').innerHTML=kv('Strategy evidence pool',strategy.strategy_profile_id ? `${strategy.strategy_profile_id} / ${strategy.strategy_profile_version}` : 'LEGACY_UNATTRIBUTED')+kv('Closed outcomes in this version / horizon',strategy.eligible_closed_outcomes ?? 'Unavailable')+`<p class="muted">Other strategy versions and unattributed history do not enter this pool. Sample counts are not proof of a trading edge; simulated fees are not verified OST fees.</p>`+$('#paper-learning').innerHTML;
  $('#paper-learning').innerHTML+=`<h4>EMA/ATR Swing shadow · ${esc(swingLearning.strategy_profile_version || 'not started')}</h4>`+Object.entries(swingLearning.horizons || {}).map(([h,row])=>kv(`${h} observed-session outcomes`,`${row.sample_count} samples; ${row.negative_count} negative; assumed net ${row.mean_net_return_assumed == null?'unavailable':num(row.mean_net_return_assumed*100)+'%'}`)).join('')+`<p class="muted">Separate next-close forward returns, not stop/target fills. EMA trend, breakout and reclaim cohorts are observational, not proof that an indicator caused profit. Fees assume 10 bps, not OST costs. The original paper simulator remains unchanged.</p>`;
  $('#paper-learning').innerHTML+=`<h4>Daily Swing policy shadow · ${esc(swingPolicy.strategy_profile_version || 'not started')}</h4>`+kv('Policy decisions',swingPolicy.decision_count ?? 'Unavailable')+Object.entries(swingPolicy.decision_states || {}).map(([state,count])=>kv(sentence(state),count)).join('')+Object.entries(swingPolicy.horizons || {}).map(([h,row])=>kv(`${h} session shadow exits`,`${row.closed_count} closed; ${row.negative_count_10bps} negative at assumed 10 bps; ${row.ambiguous_count} ambiguous stop-first bars`)+Object.entries(row.mean_net_return_scenarios || {}).map(([bps,value])=>kv(`Mean net with assumed ${bps} bps cost`,value==null?'Unavailable':num(value*100)+'%')).join('')).join('')+`<p class="muted">Separate cash-only setup simulation: later completed-close entry, fixed structural/ATR stop, 2R target and 3/4/5 observed-session exits. Daily bars use conservative stop-first handling when ordering is unknown. Costs are hypothetical, not verified OST fees. Overlapping setups are not a portfolio or validated edge. Liquidity, calendar and account risk approval remain unresolved; no orders or promotion.</p>`;
  $('#paper-model').innerHTML=kv('Model',data.model || 'Not configured')+kv('Price source',data.data_provider || '—')+kv('Commission per fill',money(data.commission_per_fill))+kv('Slippage per share',money(data.slippage_per_unit))+`<p class="muted">Entries require a later completed market session. Checking again does not invent a new price or bypass a risk limit.</p>`;
  if(igData) $('#paper-model').innerHTML+=`<h4>IG data readiness for Swing</h4>`+kv('Read-only check',sentence(igData.state))+Object.entries(igData.instruments || {}).map(([key,row])=>kv(key,sentence(row.state))+kv(`${key} traded volume`,row.history?.volume_quality ? sentence(row.history.volume_quality.state) : 'Not measurable: historical prices unavailable')).join('')+`<p class="muted">IG prices have not replaced the cash-share feed. Equity access, matching JSE sessions, cash-price basis and traded-volume coverage must be verified first. Missing volume is never invented.</p>`;
  if(alphaData) $('#paper-model').innerHTML+=`<h4>Yahoo data repair</h4>`+kv('Alpha Vantage fallback',sentence(alphaData.state))+Object.entries(alphaData.instruments || {}).filter(([,row])=>row.state!=='YAHOO_VALID').map(([key,row])=>kv(key,`${sentence(row.state)} · ${row.repaired_sessions?.length || 0} repaired · ${row.unresolved_sessions?.length || 0} unresolved`)).join('')+`<p class="muted">Only invalid or missing completed Yahoo bars trigger a fallback check. Free history covers up to 100 observations; older gaps may remain. Repairs require matching JSE identity and closing price. Cash ranking and paper fills retain their existing source.</p>`;
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
$('#paper-login').onsubmit=async e=>{e.preventDefault();try{await post('/api/paper/session',{key:$('#paper-key').value});$('#paper-key').value='';$('#paper-control-status').textContent='Journal and portfolio controls unlocked.';window.dispatchEvent(new Event('portfolio-auth-changed'));await refreshPaper();}catch(error){$('#paper-control-status').textContent=error.message;}};
refreshPaper();
setInterval(()=>{if(!document.hidden)refreshPaper();},30000);
