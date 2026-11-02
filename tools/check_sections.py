"""Exercise Sections in a fresh browser profile against an isolated static server."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def translate_path(self, path):
        from urllib.parse import urlsplit
        name=urlsplit(path).path
        if name in ['/static/font-size.js','/static/font-size.css']:
            return str(ROOT/'sales-ops'/name.lstrip('/'))
        return super().translate_path(path)

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width':1880,'height':960}, accept_downloads=True)
            page = context.new_page();errors=[]
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/#/section')
            table = page.get_by_role('table', name='Sections', exact=True)
            assert table.locator('tbody tr').count()==5
            assert table.locator('thead th').all_text_contents()==['ID⇅','Status⇅','Name⇅','Routes','Order↑','Action']
            assert page.locator('.section-order').evaluate_all('nodes=>nodes.map(n=>n.value)')==['0','1','2','3','4']
            assert page.get_by_label('Sections All count',exact=True).inner_text()=='5'
            assert page.get_by_label('Sections Active count',exact=True).inner_text()=='5'
            assert page.get_by_label('Sections Inactive count',exact=True).inner_text()=='0'
            assert page.get_by_label('Sections Active count',exact=True).evaluate('el=>getComputedStyle(el).color')=='rgb(0, 140, 54)'
            assert page.get_by_label('Sections Inactive count',exact=True).evaluate('el=>getComputedStyle(el).color')=='rgb(200, 40, 57)'
            output=ROOT/'verification';output.mkdir(exist_ok=True)
            page.locator('#main').screenshot(path=str(output/'sections-desktop.png'))
            baseline=page.evaluate('JSON.stringify(db.section)')
            other=page.evaluate('JSON.stringify(Object.fromEntries(Object.entries(db).filter(([k])=>k!=="section")))')
            search=page.get_by_role('searchbox',name='Search sections')
            search.fill('Hospital');assert table.locator('tbody tr').count()==1
            search.fill('');table.get_by_role('button',name='Name').click()
            assert table.locator('tbody tr td:nth-child(3)').all_text_contents()==['All','Blogs','Hospital Sales Team','Order Management','Vendor Sales Team']
            page.get_by_role('button',name='Columns',exact=True).click()
            page.get_by_role('checkbox',name='Routes',exact=True).uncheck()
            assert 'Routes' not in table.locator('thead').inner_text()
            page.get_by_role('checkbox',name='Routes',exact=True).check()
            page.get_by_role('button',name='Done',exact=True).click()
            page.get_by_label('Status for Blogs',exact=True).select_option('Inactive')
            assert page.get_by_label('Sections Active count',exact=True).inner_text()=='4'
            assert page.get_by_label('Sections Inactive count',exact=True).inner_text()=='1'
            page.get_by_label('Order for Blogs',exact=True).fill('0')
            page.get_by_label('Order for Blogs',exact=True).press('Tab')
            page.reload();assert page.get_by_label('Status for Blogs',exact=True).input_value()=='Inactive'
            assert page.get_by_label('Order for Blogs',exact=True).input_value()=='0'
            page.get_by_role('button',name='Add Section',exact=True).click()
            page.locator('#record-form [name=name]').fill('Test Section')
            page.locator('#record-form [name=routes]').fill('bad-route')
            page.locator('#record-form [name=order]').fill('5')
            page.locator('#record-form').get_by_role('button',name='Add Section',exact=True).click()
            assert 'Routes must start' in page.locator('#form-error').inner_text()
            page.locator('#record-form [name=routes]').fill('/test-section')
            page.locator('#record-form').get_by_role('button',name='Add Section',exact=True).click()
            assert page.locator('#modal').evaluate('el=>!el.open')
            assert table.locator('tbody tr').count()==6
            page.get_by_role('button',name='Actions for Test Section',exact=True).click()
            page.get_by_role('button',name='Edit Section',exact=True).click()
            page.locator('#record-form [name=name]').fill('Updated Test Section')
            page.get_by_role('button',name='Save Changes',exact=True).click()
            assert 'Updated Test Section' in table.inner_text()
            page.locator('.section-actions summary').click()
            with page.expect_download() as download:
                page.get_by_role('button',name='Export Excel',exact=True).click()
            assert download.value.suggested_filename.endswith('.xlsx')
            page.get_by_role('button',name='Actions for Updated Test Section',exact=True).click()
            page.get_by_role('button',name='Delete Section',exact=True).click()
            page.get_by_role('button',name='Delete local record',exact=True).click()
            assert table.locator('tbody tr').count()==5
            # Synthetic extra records prove pagination rather than only testing disabled buttons.
            page.evaluate("()=>{db.section.push(...Array.from({length:7},(_,i)=>({id:20+i,name:'Pagination test '+i,status:'Active',routes:'/test-'+i,order:10+i})));commitSections(db.section);renderMain()}")
            assert table.locator('tbody tr').count()==10
            page.get_by_role('button',name='Next',exact=True).click()
            assert table.locator('tbody tr').count()==2
            page.get_by_role('button',name='Previous',exact=True).click()
            page.get_by_label('Sections per page').select_option('25')
            assert table.locator('tbody tr').count()==12
            search.fill('NO MATCH');assert 'No sections found.' in table.inner_text()
            search.fill('')
            page.evaluate('value=>{db.section=JSON.parse(value);save();state.page=1;renderMain()}',baseline)
            assert page.evaluate('JSON.stringify(Object.fromEntries(Object.entries(db).filter(([k])=>k!=="section")))')==other
            # Simulate browser-storage failure: no false success or lost status.
            page.evaluate("()=>{window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw Error('Synthetic quota error')}}")
            page.get_by_label('Status for All',exact=True).select_option('Inactive')
            assert page.get_by_label('Status for All',exact=True).input_value()=='Active'
            assert page.evaluate('JSON.stringify(db.section)')==baseline
            page.evaluate('()=>{Storage.prototype.setItem=window.originalSetItem;}')
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.locator('#main').screenshot(path=str(output/'sections-mobile.png'))
            assert not errors,errors
            context.close();browser.close()
            print('PASS: reference records/layout, search, sort, columns, status/order persistence, validated add/edit/delete, export, pagination, empty state, quota rollback, mobile, other records unchanged.')
    finally:
        server.shutdown();server.server_close()

if __name__=='__main__':main()
