import unittest
from pathlib import Path
from app import app

ROOT=Path(__file__).parent

class TopFiveGuiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.html=(ROOT/'templates/dashboard.html').read_text(encoding='utf-8');cls.js=(ROOT/'static/js/dashboard.js').read_text(encoding='utf-8');cls.css=(ROOT/'static/css/dashboard.css').read_text(encoding='utf-8')
  cls.panel=cls.html.split('<section id="canonical-opportunities"',1)[1].split('</section>',1)[0]
 def test_page_and_accessible_canonical_tab_load(self):
  app.config['TESTING']=True;response=app.test_client().get('/');self.assertEqual(response.status_code,200);self.assertIn(b'Canonical Top 5',response.data);self.assertIn('aria-live="polite"',self.panel);self.assertIn('aria-label=',self.panel)
 def test_fetches_canonical_top_five_and_manual_refresh(self):
  self.assertIn("canonicalFetch('/api/v1/opportunities?limit=5')",self.js);self.assertIn("action('#refresh-canonical'",self.js)
 def test_score_is_not_probability(self):
  self.assertIn('Comparative research score</small>',self.js);self.assertIn('Comparative research score — not probability of profit.',self.panel);self.assertNotIn("ranking_score *",self.js);self.assertNotIn("ranking_score/",self.js)
 def test_all_direction_states_are_rendered_from_api_without_translation(self):
  self.assertIn("kv('Research direction',item.direction)",self.js)
  for state in ('LONG','SHORT','WATCH','UNKNOWN'):self.assertNotIn(f"item.direction==='{state}'",self.js)
 def test_research_only_cards_show_provenance_without_requesting_trade_state(self):
  self.assertIn("card.dataset.researchOnly === 'true'",self.js)
  self.assertIn('The Portfolio workspace shows any separate paper policy, risk decision and fill',self.js)
  self.assertIn('Research provenance and trading boundary',self.js)
 def test_blockers_unresolved_stop_and_null_size_are_visible(self):
  self.assertIn('item.blockers',self.js);self.assertIn("policy?.stop?.status",self.js);self.assertIn("'Unresolved'",self.js);self.assertIn("'Not available'",self.js)
 def test_empty_and_error_states_do_not_substitute_legacy(self):
  self.assertIn('No canonical opportunities available yet.',self.js);self.assertIn('Legacy recommendations are not substituted.',self.js);self.assertIn('Unable to load canonical opportunities.',self.js)
 def test_policy_risk_and_readiness_are_backend_values(self):
  for text in ('TradePolicy','Risk status','Approved size','Intent readiness','execution_readiness'):self.assertIn(text,self.js)
  self.assertNotIn('calculateRanking',self.js);self.assertNotIn('calculateRisk',self.js);self.assertNotIn('calculateReadiness',self.js)
 def test_no_canonical_execution_controls_or_secrets(self):
  upper=self.panel.upper()
  for phrase in ('TAKE TRADE','PLACE ORDER','AUTO TRADE','IG_API_KEY','X-SECURITY-TOKEN','PASSWORD'):self.assertNotIn(phrase,upper)
  self.assertNotIn('submit_order',self.js);self.assertNotIn('dealReference',self.js)
 def test_legacy_dashboard_sections_remain(self):
  for identifier in ('market-ai','technical-view','portfolio','system'):self.assertIn(f'id="{identifier}"',self.html)

if __name__=='__main__':unittest.main()
