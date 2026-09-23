const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('static/js/dashboard.js','utf8');
const nodes={};
const context=vm.createContext({document:{querySelector:s=>nodes[s]??=( {textContent:'',innerHTML:''})}});
vm.runInContext(source.slice(0,source.indexOf('document.querySelectorAll(\'nav button\')')),context);
test('neutral RSI is not reported as second directional confirmation',()=>{
  const item={direction:'SHORT',input_evidence:{technical:{momentum_20d_signal:-1,rsi_14_signal:0},regime:{trend_state:'range',volatility_state:'normal'}},provenance:{last_usable_session:'2026-09-22'},evaluated_at:'2026-09-23T12:00:00Z',opportunity_id:'snapshot-1'};
  context.item=item;
  const summary=vm.runInContext('directionEvidence(item)',context);
  assert.match(summary,/1 directional technical indicator; 1 neutral/);
  vm.runInContext("renderAutomaticTechnicalScreen(item,{name:'Absa',display_symbol:'ABG'})",context);
  const html=nodes['#canonical-technical-screen'].innerHTML;
  for(const value of ['snapshot-1','2026-09-22','range','normal','SHORT']) assert.ok(html.includes(value));
  assert.ok(!html.includes('HIGH_AGREEMENT'));
});
