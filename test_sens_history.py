"""Offline source, attribution, clocks, duplicate and budget contracts."""
from dataclasses import replace
from datetime import datetime, date, timezone
import json
import unittest
from unittest.mock import Mock

from application.opportunities.sens_history import (Issuer, HistoricalSENSFetcher, parse_search,
                                                   parse_announcement, source_url)
from domain.backtest.events import events_available_as_of, group_announcements, align_observed_price_context

ISSUER = Issuer('SASOL', 'SASOL LIMITED', 'SOL', 'ZAE000006896')
NOW = datetime(2026, 10, 5, 15, tzinfo=timezone.utc)
SD = 'https://www.sharedata.co.za/v2/Scripts/SENS.aspx?id=1'
SN = 'https://www.sharenet.co.za/v3/sens_display.php?seq=1&tdate=20260909174500'
MW = 'https://www.moneyweb.co.za/mny_sens/sasol-test/'
BODY = 'Director Dealings\nSasol Limited\nJSE: SOL NYSE: SSL\nZAE000006896 US8038663006\nTransaction date: 3 September 2026\nDate: 09/09/2026 05:45:00\nProduced by the JSE SENS Department.'


def document(source='sharedata_sens', body=BODY, title='SASOL LIMITED - Director Dealings'):
    if source == 'sharedata_sens':
        return '<table><tr><td>Wed 9 Sep 2026, 17:45</td><td>'+title+'</td></tr></table><pre>'+body+'</pre>'
    if source == 'sharenet_sens':
        return '<title>SOL SOLBE1 - '+title+' - 09/09/2026</title>Release Date: 09/09/2026 17:45<pre>'+body+'</pre>'
    return '<h1 id="sens-title">'+title+'</h1><h4>9 September 2026, 17:45</h4><pre>'+body+'</pre>'


