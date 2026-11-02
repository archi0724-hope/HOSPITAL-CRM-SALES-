"""Status workflow checks against a temporary database and fresh Chrome profile."""
import sys
from pathlib import Path
from threading import Thread
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crm_test_environment import app, login_browser_admin
from playwright.sync_api import sync_playwright
from waitress import create_server

def main():
    server = create_server(app.app, host='127.0.0.1', port=0)
    Thread(target=server.run, daemon=True).start()
    address = f'http://127.0.0.1:{server.effective_port}/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            login_browser_admin(context, address)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(address + '?view=clients&embedded=1')
            page.wait_for_function('dashboardReady && !document.body.inert')
            page.evaluate("""async()=>{
              const base={type:'New Prospect',city:'Test City',contact:'Test Person',mobile:'',email:'',requirement:'Test only',product:'',executive:'Test',quote:0,order:0,next:'',remark:'',status:'New Lead',workColor:''};
              clients=[{...base,id:'TEST-RED',name:'Untouched test'},
                {...base,id:'TEST-YELLOW',name:'Unconnected test'},
                {...base,id:'TEST-BLUE',name:'Followup test',status:'Follow-up Required',remark:'Call tomorrow'},
                {...base,id:'TEST-ORANGE',name:'Declined test',status:'Not Interested',workColor:'green'},
                {...base,id:'TEST-DUP',name:'Duplicate Test'}];
              calls=[{clientId:'TEST-YELLOW',recordScope:'clients',date:TODAY,connected:'No'}];
              sectionRecords={rghs:[],leads:[{...base,id:'TEST-DUP2',name:'duplicate-test'}],served:[],doctors:[{...base,id:'TEST-DOC',name:'Doctor outreach test'}],potential:[]};
              segmentData={served:sectionRecords.served,doctors:sectionRecords.doctors,potential:sectionRecords.potential};
              await writeDashboardValues({hk_v2_clients:clients,hk_v2_calls:calls,hk_v2_segments:segmentData,...Object.fromEntries(Object.entries(sectionRecords).map(([k,v])=>['hk_v2_'+k,v]))});
              navigate('clients');
            }""")
            for record, color, background in [('RED','red','rgb(255, 246, 246)'),('YELLOW','yellow','rgb(255, 249, 196)'),('BLUE','blue','rgb(241, 246, 255)'),('ORANGE','orange','rgb(255, 244, 229)')]:
                row = page.locator(f'#clientsPageRows tr[data-work-record="TEST-{record}"]')
                assert f'work-{color}' in row.get_attribute('class')
                assert row.locator('td').first.evaluate('el=>getComputedStyle(el).backgroundColor') == background
            page.locator('#clientsPageRows tr[data-work-record="TEST-ORANGE"] select').select_option('yellow')
            page.wait_for_function("clients.find(r=>r.id==='TEST-ORANGE').workColor==='yellow' && sharedWorkspaceSaving===0")
            assert page.evaluate("clients.find(r=>r.id==='TEST-ORANGE').status")=='New Lead'
            assert 'work-yellow' in page.locator('#clientsPageRows tr[data-work-record="TEST-ORANGE"]').get_attribute('class')
            assert page.locator('.work-legend .work-tag.work-yellow').evaluate('el=>getComputedStyle(el).backgroundColor')=='rgba(0, 0, 0, 0)'
            duplicate = page.locator('#clientsPageRows tr[data-work-record="TEST-DUP"]')
            assert 'duplicate-record' in duplicate.get_attribute('class')
            assert duplicate.locator('.client-name').evaluate('el=>getComputedStyle(el).color') == 'rgb(185, 214, 0)'
            assert page.locator('#clientsPageRows tr[data-work-record="TEST-RED"] option').first.inner_text() == 'Automatic — based on saved work'
            # Real UI selection must save source and linked potential in one request.
            writes = []
            page.on('request', lambda r: writes.append(r.post_data_json) if r.method=='POST' and r.url.endswith('/api/workspace') else None)
            page.locator('#clientsPageRows tr[data-work-record="TEST-RED"] select').select_option('green')
            page.wait_for_function("clients.find(r=>r.id==='TEST-RED').workColor==='green' && sharedWorkspaceSaving===0 && segmentData.potential.some(r=>r.sourceRecordId==='TEST-RED')")
            assert len(writes) == 1, len(writes)
            assert {'hk_v2_clients','hk_v2_potential'}.issubset(writes[0]['values'])
            # A duplicate refresh must run on the open module, without visiting overview.
            assert 'duplicate-record' in page.locator('#clientsPageRows tr[data-work-record="TEST-RED"]').get_attribute('class')
            page.locator('#clientsPageRows tr[data-work-record="TEST-YELLOW"] select').select_option('orange')
            page.wait_for_function("clients.find(r=>r.id==='TEST-YELLOW').status==='Not Interested' && sharedWorkspaceSaving===0")
            assert 'work-orange' in page.locator('#clientsPageRows tr[data-work-record="TEST-YELLOW"]').get_attribute('class')
            # Blue requires a remark before it can be saved.
            page.evaluate("()=>{const r=clients.find(r=>r.id==='TEST-DUP');r.remark='';}")
            page.locator('#clientsPageRows tr[data-work-record="TEST-DUP"] select').select_option('blue')
            assert page.locator('#workStatusDrawer').evaluate("el=>el.classList.contains('open')")
            assert page.locator('#workRecordRemark').get_attribute('required') is not None
            page.locator('#workRecordRemark').fill('Synthetic query follow-up')
            page.locator('#workStatusDrawer').get_by_role('button',name='Save work status').click()
            page.wait_for_function("clients.find(r=>r.id==='TEST-DUP').workColor==='blue' && sharedWorkspaceSaving===0")
            page.reload()
            page.wait_for_function('dashboardReady && !document.body.inert')
            state = page.evaluate("()=>({color:workColor(clients.find(r=>r.id==='TEST-YELLOW')),copies:segmentData.potential.filter(r=>r.sourceRecordId==='TEST-RED').length,source:!!clients.find(r=>r.id==='TEST-RED')})")
            assert state == {'color':'orange','copies':1,'source':True}, state
            assert page.evaluate("workColor(clients.find(r=>r.id==='TEST-ORANGE'))")=='yellow'
            page.evaluate("async()=>{const r=clients.find(r=>r.id==='TEST-ORANGE');applyWorkColor(r,'orange');await saveWorkRecords('clients');renderAll()}")
            page.locator('#clientsPageRows tr[data-work-record="TEST-ORANGE"] select').select_option('green')
            page.wait_for_function("clients.find(r=>r.id==='TEST-ORANGE').status==='Contacted' && sharedWorkspaceSaving===0")
            assert page.evaluate("segmentData.potential.filter(r=>r.sourceRecordId==='TEST-ORANGE').length")==1
            page.evaluate("async()=>{const record=segmentData.doctors[0];record.workColor='green';await saveWorkRecords('doctors');await saveWorkRecords('doctors');}")
            assert page.evaluate("segmentData.potential.filter(r=>r.sourceRecordId==='TEST-DOC').length") == 1
            # A failed write must roll back both status and the proposed linked copy.
            page.route('**/api/workspace', lambda route: route.fulfill(status=503,content_type='application/json',body='{"ok":false,"error":"Synthetic save failure"}') if route.request.method=='POST' else route.continue_())
            page.evaluate("()=>navigate('leads')")
            page.locator('#leadBoard [data-work-id="TEST-DUP2"].work-color-select').select_option('green')
            page.wait_for_function("sharedWorkspaceSaving===0 && document.getElementById('toast').textContent.includes('not saved')")
            assert page.evaluate("!sectionRecords.leads.find(r=>r.id==='TEST-DUP2').workColor && !segmentData.potential.some(r=>r.sourceRecordId==='TEST-DUP2')")
            page.unroute('**/api/workspace')
            page.evaluate("()=>{const r=clients.find(r=>r.id==='TEST-BLUE');r.status='Contacted';recordWorkStage(r);if(workColor(r)!=='green')throw Error('Stale query flag');}")
            page.set_viewport_size({'width':390,'height':844})
            page.evaluate("()=>{navigate('clients');document.documentElement.classList.add('crm-dark')}")
            row=page.locator('#clientsPageRows tr[data-work-record="TEST-YELLOW"]')
            assert row.locator('td').first.evaluate('el=>getComputedStyle(el).backgroundColor') not in ['rgba(0, 0, 0, 0)','rgb(255, 255, 255)']
            assert row.locator('select').get_attribute('aria-label')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile page overflows'
            context.close();browser.close()
            assert not errors, errors
            print('PASS: five status colours, direct-module neon duplicates, atomic green routing, remark validation, doctor routing, reload persistence, no repeat copies.')
    finally:
        server.close()

if __name__ == '__main__':
    main()
