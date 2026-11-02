"""Actual robot panel and server flow, temporary database, mocked Google only."""
import os
import sys
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'sales-ops'))
from crm_test_environment import app, login_browser_admin
from flask import send_from_directory, jsonify
from playwright.sync_api import sync_playwright
from waitress import create_server
import google_ai


def main():
    original_home=app.app.view_functions['home']
    app.app.view_functions['home']=lambda:send_from_directory(ROOT,'index.html')
    app.app.add_url_rule('/operations/','robot_test_operations',original_home)
    @app.app.get('/<filename>')
    def test_assets(filename):
        if filename not in {'app.js','data.js','styles.css','sections.css','assistant.css','operations.js','operations.css','sales-report.js','excel.js'}:return '',404
        return send_from_directory(ROOT,filename)
    @app.app.get('/assets/<path:filename>')
    def test_images(filename):return send_from_directory(ROOT/'assets',filename)
    @app.app.get('/api/workspace/navigation')
    def test_navigation():return jsonify(ok=True,counts=dict.fromkeys(['clients','rghs','served','doctors','potential','leads','quotes','orders'],0))
    server=create_server(app.app,host='127.0.0.1',port=0)
    Thread(target=server.run,daemon=True).start()
    address=f'http://127.0.0.1:{server.effective_port}/'
    try:
        with patch.dict(os.environ,{'GEMINI_API_KEY':'','QUOTESAARTHI_LIVE_AI':'false'}),sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000})
            login_browser_admin(context,address)
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(address+'#/section')
            assert page.locator('#quote-robot-panel iframe').count()==0
            launcher=page.get_by_role('button',name='Open AI Assistance robot assistant',exact=True)
            launcher.click()
            frame=page.frame_locator('#quote-robot-panel iframe')
            try:
                page.wait_for_function("document.querySelector('.quote-robot-loading').hidden",timeout=10000)
            except Exception:
                print('Browser startup errors:',errors)
                for item in page.frames:
                    print('Frame:',item.url,'inert:',item.evaluate('document.body?.inert'))
                raise
            assert frame.locator('#quoteAnswerSource').input_value()=='auto'
            assert frame.locator('#quoteAnswerSource option').all_text_contents()==['Search & assistance','HOSPkart workspace','Provided Excel report','Product catalogue & quotations','Google Search']
            assert 'Gemini' not in frame.locator('#chatWidget').inner_text()
            assert 'AI Assistance' in frame.locator('.chat-head').inner_text()
            assert 'Your CRM intelligence assistant' not in frame.locator('.chat-head').inner_text()
            with patch('google_ai.requests.post') as post:
                frame.get_by_label('Message AI Assistance').fill('Show CRM summary')
                frame.get_by_role('button',name='Send',exact=True).click()
                frame.locator('.quote-reply-source').get_by_text('Saved CRM',exact=True).wait_for()
                post.assert_not_called()
            # Public Google search opens only the typed query in a separate tab.
            context.route('https://www.google.com/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<title>Google search fixture</title>'))
            frame.locator('#quoteAnswerSource').select_option('web')
            frame.get_by_label('Message AI Assistance').fill('hospital beds Jaipur & Delhi')
            with page.expect_popup() as popup:
                frame.get_by_role('button',name='Search',exact=True).click()
            popup.value.wait_for_load_state()
            from urllib.parse import urlsplit,parse_qs
            assert parse_qs(urlsplit(popup.value.url).query)['q']==['hospital beds Jaipur & Delhi']
            popup.value.close()
            frame.locator('#quoteAnswerSource').select_option('')
            assert frame.get_by_role('button',name='Upload catalogue',exact=True).is_visible()
            frame.locator('#assistantCatalogueFile').set_input_files({'name':'catalogue.csv','mimeType':'text/csv','buffer':b'product_name,vendor_name,price,stock,category,manufacturer,specs,warranty\nIV Set,Vendor A,10,100,Injection,Test maker,Luer lock,Not provided\n'})
            frame.locator('#chatBody').get_by_text('Catalogue ready:',exact=False).wait_for()
            frame.get_by_label('Message AI Assistance').fill('IV Set vendor listing')
            frame.get_by_role('button',name='Send',exact=True).click()
            child=page.locator('#quote-robot-panel iframe').element_handle().content_frame()
            child.wait_for_function('!quoteSaarthiSubmitting')
            assert 'Vendor A' in frame.locator('#chatBody').inner_text()
            assert 'INR 10.00' in frame.locator('#chatBody').inner_text()
            frame.locator('#quoteAnswerSource').select_option('workspace')
            assert 'QuoteSaarthi' not in frame.locator('body').inner_text()
            # Text grows, rather than zooming the entire layout, in parent and iframe.
            parent_size=page.get_by_role('heading',name='Sections',exact=True).evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')
            child_size=frame.locator('.chat-head strong').evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')
            page.get_by_role('button',name='Increase text size',exact=True).click()
            page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--crm-font-scale')==='1.1'")
            child=page.locator('#quote-robot-panel iframe').element_handle().content_frame()
            child.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--crm-font-scale')==='1.1'")
            assert abs(page.get_by_role('heading',name='Sections',exact=True).evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')-parent_size*1.1)<0.05
            assert abs(frame.locator('.chat-head strong').evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')-child_size*1.1)<0.05
            assert page.evaluate("localStorage.getItem('hospkart-crm-font-percent')")=='110'
            page.get_by_role('button',name='Decrease text size',exact=True).click()
            assert page.evaluate("localStorage.getItem('hospkart-crm-font-percent')")=='100'
            page.evaluate("location.hash='#/operations?module=clients'")
            frame.locator('#quoteWorkspaceFocus').get_by_text('Current view: Hospitals & Clients',exact=True).wait_for()
            assert 'Change colors or add remarks beside any hospital.' not in page.frame_locator('#operations-frame').locator('body').inner_text()
            # Navigation preserves the already-open conversation and iframe.
            page.evaluate("location.hash='#/employee'")
            page.get_by_role('heading',name='Employees',exact=True).wait_for()
            assert 'Saved CRM' in frame.locator('#chatBody').inner_text()
            frame.get_by_role('button',name='Close AI Assistance',exact=True).click()
            page.locator('#quote-robot-panel').wait_for(state='hidden')
            assert page.locator('#quote-robot-panel').is_hidden()
            assert launcher.get_attribute('aria-expanded')=='false'
            launcher.click();frame.get_by_label('Message AI Assistance').press('Escape')
            page.locator('#quote-robot-panel').wait_for(state='hidden')
            assert page.locator('#quote-robot-panel').is_hidden()
            page.get_by_role('button',name='Increase text size',exact=True).click()
            page.reload()
            page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--crm-font-scale')==='1.1'")
            page.set_viewport_size({'width':390,'height':844})
            launcher.click()
            page.wait_for_function("document.querySelector('.quote-robot-loading').hidden")
            box=page.locator('#quote-robot-panel').bounding_box()
            assert box['x']>=0 and box['x']+box['width']<=390
            assert box['y']>=0 and box['y']+box['height']<=844
            assert frame.get_by_role('button',name='Send',exact=True).is_visible()
            assert frame.locator('#chatWidget').evaluate("el=>getComputedStyle(el).flexDirection")=='column'
            assert frame.locator('#chatInput').bounding_box()['y']>frame.locator('.chat-head').bounding_box()['y']
            (ROOT/'verification').mkdir(exist_ok=True)
            page.screenshot(path=str(ROOT/'verification/robot-assistant-mobile.png'))
            assert not errors,errors
            context.close();browser.close()
            print('PASS: AI Assistance title, local workspace, no Gemini UI, text-size changes across frames, navigation persistence, close/Escape, mobile fit.')
    finally:server.close()

if __name__=='__main__':main()