class SENSHistoryTests(unittest.TestCase):
    def test_header_clock_not_transaction_date_or_ambiguous_footer(self):
        for source, url in (('sharedata_sens', SD), ('sharenet_sens', SN), ('moneyweb_sens', MW)):
            item = parse_announcement(source, document(source), url, ISSUER, NOW)
            self.assertEqual(item.published_at, '2026-09-09T15:45:00+00:00')
            self.assertEqual(item.metadata['raw_footer_timestamp'], '09/09/2026 05:45:00')
            self.assertEqual(item.metadata['available_at'], NOW.isoformat())
            self.assertEqual(item.tickers, ['SOL'])
            self.assertEqual(item.metadata['identity_state'], 'CASH_CODE_AND_ISIN_IN_BODY')
            self.assertEqual(item.score, 0)

    def test_real_receipt_blocks_retrospective_feature_leak(self):
        item = parse_announcement('sharedata_sens', document(), SD, ISSUER, NOW)
        self.assertEqual(events_available_as_of([item], datetime(2026, 9, 10, tzinfo=timezone.utc)), ())
        self.assertEqual(events_available_as_of([item], NOW), (item,))
        self.assertEqual(events_available_as_of([replace(item, published_at=None)], NOW), ())
        bad = replace(item, ingested_at='2026-09-01T00:00:00+00:00')
        self.assertEqual(events_available_as_of([bad], NOW), ())
        with self.assertRaises(ValueError): events_available_as_of([item], datetime(2026, 10, 5))

    def test_same_disclosure_is_one_origin_and_revisions_are_preserved(self):
        items = [parse_announcement(s, document(s), u, ISSUER, NOW) for s, u in
                 (('sharedata_sens', SD), ('sharenet_sens', SN), ('moneyweb_sens', MW))]
        groups = group_announcements(items)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['independent_origin_count'], 1)
        self.assertEqual(len(groups[0]['evidence_ids']), 3)
        changed = parse_announcement('sharedata_sens', document(body=BODY.replace('3 September', '4 September')), SD, ISSUER, NOW)
        self.assertNotEqual(items[0].evidence_id, changed.evidence_id)
        self.assertEqual(len(group_announcements(items+[changed])[0]['content_versions']), 2)

    def test_correction_stays_separate_and_does_not_rewrite_original(self):
        original = parse_announcement('sharedata_sens', document(), SD, ISSUER, NOW)
        correction = parse_announcement('sharedata_sens', document(title='SASOL LIMITED - Correction: Director Dealings'), SD, ISSUER, NOW)
        self.assertEqual(len(group_announcements([original, correction])), 2)
        self.assertFalse(correction.metadata['automatic_corporate_action'])

    def test_other_issuers_adr_bee_and_missing_isin_are_not_cash_identity(self):
        with self.assertRaises(ValueError):
            parse_announcement('sharedata_sens', document(title='SASOL FINANCING LIMITED - Debt payment'), SD, ISSUER, NOW)
        for body in (BODY.replace('JSE: SOL', 'JSE: SOLBE1'), BODY.replace('ZAE000006896', ''), 'NYSE: SSL US8038663006'):
            item = parse_announcement('sharedata_sens', document(body=body), SD, ISSUER, NOW)
            self.assertEqual(item.metadata['identity_state'], 'HEADLINE_ONLY_UNVERIFIED')
            self.assertEqual(events_available_as_of([item], NOW), ())

    def test_paywall_or_hidden_body_never_supplies_text(self):
        gated = document('moneyweb_sens')+'<h3>This Sens announcement is available to subscribers</h3>'
        item = parse_announcement('moneyweb_sens', gated, MW, ISSUER, NOW)
        self.assertEqual(item.metadata['body_state'], 'BODY_UNAVAILABLE_OR_SUBSCRIBER_GATED')
        self.assertIsNone(item.metadata['content_sha256'])
        hidden = document().replace('<pre>', '<pre style="display: none">')
        item = parse_announcement('sharedata_sens', hidden, SD, ISSUER, NOW,
                                  lead={'title':'SASOL LIMITED - Director Dealings'})
        self.assertEqual(item.metadata['identity_state'], 'HEADLINE_ONLY_UNVERIFIED')

    def test_search_filters_exact_company_and_preserves_ambiguous_machine_clock(self):
        raw = '<div class="sens-row"><time datetime="2026-09-09T17:45:00+00:00">09.09.26, 17:45</time><a href="/mny_sens/one/">SASOL LIMITED – Director Dealings</a></div>'
        raw += '<div class="sens-row"><a href="/mny_sens/two/">SASOL FINANCING LIMITED – Interest</a></div>'
        leads = parse_search('moneyweb_sens', raw, MW, ISSUER)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['published_at'].isoformat(), '2026-09-09T15:45:00+00:00')
        self.assertEqual(leads[0]['raw_machine_timestamp'], '2026-09-09T17:45:00+00:00')
        raw = json.dumps(["<table><tr><td onclick='ViewSENSWithHighlight(9);return false;'>SASOL LIMITED - Director Dealings</td></tr><tr><td>9 Sep 2026, 17:45</td></tr></table>", '1 Sep 2026', '2 Oct 2026'])
        self.assertEqual(parse_search('sharedata_sens', raw, SD, ISSUER)[0]['source_item_id'], '9')
        with self.assertRaises(ValueError): parse_search('sharedata_sens', '{}', SD, ISSUER)

    def test_known_hosts_and_public_parameters_only(self):
        for url in ('http://www.sharedata.co.za/x', 'https://www.sharedata.co.za.evil/x',
                    'https://user:password@www.sharedata.co.za/x', SD+'&token=secret'):
            with self.assertRaises(ValueError): source_url('sharedata_sens', url)

    def test_legacy_archive_link_upgrades_only_known_host(self):
        raw = '<a href="http://www.sharenet.co.za/v3/sens_display.php?seq=50&tdate=20260909174500">SASOL LIMITED - Director Dealings</a>'
        self.assertTrue(parse_search('sharenet_sens', raw, SN, ISSUER)[0]['url'].startswith('https://'))
        with self.assertRaises(ValueError):
            parse_search('sharenet_sens', raw.replace('www.sharenet.co.za', 'evil.test'), SN, ISSUER)

    def test_request_caps_oversize_and_access_blocks_without_retries(self):
        session = Mock()
        response = Mock(status_code=403)
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        session.get.return_value = response
        fetcher = HistoricalSENSFetcher(max_requests=1, session=session)
        self.assertIsNone(fetcher.read('moneyweb_sens', MW))
        self.assertIsNone(fetcher.read('moneyweb_sens', MW))
        self.assertEqual(session.get.call_count, 1)
        self.assertFalse(session.get.call_args.kwargs['allow_redirects'])
        for cap in (0, 17, True, 1.5):
            with self.assertRaises(ValueError): HistoricalSENSFetcher(max_requests=cap)
        response.status_code = 200; response.iter_content.return_value = [b'x' * (SENS_MAX+1)]
        fetcher = HistoricalSENSFetcher(max_requests=1, session=session)
        self.assertIsNone(fetcher.read('sharedata_sens', SD))
        self.assertEqual(fetcher.last_status, 'RESPONSE_TOO_LARGE')

    def test_observed_slot_alignment_is_posthoc_and_does_not_backdate(self):
        item = parse_announcement('sharedata_sens', document(), SD, ISSUER, NOW)
        daily = {'bars':[{'timestamp':'2026-09-09T00:00:00+02:00'}]}
        intraday = {'bars':[{'timestamp':'2026-09-09T16:30:00+02:00'}, {'timestamp':'2026-09-10T09:00:00+02:00'}]}
        row = align_observed_price_context([item], daily, intraday)[0]
        self.assertEqual(row['observed_daily_date'], '2026-09-09')
        self.assertEqual(row['first_observed_slot_start_at_or_after_release'], '2026-09-10T09:00:00+02:00')
        self.assertEqual(row['historical_eligible_evidence_count'], 0)


SENS_MAX = HistoricalSENSFetcher.MAX_RESPONSE_BYTES
if __name__ == '__main__': unittest.main()
