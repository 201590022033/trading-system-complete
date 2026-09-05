"""Opt-in real-provider browser smoke test; not part of offline test discovery.

Start `.venv/bin/python app.py`, install Playwright/Chromium separately, then run
this script. It loads the public feeds and configured AI service through the app.
Screenshots are written to /tmp. Requires reachable Yahoo and Moneyweb providers.
"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:5000/')
    page.wait_for_selector('#stock-chart svg',timeout=50000)
    page.wait_for_selector('#index-chart svg',timeout=50000)
    page.wait_for_selector('.headline',timeout=50000)
    page.locator('#auto-refresh').uncheck()
    print('Charts:',page.locator('.chart-panel svg').count())
    print('Quotes:',page.locator('.quote').count())
    print('Headlines:',page.locator('.headline').count())
    print('News status:',page.locator('#news-status').inner_text())
    page.screenshot(path='/tmp/oi3-desktop.png',full_page=True)
    page.locator('#quote-SOL').click()
    page.wait_for_function("document.querySelector('#stock-chart').textContent.includes('SOL.JO')",timeout=40000)
    page.locator('#chart-period').select_option('1mo')
    page.wait_for_function("document.querySelector('#stock-chart svg') !== null",timeout=40000)
    print('Instrument and range switching: passed')
    page.locator('#run').click()
    page.wait_for_function("document.querySelector('#notice').textContent.startsWith('Run ')")
    assert page.locator('.gate').count()==30
    page.locator('nav button[data-tab=scanner]').click()
    page.locator('#scan').click()
    page.wait_for_selector('#scan-result tbody tr',timeout=10000)
    assert page.locator('#scan-result tr').count()==7
    print('Analysis and scanner: passed')
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path='/tmp/oi3-mobile.png',full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
    print('Mobile width: passed')
    assert not errors,errors
    print('Browser errors:',errors)
    browser.close()
