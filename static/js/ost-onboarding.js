/* Local export controls contain no broker credentials or browser-session access. */
(() => {
  const panel=document.querySelector('#ost-onboarding');
  if(!panel) return;
  const esc=x=>String(x ?? '—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let status, files=[];
  const output=panel.querySelector('#ost-result');
  async function load() {
    try {
      const response=await fetch('/api/v1/ost/onboarding',{cache:'no-store',signal:AbortSignal.timeout(15000)});
      if(!response.ok) throw Error('Coverage unavailable');
      status=await response.json();
      panel.querySelector('#ost-summary').textContent=status.primary_active
        ? 'Primary JSE research source: Standard Bank OST. Missing or expired exports remain unavailable; no Yahoo fallback.'
        : 'Standard Bank is the preferred source. Import your first verified export to activate the primary research feed.';
      panel.querySelector('#ost-coverage').innerHTML=`<div class="table-scroll"><table><caption>Stock and sector onboarding coverage</caption><thead><tr><th>Instrument / sector</th><th>Coverage</th><th>Completed session / bars</th><th>Missing opens / HLC errors</th><th>Export</th></tr></thead><tbody>${status.instruments.map(r=>`<tr><td>${esc(r.ost_code)} · ${esc(r.name)}<br>${esc(r.sector)}</td><td>${esc(r.state)}</td><td>${esc(r.last_session)} / ${r.bars}</td><td>${r.missing_open_bars} / ${r.invalid_hlc_bars}</td><td><a href="${esc(r.history_url)}" target="_blank" rel="noopener">OST history</a></td></tr>`).join('')}</tbody></table></div><p>Gold and USD/ZAR: source and product contracts still required; public reference charts are separate.</p>`;
      panel.querySelector('#ost-import-controls').hidden=!status.local_import_available;
      panel.querySelector('#ost-local-note').textContent=status.local_import_available
        ? 'Sign in directly to OST, export price history, then select the CSV files below. Imports are stored locally; the existing scheduled upload transfers the bounded research dataset.'
        : 'Imports are available in the local dashboard. This view displays coverage only.';
    } catch(error) {panel.querySelector('#ost-summary').textContent='OST coverage unavailable. No source readiness assumed.';}
  }
  panel.querySelector('#ost-files').addEventListener('change',event=>{
    files=Array.from(event.target.files || []);
    const options=(selected)=>status.instruments.map(r=>`<option value="${esc(r.instrument_id)}" ${r.ost_code===selected?'selected':''}>${esc(r.ost_code)} · ${esc(r.name)}</option>`).join('');
    panel.querySelector('#ost-file-mappings').innerHTML=files.map((file,index)=>{
      const match=status.instruments.find(r=>file.name.replace(/\.csv$/i,'').toUpperCase()===r.ost_code);
      return `<label>${esc(file.name)} — instrument <select data-ost-file="${index}" required><option value="">Choose the exact instrument</option>${options(match?.ost_code)}</select></label>`;
    }).join('');
  });
  panel.querySelector('#ost-import-form').addEventListener('submit',async event=>{
    event.preventDefault();
    const button=panel.querySelector('#ost-import');button.disabled=true;
    try {
      if(!files.length || files.length>34 || files.reduce((n,f)=>n+f.size,0)>1800000) throw Error('Select 1–34 CSV files, at most 1.8 MB in total.');
      const stamp=panel.querySelector('#ost-captured').value;
      if(!stamp) throw Error('Enter the actual export capture time.');
      // Explicit SAST offset; do not interpret the date in the browser timezone.
      const acquired_at=new Date(stamp+'+02:00').toISOString();
      const exports=[];
      for(let i=0;i<files.length;i++) {
        const instrument_id=panel.querySelector(`[data-ost-file="${i}"]`).value;
        if(!instrument_id) throw Error('Choose the exact instrument for every file.');
        exports.push({instrument_id,acquired_at,csv:await files[i].text()});
      }
      output.textContent='Validating the complete batch…';
      const response=await fetch('/api/v1/ost/import',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({exports,instrument_confirmed:panel.querySelector('#ost-confirm').checked}),signal:AbortSignal.timeout(30000)});
      const result=await response.json();
      if(!response.ok) throw Error(result.error || 'Import failed');
      output.textContent='Imported locally. Coverage is updated; cloud learning changes after the scheduled upload and worker. No model or trade was triggered.';
      await load();
    } catch(error) {output.textContent=error.message;}
    finally {button.disabled=false;}
  });
  panel.querySelector('#ost-refresh').addEventListener('click',load);
  load();
})();
