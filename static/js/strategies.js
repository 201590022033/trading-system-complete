/* Strategy discovery only. Existing canonical ranking and account controls stay separate. */
(() => {
  const root=document.querySelector('#strategy-cards'), detail=document.querySelector('#strategy-detail');
  const status=document.querySelector('#strategy-status');
  const esc=value=>String(value ?? 'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let requestVersion=0;
  async function read(url) {
    const response=await fetch(url,{signal:AbortSignal.timeout(10000)});
    if(!response.ok) throw Error(`Strategy discovery unavailable (${response.status})`);
    return response.json();
  }
  function renderDetail(profile) {
    detail.hidden=false;
    detail.innerHTML=`<h3>${esc(profile.display_name)}</h3><p>${esc(profile.lifecycle_label)} · version ${esc(profile.strategy_profile_version)}</p>
      <p class="notice">Profile foundation only. Opening a profile neither selects a trading model nor enables execution.</p>
      <p>Intended timeframe: ${esc(profile.decision_timeframe)}. Holding horizons: ${esc((profile.intended_horizon_ids || []).join(', '))} — intent, not runtime configuration.</p>
      <h4>Capabilities and remaining gates</h4><ul>${(profile.capabilities || []).map(item=>`<li><strong>${esc(item.capability_id)} · ${esc(item.state)}</strong><p>${esc(item.description)}</p></li>`).join('')}</ul>
      <h4>Limitations</h4><ul>${(profile.limitations || []).map(item=>`<li>${esc(item)}</li>`).join('')}</ul>
      <p>Research ranking → execution feasibility → account-specific sizing remain separate. A high research rank may be uneconomic for your account.</p>
      ${profile.canonical_workflow_tab === 'canonical-opportunities' ? '<button type="button" data-open-canonical>Open existing canonical screening / Top 5</button><p class="muted">This is the existing daily workflow, not a new profile-attributed ranking. Strategy attribution is still pending.</p>' : '<p class="muted">No strategy trading workflow is connected. Development placeholder only.</p>'}`;
    detail.querySelector('[data-open-canonical]')?.addEventListener('click',()=>{
      document.querySelector('nav button[data-tab="canonical-opportunities"]').click();
    });
    detail.focus();
  }
  async function openProfile(profile) {
    const version=++requestVersion;
    detail.hidden=false; detail.textContent='Reading the exact strategy profile version…';
    try {
      const result=await read(`/api/v1/strategy-profiles/${encodeURIComponent(profile.strategy_profile_id)}/versions/${encodeURIComponent(profile.strategy_profile_version)}`);
      if(result.profile?.strategy_profile_id !== profile.strategy_profile_id || result.profile?.strategy_profile_version !== profile.strategy_profile_version) throw Error('Mismatched strategy profile version');
      if(version===requestVersion) renderDetail(result.profile);
    } catch(error) { if(version===requestVersion) detail.textContent=`${error.message}. No capability has been substituted.`; }
  }
  async function load() {
    const version=++requestVersion; detail.hidden=true; root.replaceChildren(); status.textContent='Loading backend strategy profiles…';
    try {
      const result=await read('/api/v1/strategy-profiles');
      if(version!==requestVersion) return;
      if(!Array.isArray(result.profiles)) throw Error('Malformed strategy profile response');
      status.textContent=result.profiles.length ? 'Versioned research profiles · read-only discovery · live execution disabled' : 'No strategy profiles registered. No trading capability has been substituted.';
      for(const profile of result.profiles) {
        const card=document.createElement('article'); card.className='panel strategy-card';
        card.innerHTML=`<h3>${esc(profile.card_title)}</h3><p class="strategy-horizon">${esc(profile.holding_period_label)}</p><p>${esc(profile.lifecycle_label)}</p><small>${esc(profile.strategy_profile_id)} · v${esc(profile.strategy_profile_version)}</small><button type="button">Open Strategy</button>`;
        card.querySelector('button').addEventListener('click',()=>openProfile(profile)); root.appendChild(card);
      }
    } catch(error) { if(version===requestVersion) { root.replaceChildren(); status.textContent=`${error.message}. No profiles or trading claims have been substituted.`; } }
  }
  document.querySelector('#refresh-strategies').addEventListener('click',load);
  load();
})();
