/* Aggregate research progress only. Refresh never starts a worker or a model. */
(() => {
  const target=document.querySelector('#daily-learning-overview');
  if(!target) return;
  const esc=x=>String(x ?? 'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const value=x=>x==null?'Unavailable':x;
  let version=0;
  async function load() {
    const request=++version;
    target.textContent='Reading persisted daily learning evidence…';
    try {
      const response=await fetch('/api/v1/learning/overview',{cache:'no-store',signal:AbortSignal.timeout(20000)});
      if(!response.ok) throw Error('Learning source unavailable');
      const d=await response.json();
      if(d.schema!=='daily-learning-overview-v1' || d.state!=='AVAILABLE') throw Error('Learning source unavailable');
      if(request!==version) return;
      const ai=d.ai_comparison || {}, s=d.sasol || {}, quality=d.latest_feature_quality || {}, inputs=d.research_inputs || {};
      target.innerHTML=`<p><strong>Learning records: ${esc(d.runtime)} · ${esc(d.database)}</strong></p>
        <p>Worker: ${esc(d.worker?.status)} · last heartbeat ${esc(d.worker?.last_heartbeat_at)} · next scheduled ${esc(d.worker?.next_scheduled_at)}</p>
        <p>Upload: ${esc(d.source_observed_at)} · ${esc(d.data_state)}. Latest decision: ${esc(d.decision_at)}.</p>
        <p><strong>Integrated supplemental research inputs: ${esc(inputs.state)}</strong></p>
        ${['SASOL','ETF_STX40'].filter(k=>inputs.charts?.[k]).map(k=>`<p>${esc(k)}: ${esc(inputs.charts[k].provider)} · completed price session ${esc(inputs.charts[k].last_session)} · acquired ${esc(inputs.charts[k].acquired_at)} · ${esc(inputs.charts[k].bars)} bars.</p>`).join('')}
        ${inputs.sasol?.state ? `<p>Current Sasol input preview: ${esc(inputs.sasol.state)} · ${esc(inputs.sasol.session)}. Missing: ${esc((inputs.sasol.missing || []).join(', ') || 'No missing numerical inputs')}.</p>` : ''}
        <p class="muted">Input preview is separate from the last frozen worker decision below. Supplemental feeds are prospective shadow research; adjustment/actions, volume and historical availability remain unverified. They are excluded from historical AI evaluation and B5 admission.</p>
        <p>Frozen Swing ${esc(d.feature_strategy?.version)} decisions in read window: ${esc(value(d.decisions_in_read_window))}.</p>
        <table><caption>Prospective observed-session forward outcomes</caption><thead><tr><th>Horizon</th><th>Matured</th><th>Pending</th><th>Negative after assumed costs</th></tr></thead><tbody>${['3','4','5'].map(h=>`<tr><td>${h} sessions</td><td>${esc(value(d.horizons?.[h]?.matured))}</td><td>${esc(value(d.horizons?.[h]?.pending))}</td><td>${esc(value(d.horizons?.[h]?.negative))}</td></tr>`).join('')}</tbody></table>
        <p class="muted">Entry is the first observable close after the frozen decision, followed by 3/4/5 later observed sessions. These are forward returns, not stop/target fills. Costs assume 10 bps; they are not verified OST fees.</p>
        <p>Latest feature coverage: ${esc(quality.available)} complete · ${esc(quality.partial)} partial · ${esc(quality.unavailable)} unavailable.</p>
        <p>Sasol: ${esc(s.state)} · price session ${esc(s.session)} · invalid OHLC days ${esc(value(s.invalid_ohlc_days))}. Missing: ${esc((s.missing || []).join(', ') || 'No reported missing fields')}.</p>
        <p>Selected versus other-share controls: ${esc(value(d.selected_vs_other?.decisions))} decisions · ${esc(value(d.selected_vs_other?.outcomes))} outcomes · ${esc(value(d.selected_vs_other?.independent_sessions))} independent paired sessions.</p>
        <p>AI hypothesis: ${esc(ai.state)} · ${esc(ai.provider)} · ${esc(ai.validation)}. Baseline holdout ${esc(value(ai.baseline_holdout_samples))} samples; candidate ${esc(value(ai.candidate_holdout_samples))}. Blocked/unresolved checks: ${esc(value(ai.baseline_blocked))} baseline / ${esc(value(ai.candidate_blocked))} candidate.</p>
        <details><summary>Present / absent condition controls</summary>${['3','4','5'].map(h=>`<h4>${h} sessions</h4>${d.condition_cohorts?.[h]?.length ? `<ul>${d.condition_cohorts[h].map(r=>`<li>${esc(r.condition)}: ${esc(r.samples)} observations; ${esc(r.negative)} negative</li>`).join('')}</ul>` : '<p>No matured condition cohorts yet.</p>'}`).join('')}</details>
        <p class="muted">${esc(d.limitations)}</p><p><strong>No automatic strategy promotion. B5 real-data acceptance remains pending.</strong></p>`;
    } catch(error) { if(request===version) target.textContent='Daily learning evidence is unavailable. No zero counts, cloud results or training success are assumed.'; }
  }
  document.querySelector('#refresh-daily-learning').addEventListener('click',load);
  load();
})();
