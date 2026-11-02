"""Integration routing, data boundaries and asset checks; never writes live records."""
import json
from html.parser import HTMLParser
import re
import unittest
from pathlib import Path
import run_local

ROOT = Path(__file__).resolve().parent

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = run_local.app.test_client()

    def test_original_frontend_is_the_home_page(self):
        self.assertEqual(self.client.get('/', buffered=True).data, (ROOT / 'index.html').read_bytes())
        self.assertIn(b'operations.js', self.client.get('/', buffered=True).data)

    def test_operations_template_and_all_local_assets_load(self):
        page = self.client.get('/operations/?view=clients')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'integration-navigation.js', page.data)
        for url in re.findall(r"""(?:src|href)=["'](/static/[^"']+)""", page.get_data(as_text=True)):
            self.assertEqual(self.client.get(url, buffered=True).status_code, 200, url)

    def test_databases_and_configuration_are_not_public_files(self):
        for url in ['/sales-ops/data/hospkart_crm.db', '/.env', '/run_local.py', '/integration-backup/hashes.json']:
            self.assertEqual(self.client.get(url, buffered=True).status_code, 404, url)

    def test_original_styles_and_seeds_are_unchanged(self):
        if not (ROOT / 'integration-backup/styles.css').is_file():
            self.skipTest('Original local inspection baseline is not included in the public repository.')
        for name in ['styles.css', 'data.js']:
            self.assertEqual((ROOT / name).read_bytes(), (ROOT / 'integration-backup' / name).read_bytes())

    def test_core_operations_read_endpoints(self):
        for url in ['/api/health', '/api/workspace?revision=-1', '/api/spreadsheet/status', '/api/drive-import', '/activity']:
            self.assertEqual(self.client.get(url, buffered=True).status_code, 200, url)

    def test_embedded_pages_share_the_crm_theme(self):
        for route in ['/operations/?view=clients&embedded=1&theme=dark', '/activity?embedded=1&theme=dark']:
            page = self.client.get(route, buffered=True)
            self.assertIn(b'crm-integrated crm-embedded crm-dark', page.data)
            self.assertIn(b'integration-theme.css', page.data)
            self.assertIn(b'integration-theme.js', page.data)
        self.assertNotIn(b'crm-embedded', self.client.get('/operations/', buffered=True).data.split(b'</head>')[0])
        self.assertEqual(self.client.get('/operations.css', buffered=True).status_code, 200)

    def test_integration_scripts_are_outside_the_main_script(self):
        class ScriptParser(HTMLParser):
            def __init__(self):
                super().__init__();self.scripts=[];self.current=None;self.parts=[]
            def handle_starttag(self, tag, attrs):
                if tag == 'script': self.current=dict(attrs);self.parts=[]
            def handle_data(self, data):
                if self.current is not None: self.parts.append(data)
            def handle_endtag(self, tag):
                if tag == 'script' and self.current is not None:
                    self.scripts.append((self.current.get('src',''),''.join(self.parts)));self.current=None
        parser=ScriptParser();parser.feed(self.client.get('/operations/?embedded=1', buffered=True).get_data(as_text=True))
        main=[body for src,body in parser.scripts if not src and 'function exportSegmentExcel' in body]
        self.assertEqual(len(main),1)
        self.assertIn('startDashboard().catch',main[0])
        self.assertNotIn('<script',main[0])
        urls=[src.split('?')[0] for src,body in parser.scripts if src]
        self.assertEqual(urls[-2:],['/static/integration-navigation.js','/static/integration-theme.js'])
        self.assertEqual(urls.count('/static/integration-navigation.js'),1)
        self.assertEqual(urls.count('/static/integration-theme.js'),1)

    def test_workspace_navigation_counts_match_saved_data(self):
        response=self.client.get('/api/workspace/navigation',buffered=True)
        self.assertEqual(response.status_code,200)
        result=response.json
        self.assertLess(len(response.data),1024)
        workspace=self.client.get('/api/workspace',buffered=True).json['workspace']
        values=workspace['values']
        for key in ['clients','rghs','served','doctors','potential','leads']:
            self.assertEqual(result['counts'][key],len(values['hk_v2_'+key]))
        records=values['hk_v2_clients']+values['hk_v2_leads']
        self.assertEqual(result['counts']['quotes'],sum(float(row.get('quote') or 0)>0 for row in records))
        won={'PO / Order Confirmed','Order Finalized','Demand Fulfilled','Delivered','Feedback Pending','Completed / Served'}
        self.assertEqual(result['counts']['orders'],sum(row.get('status') in won or float(row.get('order') or 0)>0 for row in records))
        self.assertEqual(result['revision'],workspace['revision'])

    def test_original_report_import_is_available_without_changing_workspace(self):
        if not (ROOT / 'imports/original-sales-report.json').is_file():
            self.skipTest('Private workbook records must be imported locally before this source comparison.')
        before=self.client.get('/api/workspace',buffered=True).json['workspace']['revision']
        response=self.client.get('/api/sales-report/import',buffered=True)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json['meetings']),425)
        self.assertEqual(response.json['allFollowups'],611)
        self.assertEqual(len(response.json['leads']),8)
        self.assertEqual(self.client.get('/api/workspace',buffered=True).json['workspace']['revision'],before)
        self.assertEqual(self.client.get('/sales-report.js',buffered=True).status_code,200)
        self.assertIn(b'sales-report.js',self.client.get('/',buffered=True).data)

    def test_background_jobs_stay_disabled(self):
        self.assertFalse(run_local.operations.scheduler.running)
        self.assertEqual(run_local.operations.DATABASE_URL, '')

if __name__ == '__main__':
    unittest.main()
