/* Broker cash is a display aggregate. This journal never places orders. */
let connected=null, selectedAccount=null, entryId=crypto.randomUUID(), accountsBusy=false;
const cashLabel=(value,currency)=>Number.isFinite(value)?`${currency} ${num(value)}`:'Unavailable';
function chooseAccount(key) {
  selectedAccount=key;
  $('#journal-close').hidden=true;
  $('#journal-entry').reset();entryId=crypto.randomUUID();
  renderConnected();refreshJournal();
}
function renderConnected() {
  if(!connected)return;
  $('#paper-unlock').hidden=!!connected.control_access;
  $('#connected-totals').innerHTML=['DEMO','LIVE'].map(mode=>{
    const group=connected.groups[mode];
    const originals=group?Object.entries(group.by_currency).map(([c,v])=>cashLabel(v,c)).join(' + '):'No connected accounts';
    return `<article class="portfolio-metric"><span>${mode==='DEMO'?'Combined demo available funds':'Real-money available funds'}</span><strong>${group?cashLabel(group.zar_total,'ZAR'):'Not connected'}</strong><small>${esc(originals)}</small>${group&&!group.complete?'<small>Incomplete: missing balance or dated FX. No total guessed.</small>':''}</article>`;
  }).join('');
  $('#connected-tabs').innerHTML=connected.accounts.map(a=>`<button role="tab" aria-selected="${a.key===selectedAccount}" data-account="${esc(a.key)}">${esc(a.broker)} · ${esc(a.environment)} · …${esc(a.account_id.slice(-3))}</button>`).join('')+'<button role="tab" aria-selected="'+(selectedAccount==='standard-bank')+'" data-account="standard-bank">Standard Bank · not connected</button>';
  $('#connected-tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>chooseAccount(b.dataset.account));
  const a=connected.accounts.find(x=>x.key===selectedAccount);
  $('#connected-detail').innerHTML=a?`<h3>${esc(a.broker)} ${esc(a.environment)} · ${esc(a.account_name || a.account_type || 'Account')} · …${esc(a.account_id.slice(-3))}</h3><div class="portfolio-metrics"><div><span>Broker available funds</span><h2>${esc(cashLabel(a.available_funds,a.account_currency))}</h2></div><div><span>Broker balance (not equity)</span><h2>${esc(cashLabel(a.balance,a.account_currency))}</h2></div><div><span>Indicative rand equivalent</span><h2>${esc(cashLabel(a.cash_zar,'ZAR'))}</h2></div></div><p>Account read: ${esc(when(a.retrieved_at))} · ${esc(a.state)}</p>${a.conversion?`<p class="muted">1 ${esc(a.account_currency)} = ZAR ${esc(num(a.conversion.zar_per_unit))} · ${esc(a.conversion.source)} · ${esc(a.conversion.timestamp_kind)} ${esc(when(a.conversion.as_of))}. Display-only conversion; dated rates up to four days old may be used across weekends.</p>`:''}${a.reason?`<p class="unavailable">${esc(a.reason)}</p>`:''}`:`<h3>${selectedAccount==='standard-bank'?'Standard Bank is not connected':'IG account unavailable'}</h3><p>No balance is assumed. It will contribute only after a read-only account adapter is connected and returns factual cash and currency.</p>`;
  const usable=!!a&&a.environment==='DEMO'&&a.state==='AVAILABLE'&&connected.control_access;
  $('#journal-entry').querySelectorAll('input,select,textarea,button').forEach(x=>x.disabled=!usable);
  $('#journal-status').textContent=!connected.control_access?'Unlock the journal above to record and review trades.':!a?'Select an available demo account.':a.environment!=='DEMO'?'This journal accepts demo trades only.':`Selected: ${a.broker} …${a.account_id.slice(-3)}. Planned risk and net P&L use ${a.account_currency}.`;
}
async function refreshConnected() {
  if(accountsBusy)return;accountsBusy=true;
  try {
    connected=await api('/api/portfolio/accounts');
    if(!selectedAccount)selectedAccount=connected.accounts[0]?.key || 'unavailable';
    renderConnected();await refreshJournal();
  } catch(e){$('#connected-totals').textContent='Connected balances unavailable: '+e.message;}
  finally{accountsBusy=false;}
}
async function refreshJournal() {
  const key=selectedAccount;
  $('#journal-review').textContent='';
  if(!connected?.control_access||!connected.accounts.some(a=>a.key===key))return;
  try {
    const review=await api(`/api/portfolio/accounts/${key}/trades`);
    if(key!==selectedAccount)return;
    const currency=connected.accounts.find(a=>a.key===key).account_currency;
    $('#journal-review').innerHTML=`<h4>Review: ${review.closed_count} closed · ${review.wins} profitable · net ${esc(cashLabel(review.net_pnl,currency))}</h4><p class="muted">${esc(review.scope)}</p>`+review.trades.map(t=>`<article class="journal-trade"><div class="row"><h4>${esc(t.entry.instrument)} · ${esc(t.entry.direction)} · ${esc(t.outcome)}</h4>${!t.closure?`<button data-close-trade="${esc(t.entry.trade_id)}">Record outcome</button>`:''}</div><p>${esc(num(t.entry.quantity))} at ${esc(num(t.entry.entry_price))} · entered ${esc(when(t.entry.opened_at))} · ${esc(sentence(t.entry.idea_source))}</p><p>Initial stop ${esc(t.entry.stop_price ?? 'not recorded')} · target ${esc(t.entry.target_price ?? 'not recorded')} · planned risk ${esc(cashLabel(t.entry.planned_risk,currency))}</p><p>${esc(t.entry.notes || 'No rationale recorded.')}</p>${t.closure?`<p>Exit ${esc(num(t.closure.exit_price))} · ${esc(when(t.closure.closed_at))} · net ${esc(cashLabel(t.closure.net_pnl,currency))} · ${t.r_multiple==null?'R multiple unavailable':esc(num(t.r_multiple))+' R'}</p><p>${esc(t.closure.notes)}</p>`:''}<small>Recorded ${esc(when(t.entry.recorded_at))} · self-reported${t.entry.retrospective?' · retrospective entry':''}</small></article>`).join('');
    review.trades.forEach((trade,i)=>{
      const article=$('#journal-review').querySelectorAll('.journal-trade')[i];
      article.insertAdjacentHTML('beforeend',(trade.assessment || []).map(note=>`<p class="muted">${esc(note)}</p>`).join(''));
    });
    if(review.patterns?.length)$('#journal-review').innerHTML+='<h4>Patterns in your reported outcomes — descriptive only</h4>'+paperTable(['Instrument','Idea source','Closed','Profitable','Net result'],review.patterns.map(p=>[p.instrument,sentence(p.idea_source),p.closed_count,p.wins,cashLabel(p.net_pnl,currency)]));
    if(!review.trades.length)$('#journal-review').innerHTML+=emptyPaper('No recorded trades for this account yet.');
    $('#journal-review').querySelectorAll('[data-close-trade]').forEach(button=>button.onclick=()=>{
      $('#journal-close').reset();$('#journal-close').elements.trade_id.value=button.dataset.closeTrade;
      $('#journal-close').hidden=false;$('#journal-close').scrollIntoView({behavior:'smooth',block:'center'});
    });
  }catch(e){if(key===selectedAccount)$('#journal-status').textContent=e.message;}
}
function journalPayload(form,numeric,time) {
  const body=Object.fromEntries(new FormData(form));
  numeric.forEach(k=>body[k]=body[k]===''?null:Number(body[k]));
  body[time]=new Date(body[time]).toISOString();
  return body;
}
$('#journal-entry').onsubmit=async e=>{
  e.preventDefault();const button=e.target.querySelector('button[type=submit]');button.disabled=true;
  try{
    const body=journalPayload(e.target,['quantity','entry_price','stop_price','target_price','planned_risk'],'opened_at');body.trade_id=entryId;
    await post(`/api/portfolio/accounts/${selectedAccount}/trades`,body);
    entryId=crypto.randomUUID();e.target.reset();$('#journal-status').textContent='Trade recorded. No order was submitted; broker cash was not changed.';await refreshJournal();
  }catch(error){$('#journal-status').textContent=error.message;}
  finally{button.disabled=false;}
};
$('#journal-close').onsubmit=async e=>{
  e.preventDefault();const button=e.target.querySelector('button[type=submit]');button.disabled=true;
  try{
    const body=journalPayload(e.target,['exit_price','net_pnl'],'closed_at');const id=body.trade_id;delete body.trade_id;
    await post(`/api/portfolio/accounts/${selectedAccount}/trades/${id}/close`,body);
    e.target.hidden=true;$('#journal-status').textContent='Outcome saved for later review. No broker order was submitted.';await refreshJournal();
  }catch(error){$('#journal-status').textContent=error.message;}
  finally{button.disabled=false;}
};
$('#cancel-journal-close').onclick=()=>$('#journal-close').hidden=true;
$('#refresh-connected').onclick=refreshConnected;
window.addEventListener('portfolio-auth-changed',refreshConnected);
refreshConnected();
setInterval(()=>{if(!document.hidden)refreshConnected();},60000);
