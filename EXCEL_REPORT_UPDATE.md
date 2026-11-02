# Original Sales CRM Excel report integration

The Dashboard and Meetings export actions now download `sales-crm-report-YYYY-MM-DD.xlsx` with the original eight-sheet structure: Summary, Meetings, Follow Ups, Overdue Follow Ups, Quotations, Updates, Documents, and Hope Leads. Headers, sheet order, column widths, blue header styling, date text, employee summaries and numeric quotation amounts follow the supplied workbook. Detail row ordering can differ because activities are grouped under their meetings.

## Activate the additive import

Open or refresh http://localhost:5500. On the next load, the browser imports the supplied report into the existing Meetings, Employees and HOPE Leads records. Existing records and settings are retained. The original dashboard layout and reference dashboard snapshot remain unchanged. Sales Operations client lists use their separate SQLite workspace and are not overwritten by this import.

The source contains 425 meetings, 19 named employees, 8 leads, 611 distinct follow-ups, 14 quotations, 208 updates and 11 document links. Six follow-ups appear only in the Overdue sheet and predate the report period; they are retained. Exporting the original period, 1 April–2 November 2026, produces 605 in-period follow-ups and 598 overdue follow-ups. Source quotation totals sum to INR 228,946.85.

Imported records retain their source IDs. If a meeting ID conflicts with an existing local ID, a separate local ID is allocated and its nested activities remain linked to that meeting. Repeat loads skip the same source records. A fingerprint records completion in browser storage.

Before importing, the existing browser database is saved under `hospkart-crm-frontend-v1-before-original-report-import`. If a storage write fails, the importer leaves the in-memory database unchanged and displays recovery guidance. The backup is local to that browser and origin. Use the application's backup download for an independent copy. The import does not provide shared or cloud persistence.

Document links remain links and are opened only on user request. Original quotation totals and line-item descriptions are retained; missing GST and item specifications are not invented. Intentionally blank creator/assignment fields remain blank in the export. Other module exports retain their existing behavior.

## Verification and limits

- Ten integration checks pass, including the read-only import endpoint and unchanged Operations workspace revision.
- Isolated JavaScript tests verify additive import, ID collisions, repeat import, storage failure, employee filtering, invalid date ranges, and standalone script parsing.
- Independent openpyxl readback compares every source detail cell and employee summary value, plus headers and visible formatting. The original report period and generated timestamp are fixed only in this comparison fixture.
- Reference and generated worksheet header previews were rendered; Summary, Meetings and Quotations were visually inspected. A private openpyxl-normalized inspection copy was necessary because the source workbook's package metadata was rejected by the renderer. The source workbook itself was not modified.
- The running localhost root, script, import and workspace navigation endpoints return HTTP 200.
- Browser automation was unavailable. The user's actual browser import and download clicks were not observed. Refreshing the localhost application triggers the authorized import; the isolated tests do not modify the user's browser storage.
- The single-file HTML was rebuilt and its scripts parsed successfully. Automatic source import requires localhost; the private customer dataset is not embedded in that standalone file.

Reproduce the checks with the local Python environment and cached Node runtime:

1. Run `python check_integration.py`.
2. Run `node tools/test_sales_report.mjs`.
3. Run `python tools/check_sales_report.py <path-to-original-workbook>`.

The importer payload and verification workbooks contain private customer data and are excluded in `.gitignore`. Keep them local. `tools/prepare_original_sales_report.py` regenerates the payload from the supplied report; it does not write to the Operations database.
