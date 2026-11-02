# HOSPkart CRM — Sales Operations and AI Assistance

Run the integrated dashboard locally at **http://localhost:5500**.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r sales-ops/requirements.txt
.venv\Scripts\python.exe run_local.py
```

AI Assistance offers **Google Search** for public queries: select it, type a question and press Search to open Google results in a separate tab. CRM records are not attached. Product prices and quotation drafts require verified product data: select Product catalogue & quotations, download the CSV template, and use Upload catalogue (CSV or XLSX, up to 5 MB / 10,000 rows). Missing catalogues produce actionable guidance instead of an error.

Recent features: reference-style Sections management; live sidebar status counts; saved **A− / A+** text sizing (80–150%); a bottom-right **AI Assistance** robot; local workspace answers; read-only knowledge from your private Excel report; additive report import and matching eight-sheet XLSX export. Google Gemini controls have been removed from the dashboard. The assistant is not a connection to private ChatGPT workspace chats.

## Private data setup

This public repository contains application source and demonstration records. Customer workbooks, the normalized report dataset, local SQLite databases, secrets, backups and inspection screenshots stay local and are ignored by Git.

To connect your own original Sales CRM report:

```powershell
.venv\Scripts\python.exe tools/prepare_original_sales_report.py "C:\path\to\sales-crm-report.xlsx"
```

Restart localhost, then refresh the browser. Import is additive; existing browser records are preserved. In **AI Assistance**, choose **Provided Excel report** for snapshot-specific questions. Questions about meetings, quotations or employees can also use that report automatically from HOSPkart workspace mode. Each report answer identifies its source and reporting period. This is local retrieval and deterministic calculation, not paid model fine-tuning. Live workspace questions continue to read saved Operations records. Report snapshots do not include subsequent browser-only meeting edits.

The source workbook must follow the eight-sheet schema in `imports/report-schema.json`. A checkout without the private dataset still runs the CRM; report-specific answers explain that the source needs importing. The product catalogue requires your separately configured catalogue data.

## Verification

Install `sales-ops/requirements-dev.txt` for browser checks; Chrome must be installed. Run `check_integration.py`, `tools/check_sections.py`, `sales-ops/tests/check_work_colors.py` and `sales-ops/tests/check_robot_assistant.py`. Backend unit tests run from `sales-ops` with `python -m unittest discover -s tests`.

---

# Original frontend reference

Sales Operations is now integrated. Start the combined application with **start-local.bat**, then visit **http://localhost:5500**. See [INTEGRATION.md](INTEGRATION.md) for the imported modules, database, startup and validation. The static-only instructions below apply to the original frontend.

A responsive HTML, CSS and JavaScript recreation of the authenticated HOPE Admin CRM reviewed on 31 October 2026. This is a local frontend implementation, not the original server source or a complete CRM database export.

## Open in VS Code

1. Extract `HOSPkart_CRM_Complete_Project.zip`.
2. In VS Code choose **File → Open Folder → hospkart-crm**.
3. Open `index.html` with VS Code Live Server, or simply double-click it.
4. Alternatively open `HOSPkart_CRM_Standalone.html`: it contains CSS, JavaScript and the logo in one file and requires no installation or internet.

Optional local server, from this folder:

```bash
python -m http.server 5500
```

Then visit `http://localhost:5500`. No npm install, framework, API key or build is required. Use a current Chrome, Edge, Firefox or Safari browser. Some browsers restrict file:// storage; use Live Server if saving is unavailable.

## Included

- Sales Meeting Dashboard with the observed layout and labelled reference totals.
- Employee Management: Sections, Roles, Employees.
- Sales & Marketing: Locations, Hospital Meetings, Vendor Meetings, All Meetings.
- Meeting detail tabs: Info, Follow-ups, Quotations, Documents, Updates.
- Settings: local subscription-price editor.
- HOPE: Categories, Brands, Blogs, Boxes, Coupons, Plans, Leads, Procurement Audits, Users, Subscriptions/Payments and Orders.
- Search, filters, date range, clear filters, sorting, pagination, column visibility, table/card view and dark theme.
- Local add/edit/delete forms, team assignment and lead generation.
- Quotation line items, GST calculations, status changes, Excel and print preview.
- Product media, pricing, inventory, specifications, tiers; blog FAQs and SEO fields; membership and plan editors.
- JSON backup/restore and genuine `.xlsx` workbook export (no CDN dependency).

## Data and source limits

The default dashboard summary is a **reference snapshot**: 425 meetings, 612 follow-ups, 228 scheduled, 14 quotations, ₹2,28,947 quotation value and 5 accepted. Status totals and alerts were also read from the live dashboard. These are historical observations, not live queries.

Lists use **22 demo meetings** and small demo datasets for other modules. Some organization names seen during inspection are used as labels. Contact details, activities and commercial figures in the local dataset are synthetic. All email addresses in demo records use example.com. It does not contain all 425 original records. Click **Use local totals** to calculate from local data; changing dashboard filters automatically uses local totals. Quotation Pipeline and activity lists always show local data and are labelled.

No production data is changed. No passwords, cookies, session tokens, payment credentials or original account secrets are bundled. Password and MFA controls are UI placeholders requiring a backend. Real notifications are not sent.

The displayed HOPE logo was retained from the source site. The frontend follows the observed white/blue/violet admin theme rather than changing it to HOSPkart's quotation gold theme. Typography uses an offline system fallback.

## Files

| File | Purpose |
| --- | --- |
| index.html | Multi-file entry point |
| styles.css | Desktop, tablet, mobile and print styles |
| data.js | Menu definitions, forms, columns and demo seed |
| app.js | Routes, filters, forms, local storage and interactions |
| excel.js | Dependency-free XLSX writer |
| assets/hope-logo.png | Source site's displayed HOPE logo |
| HOSPkart_CRM_Standalone.html | Complete single-file version |
| api.example.js | Optional backend adapter skeleton; not loaded |
| API_REQUIREMENTS.md | Integration contracts and backend boundary |
| INSPECTION.md | Reviewed screens, evidence and limitations |
| VALIDATION.md | Checks performed and limits |
| build_standalone.py | Regenerates the standalone HTML after edits |

## Saving and media

Local records save to localStorage in the current browser origin. Different ports, browsers or the standalone file can have separate workspaces. Use **Download local backup** and **Restore local backup** to move data. Restore replaces the local workspace. Browser data clearing removes local records.

Files are limited to 2 MB each in local mode; gallery supports up to 8 files. Browser quotas are usually much smaller than real object storage. The app warns on quota failures; reduce attachments or download a backup. Real multi-user document storage needs backend integration.

## Editing

Update `data.js` for forms, menus or seed data; `styles.css` for appearance; `app.js` for workflows. Run `python build_standalone.py` after editing to refresh the standalone version. Existing saved data takes precedence over changed seed records; test under a new local origin or intentionally clear the `hospkart-crm-frontend-v1` browser storage key after backing up.

## Verification limits

This recreation covers the observed page types and principal workflows. It is not a pixel-perfect copy of every original record/detail screen. Secondary dialogs and some administration details are approximated. Live authentication, permissions, payment processing, real reminders, document delivery, publishing and database synchronization require your tech team's backend.
