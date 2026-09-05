"""Browser regression using intercepted feed fixtures; run against a local app.
Requires separately installed Playwright/Chromium. Does not contact public feed
providers: all feed requests are fulfilled inside the isolated browser page.
"""
import json
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
calls={}
fail_news=False
news={'state':'AVAILABLE','refreshing':False,'last_success':'2026-09-05T06:00:00Z','data':{'items':[{'headline':'<img src=x onerror=alert(1)>','source':'Test fixture','timestamp':'2026-09-05T06:00:00Z','summary':'Fixture only','sentiment':'bullish','score':.5,'llm_used':True,'url':'javascript:alert(1)','assets':[{'name':'SASOL','direction':1}]}],'macro':{},'sources':{'fixture':'AVAILABLE'},'analysis_method':'AI + keyword fallback'}}
def market(route):
    url=urlparse(route.request.url);key=url.path+'?'+url.query
    calls[key]=calls.get(key,0)+1
    if calls[key]==1:
        data={'state':'LOADING','refreshing':True,'data':None}
    else:
        symbol=url.path.rsplit('/',1)[-1];period=parse_qs(url.query)['period'][0]
        data={'state':'AVAILABLE','refreshing':False,'data_state':'DELAYED_PUBLIC','last_success':'2026-09-05T06:00:00Z','note':'Fixture', 'data':{'symbol':symbol+'.JO','currency':'ZAR','period':period,'interval':'1d','price':101,'source_timestamp':'2026-09-04T00:00:00Z','change_pct':1,'bars':[{'timestamp':'2026-09-03T00:00:00Z','close':100,'volume':10},{'timestamp':'2026-09-04T00:00:00Z','close':101,'volume':20}]}}
    route.fulfill(json=data)
def news_route(route):
    route.fulfill(status=503,json={'error':'Fixture provider outage'}) if fail_news else route.fulfill(json=news)
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/api/feed/market/**',market)
    page.route('**/api/feed/news',news_route)
    page.goto('http://127.0.0.1:5000/')
    page.wait_for_selector('#stock-chart svg')
    page.locator('#auto-refresh').uncheck()
    page.locator('#quote-SOL').click()
    page.wait_for_function("document.querySelector('#stock-chart').textContent.includes('SOL.JO')")
    page.locator('#chart-period').select_option('1y')
    page.wait_for_function("document.querySelector('#stock-chart svg') !== null")
    page.locator('#news-filter').select_option('selected')
    assert page.locator('.headline').count()==1
    assert page.locator('.headline img').count()==0
    assert page.locator('.headline a').count()==0
    assert 'AI analysed' in page.locator('.headline').inner_text()
    fail_news=True
    page.locator('#refresh-news').click()
    page.wait_for_function("document.querySelector('#news-status').textContent.includes('refresh failed')")
    assert page.locator('.headline').count()==1
    assert not errors,errors
    print('PASS: cold chart/range loading with refresh paused; sentiment filtering; escaped feed content; retained news on HTTP failure; no browser errors')
    browser.close()
