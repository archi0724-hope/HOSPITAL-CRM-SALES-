Latest uploaded-project refresh: see [INTEGRATION_UPDATE.md](INTEGRATION_UPDATE.md). The Operations bootstrap defect documented in the earlier audit has been repaired.

# Local CRM integration

The existing CRM stays at http://localhost:5500. Its Sales Meeting Dashboard, styles, sample data and browser storage key are preserved. The sidebar adds 17 Sales Operations entries. The imported workflows share the CRM’s white-and-violet styling, light/dark appearance, title area and grouped sidebar. Operations module changes retain the running workspace instead of reloading the full page. An Open in new tab link is available.

## Start

Double-click start-local.bat, or run:

    .venv\Scripts\python.exe run_local.py

If the environment needs rebuilding:

    uv venv --python 3.12 .venv
    uv pip install --python .venv\Scripts\python.exe -r sales-ops\requirements.txt

Keep the process running while using the CRM. The launcher binds to this computer only (127.0.0.1:5500). To stop the background instance started during integration, use the PID in local-server.pid; confirm that it is still the run_local.py process before stopping it. Subsequent manual starts can be stopped with Ctrl+C.

## Included

The ZIP's application source, static assets, templates, tests, documentation, main SQLite database and four supplied client/doctor/RGHS/served workbooks are in sales-ops/. Imported database totals at integration: 853 clients, 666 RGHS, 818 leads, 202 served, 185 doctors, 1 potential lead, 1 call, and 10 backups. These are workspace totals; records can overlap across sections.

The old meeting CRM keeps its original browser data (hospkart-crm-frontend-v1). Sales Operations uses sales-ops/data/hospkart_crm.db and its own storage namespace. They are available in one application but have different record schemas; records are not automatically merged or deduplicated between them. The meeting dashboard's totals remain unchanged.

The original CRM files are backed up in integration-backup/. The supplied ZIP remains unchanged. Packaged .env secrets, an old virtual environment, debug captures, database migration snapshots and a downloaded CLI binary were not copied into the working integration.

## External integrations

The local launcher uses SQLite and disables background scheduling and automatic outbound messaging. No external account credentials were imported. WhatsApp delivery, SMTP email, private Google access and live AI require configuration before they can work. All related application screens and handlers are included. QuoteSaarthi's saved CRM answers are available; product-catalog search requires a prepared catalog, which was not included in the supplied archive.

The source project's existing local access behavior is retained. For shared hosting, configure its administrator access and service credentials separately.

## Verification

- 178 supplied backend tests passed using temporary databases.
- 7 additional integration checks passed for routing, asset delivery, private files and preserved frontend data.
- All 17 sidebar module routes rendered successfully in a JavaScript DOM stub.
- The original dashboard markup is identical before integration and after visiting Operations and returning.
- Dashboard rendering function, styles.css and data.js are unchanged.
- Running-server checks passed for the root page, Operations, JavaScript, database health and Drive-link listing.
- Full browser visual verification could not complete because the computer-use tool timed out waiting for application access.

The standalone HTML file retains the original frontend. Use start-local.bat for the combined application; a simple static file server cannot run the added backend.

## Interface polish

Sales Operations navigation is grouped into Hospital directory, Sales pipeline, Customer outreach, and Reports & tools. Embedded pages hide their duplicate navigation and title; contextual workflow actions remain available. Parent/child navigation and theme messages require a matching origin and window source. QuoteSaarthi has a dedicated assistant view. Checks cover persistent module changes, assistant navigation, theme propagation and rejection of unrelated messages. The original meeting dashboard function, data and base stylesheet remain unchanged.
