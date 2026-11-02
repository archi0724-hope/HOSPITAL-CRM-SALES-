"""Run the original meeting dashboard and imported Sales Operations together."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPS = ROOT / 'sales-ops'
# This launcher always uses the bundled local SQLite workspace.
# External accounts and background jobs require separate configuration.
os.environ['DATABASE_URL'] = ''
os.environ['CRM_DATA_DIR'] = str(OPS / 'data')
os.environ['SCHEDULER_ENABLED'] = 'false'
os.environ['WHATSAPP_AUTOMATION_ENABLED'] = 'false'
os.environ['WHATSAPP_AUTO_REPLY_ENABLED'] = 'false'
os.environ['EMAIL_AUTOMATION_ENABLED'] = 'false'
sys.path.insert(0, str(OPS))

from flask import send_from_directory, jsonify
import app as operations
from waitress import serve

app = operations.app
operations_home = app.view_functions['home']
app.view_functions['home'] = lambda: send_from_directory(ROOT, 'index.html')
app.add_url_rule('/operations/', 'operations_home', operations_home)

PUBLIC_FILES = {'index.html', 'styles.css', 'data.js', 'excel.js', 'sales-report.js', 'operations.js', 'operations.css', 'sections.css', 'assistant.css', 'app.js', 'HOSPkart_CRM_Standalone.html'}

@app.get('/api/sales-report/import')
def original_sales_report_import():
    response = send_from_directory(ROOT / 'imports', 'original-sales-report.json')
    response.headers['Cache-Control'] = 'no-store, private'
    return response


@app.get('/api/workspace/navigation')
def workspace_navigation_counts():
    # Count in the local database; never transfer customer rows or backup archives.
    with operations.db_conn() as conn:
        row = conn.execute("""
            WITH workspace AS (SELECT revision, data FROM crm_workspace WHERE id=1),
            pipeline AS (
                SELECT value FROM workspace, json_each(workspace.data, '$.hk_v2_clients')
                UNION ALL
                SELECT value FROM workspace, json_each(workspace.data, '$.hk_v2_leads')
            )
            SELECT revision,
                json_array_length(data, '$.hk_v2_clients') AS clients,
                json_array_length(data, '$.hk_v2_rghs') AS rghs,
                json_array_length(data, '$.hk_v2_served') AS served,
                json_array_length(data, '$.hk_v2_doctors') AS doctors,
                json_array_length(data, '$.hk_v2_potential') AS potential,
                json_array_length(data, '$.hk_v2_leads') AS leads,
                (SELECT COUNT(*) FROM pipeline
                 WHERE CAST(COALESCE(json_extract(value,'$.quote'),0) AS REAL)>0) AS quotes,
                (SELECT COUNT(*) FROM pipeline
                 WHERE json_extract(value,'$.status') IN (
                    'PO / Order Confirmed','Order Finalized','Demand Fulfilled',
                    'Delivered','Feedback Pending','Completed / Served')
                 OR CAST(COALESCE(json_extract(value,'$.order'),0) AS REAL)>0) AS orders
            FROM workspace
        """).fetchone()
    counts = {key: int(row[key] or 0) for key in
              ('clients','rghs','served','doctors','potential','leads','quotes','orders')}
    response = jsonify(ok=True, revision=row['revision'], counts=counts)
    response.headers['Cache-Control'] = 'no-store, private'
    return response


@app.get('/<filename>')
def frontend_file(filename):
    if filename not in PUBLIC_FILES:
        from flask import abort
        abort(404)
    return send_from_directory(ROOT, filename)

@app.get('/assets/<path:filename>')
def frontend_asset(filename):
    return send_from_directory(ROOT / 'assets', filename)

@app.after_request
def local_response_headers(response):
    if response.mimetype == 'text/html' or response.mimetype == 'text/javascript':
        response.headers['Cache-Control'] = 'no-cache'
    return response

if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=int(os.getenv('PORT', '5500')), threads=6)
