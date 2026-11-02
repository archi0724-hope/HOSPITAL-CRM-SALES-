# Source inspection record — 31 October 2026

Source: https://crm.hospkart.com/sales-meeting/dashboard. Authentication was completed in the user's browser session. No production records were created, updated, deleted or paid during review. Creation dialogs were opened and left without submission.

## Screens opened

| Area | Source UI route | Reviewed elements |
| --- | --- | --- |
| Home | / | Sidebar, header, account and theme controls |
| Dashboard | /sales-meeting/dashboard | 7 filters, KPIs, alerts, meeting status, overdue/upcoming follow-ups, expired quotations, recent meetings and pipeline |
| All meetings | /sales-meeting | Table headings, search, filters, table/card controls, columns, export, pagination, add dialog |
| Meeting detail | /sales-meeting/431 | Header, contact info, team, lead generation, five tabs |
| Follow-up | Detail tab | Date, status, type, next date, outcome, remarks, team tags |
| Quotation | Detail tab | Validity, remarks, product/specifications/HSN/GST/qty/unit price/total, Add Item |
| Documents | Detail tab | Name, file/upload, remarks, team tags |
| Updates | Detail tab | Update inputs, text area and tags; exact unlabeled input semantics approximated |
| Sections | /section | Table and New Section form |
| Roles | /role | Table and New Role form, section permissions |
| Employees | /employee?type=Employee | Table, New Employee basic form; Additional Details tab present but not exhaustively reviewed |
| Locations | /location | Table, ordering, status and New Location form |
| Hospital meetings | /hospital-sales-meeting | Same meeting table; fixed Hospital type; add dialog |
| Vendor meetings | /vendor-sales-meeting | Same table; fixed Vendor type; optional name/location, address, PIN code |
| Categories | /hope-category | Table, name, description and image editor |
| Brands | /hope-brand | Table, name, code and logo editor |
| Blogs | /hope-blog | Table, title, slug, category, cover, excerpt, content, author, tags, FAQ and SEO fields |
| Boxes | /hope-box | Table; Overview, Media, Pricing & stock, Specifications and Price tiers form tabs |
| Coupons | /hope-coupon | Table, code, description, discount type/value and employee |
| Plans | /hope-plan | Table, Details/Tags/Features tabs, monthly billing, prices and recommendation switch |
| Leads | /hope-lead | Table, name/email/phone/PIN, facility, role, lead status, spend and assignment |
| Procurement audits | /procurement-audit | Search/filters, refresh, table headers and pagination; initially loading |
| Users | /hope-user | User/facility/MFA summary, filters/table; New User Basic Info and Facility Profile forms |
| Subscriptions | /hope-subscription | Summary, plans filter, Subscriptions and Payments tab column schemas |
| Orders | /hope-order | Summary, order/payment/delivery filters and table schema |
| Settings | /settings | Subscription price field and Save changes |

All sidebar submenu labels and paths were expanded. Active/Inactive, Paid/Pending Payment and Active/Expired variants were identified. Filtered variants share the reconstructed table implementation; each remote variant was not separately visited.

## Observed dashboard totals

425 total meetings; 612 follow-ups; 228 scheduled; 14 quotations; 0 pending quotations; ₹2,28,947 quotation value; 5 accepted quotations; 10 overdue follow-up alerts; 4 expired quotation alerts; 23 pending meeting alerts.

Meeting status: Follow Up 68, Signed Up 46, Visited 269, Pending 23, Completed 12, Cancelled 7. Observed quotation pipeline: 0 Pending, 7 Shared, 5 Accepted, 2 Rejected. These totals are reference observations and are separated from the local records.

## Limits

No exhaustive crawl of every pagination page, row action, role, permission, order, subscription or detail record was performed. Some source tables were observed before their records finished loading; the visible headings/forms were still available. No server endpoint discovery, database export or original source recovery occurred. Static assets and visual layout were reconstructed with system fonts and small approximations. Authentication, MFA, forgot-password and payment actions were not exercised. The standalone file does not inherit the user's signed-in session.
