/* Read-only frozen reports. Refresh performs no replay or provider calls. */
(() => {
  const target=document.querySelector('#local-backtest-summary');
  if (!target) return;
  const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let version=0;
  async function load() {
    const current=++version;
    target.textContent='Reading saved research evidence…';
    try {
      const response=await fetch('/api/v1/local-backtest/research-summary',{signal:AbortSignal.timeout(10000),cache:'no-store'});
      const result=await response.json();
      if (current!==version) return;
      if (!response.ok || result.state!=='AVAILABLE') {
        target.textContent=result.state==='NOT_CONFIGURED' ? 'Local research reports have not been connected on this installation.' : 'Saved research evidence is unavailable or failed its integrity check.';
        return;
      }
      const r=result.report,c=r.counters;
      target.innerHTML=`<p><strong>B5 partially closed · software verified, market-data acceptance pending</strong></p>
        <p>Saved evidence: ${esc(r.evidence_date)} · Sasol JSE cash share · ${esc(r.window[0])} to ${esc(r.window[1])}</p>
        <p>${esc(c.safe_tests)} software tests and ${esc(c.protected_checks)} protected checks passed. ${esc(c.conditional_cases)} conditional accounting scenarios; ${esc(c.fee_checks)} directional fee checks.</p>
        <table><caption>Observed source comparison</caption><thead><tr><th>Comparison</th><th>Result</th></tr></thead><tbody>
        <tr><td>Iress intraday OHLC versus daily prices</td><td>${esc(c.price_match_days)} / ${esc(c.daily_sessions)} dates match</td></tr>
        <tr><td>Iress intraday volume versus daily totals</td><td>${esc(c.volume_match_days)} / ${esc(c.daily_sessions)} dates match</td></tr>
        <tr><td>Captured Iress intraday bars</td><td>${esc(c.intraday_bars)}</td></tr>
        <tr><td>Cost and daily-capacity sensitivities</td><td>${esc(c.stress_cases)} cases</td></tr></tbody></table>
        <p><strong>0 admitted real-data trades.</strong> Conditional calculations are not a validated trading result.</p>
        <details><summary>Remaining data gates</summary><ul><li>RAW-price and complete corporate-action coverage</li><li>Intraday volume eligibility and bar timing</li><li>Independent engine trade/cash audit after data admission</li></ul><p>IG history availability must be checked separately in this installation. Integration does not establish data entitlement.</p></details>`;
    } catch (_) {
      if (current===version) target.textContent='Saved research evidence could not be read.';
    }
  }
  document.querySelector('#refresh-local-backtest')?.addEventListener('click',load);
  load();
})();
