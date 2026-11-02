# Backend integration requirements

No private API endpoints, server source or database schema were available from the UI review. The contracts below are **proposed integration requirements**, not verified HOSPkart API URLs. The frontend is deliberately not connected to production.

## Local vs server responsibilities

| Feature | Working local implementation | Server work required |
| --- | --- | --- |
| Login, roles, MFA | Login preview; roles editor only | Authenticate, issue HttpOnly secure sessions, enforce authorization and MFA; audit access |
| Meetings, contacts, teams | CRUD and local lead generation | Validated CRUD, unique IDs, ownership, assignments, search and permissions |
| Dashboard | Labelled captured totals or local aggregation | Filtered aggregates, live alerts and quotation pipeline |
| Filters and exports | Client-side filtering, sorting, pagination and XLSX | Paginated queries and full-dataset exports at scale |
| Follow-ups | Schedule, next date and completion records | Scheduler, reminder delivery, timezone, task ownership and retries |
| Quotations | Line items, GST, totals, print and export | Official numbering, tax verification, approvals, versioning, PDF storage and sharing |
| Documents/media | Browser data URLs, 2 MB/file | Private file storage, MIME validation, size limits, malware checks, signed downloads |
| Updates and tags | Local activity records and team tags | Audit trail, notifications, email/WhatsApp integrations |
| Blogs/categories/brands/boxes | Local editor and media preview | Authorized publication, sanitization, SEO, stock and pricing validation |
| Coupons/plans | Local configuration | Eligibility, discount enforcement, expiry and recurring billing rules |
| Users/leads | Local sample management | Account lifecycle, duplicate detection, consent, secure profile persistence |
| Subscriptions/payments | Sample table, local edits and tabs | Gateway, idempotent webhooks, reconciliation and subscription expiry |
| Orders | Local fulfillment/payment status editor | Validated transitions, stock reservation, logistics and invoice integration |
| Settings | Local subscription price | Persistent authorized settings and charging logic |
| Languages | English UI, selector placeholder | Reviewed translations; no automatic translation service included |

## Proposed data contracts

`api.example.js` is an optional starting point. It is not referenced by index.html, so no network request is made by the delivered app. Implement the server first, replace the example paths with verified routes, then migrate local operations in app.js to async calls. Do not put API keys or production passwords in frontend JavaScript.

Suggested resources: `meetings`, `employees`, `sections`, `roles`, `locations`, `categories`, `brands`, `blogs`, `boxes`, `coupons`, `plans`, `leads`, `audits`, `users`, `subscriptions`, `payments`, `orders`, `settings`.

- List: `{items: [...], total: number, page: number, pageSize: number}`.
- Filters: employeeId, locationId, fromDate, toDate, meetingType, meetingStatus, recordStatus, search, sort, order.
- Meeting: `{id, name, type, locationId, employeeId, contact, phone, email, gst, address, pincode, meetingStatus, status, teamIds, createdAt, updatedAt}`.
- Follow-up: `{id, meetingId, scheduledAt, status, type, nextFollowupAt, outcome, remarks, taggedEmployeeIds}`.
- Quotation: `{id, number, meetingId, validUntil, status, currency:'INR', remarks, items:[{productId?, product, specifications, hsn, gstRate, quantity, unitPrice}], subtotal, gstAmount, total}`.
- Dashboard: aggregate metrics plus grouped meeting status, overdue follow-ups, upcoming activities, expired quotations and recent meetings.
- Money: calculate server-side with decimal arithmetic or integer minor units and an agreed tax/rounding policy. Browser totals are previews; HSN/GST must be verified.
- Timestamps: store UTC, display Asia/Kolkata where applicable. The current local demo uses the browser's timezone for entry dates.
- Updates/documents: meetingId, uploader/author, tags, timestamps, private file IDs; keep uploaded file bytes out of database text fields.

## Recommended error handling and access controls

Enforce authorization on the server for every operation. Client-visible roles and status filters do not secure records. Validate identifiers, file MIME, sizes, form values, stock, discounts, transitions and duplicates. Sanitize blog HTML on publication. Add CSRF protection for cookie-based state changes, restrictive CORS, rate limiting, request IDs, validation errors and concurrency/version checks. Use payment webhooks as the payment source of truth; never accept client edits as payment confirmation.

Back up the original database separately. This ZIP does not migrate any live records or alter the existing CRM.
