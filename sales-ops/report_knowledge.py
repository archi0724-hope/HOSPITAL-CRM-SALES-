"""Read-only answers from the user's private, normalized Excel report. No model training."""
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / 'imports' / 'original-sales-report.json'


def matches(message):
    return bool(re.search(r'\b(?:meetings?|quotations?|employees?)\b|\b(?:provided|uploaded|original|sales)\s+(?:excel\s+)?report\b', message, re.I))


def load():
    if not SOURCE.is_file():
        raise ValueError('The provided Excel report is not loaded on this server. Import your private report first; saved workspace answers remain available.')
    payload=json.loads(SOURCE.read_text(encoding='utf-8'))
    if not isinstance(payload,dict) or not isinstance(payload.get('meetings'),list):
        raise ValueError('The report knowledge source is invalid. Re-import the original Excel report.')
    return payload


def facts(payload):
    meetings=payload['meetings'];period=payload['period']
    followups=[f for m in meetings for f in m.get('followups',[])]
    quotes=[q for m in meetings for q in m.get('quotations',[])]
    in_period=lambda f: period['from'] <= str(f.get('date',''))[:10] <= period['to']
    overdue=lambda f: bool(f.get('date')) and f['date'][:10]<period['to'] and f.get('status') not in ('Completed','Cancelled')
    return {'meetings':len(meetings),'employees':len(payload.get('employees',[])),
        'followups_all':len(followups),'followups_in_period':sum(in_period(f) for f in followups),
        'overdue_as_of_report':sum(overdue(f) for f in followups),'quotations':len(quotes),
        'quotation_value':str(sum((Decimal(str(q.get('totalAmount',0))) for q in quotes),Decimal(0)).quantize(Decimal('0.01'))),
        'accepted_quotations':sum(q.get('status')=='Accepted' for q in quotes),
        'updates':sum(len(m.get('updates',[])) for m in meetings),
        'documents':sum(len(m.get('documents',[])) for m in meetings),'hope_leads':len(payload.get('leads',[]))}


def status():
    try:
        payload=load()
        return {'available':True,'source':payload.get('sourceFile','Provided Excel report'),'period':payload['period'],'counts':facts(payload)}
    except (ValueError,OSError,KeyError,TypeError):
        return {'available':False}


def reply(message):
    payload=load();summary=facts(payload);period=payload['period'];text=message.casefold()
    footer=f"\nSource: {payload.get('sourceFile','Provided Excel report')} · snapshot {period['from']} to {period['to']}. This report is a snapshot, not today's live workspace."
    meetings=payload['meetings']
    if re.search(r'\b(?:delete|remove|reset|send|edit|change|update)\b',text) and not re.search(r'\b(?:how|draft|help|steps)\b',text):
        return 'The report connection is read-only. Use the CRM controls to change records; no record or message was changed.'+footer
    if re.search(r'\b(?:invoice|payment|stock|gst|tax rate)\b',text):
        return 'This report does not contain verified invoices, payment history, stock or item GST details. Original quotation totals are preserved; missing values are not inferred.'+footer
    people=[p for p in payload.get('employees',[]) if (p.get('code') and re.search(r'(?<!\w)'+re.escape(p['code'].casefold())+r'(?!\w)',text)) or (p.get('name') and len(p['name'])>=4 and p['name'].casefold() in text)]
    if people:
        codes={p['code'] for p in people};rows=[m for m in meetings if m.get('employeeCode') in codes]
        followups=[f for m in rows for f in m.get('followups',[]) if period['from']<=f.get('date','')[:10]<=period['to']]
        return ('Employee: '+', '.join(p.get('name',p['code']) for p in people)+f"\nMeetings: {len(rows)} · in-period follow-ups: {len(followups)} · quotations: {sum(len(m.get('quotations',[])) for m in rows)}."+footer)
    if re.search(r'\b(?:find|search|details|lookup|meeting id)\b',text):
        term=re.sub(r'^.*?\b(?:find|search|lookup|details(?:\s+(?:for|of))?|meeting id)\s*[:#]?\s*','',message,flags=re.I).strip(' ?."\'').casefold()
        term=re.sub(r'^meeting\s*(?:id)?\s*[:#]?\s*','',term)
        rows=[m for m in meetings if term and (term==str(m.get('sourceId','')).casefold() or term in str(m.get('name','')).casefold())]
        if not rows:return 'No matching meeting in the provided report. Try the exact meeting ID or hospital name.'+footer
        lines=[f"{len(rows)} matching meeting records; showing up to 8:"]
        for m in rows[:8]:
            lines.append(f"Meeting {m.get('sourceId')} · {m.get('name','')} · {m.get('meetingStatus','')} · {m.get('employeeName','')} · follow-ups {len(m.get('followups',[]))} · quotations {len(m.get('quotations',[]))}")
        return '\n'.join(lines)+footer
    if re.search(r'\b(?:quotations?|quotes?)\b',text):
        return f"Quotations: {summary['quotations']} · original total: INR {summary['quotation_value']} · accepted: {summary['accepted_quotations']}. Item tax rates have not been invented."+footer
    if re.search(r'\b(?:follow[- ]?ups?|overdue)\b',text):
        return f"Follow-ups: {summary['followups_in_period']} within the report period; {summary['followups_all']} retained in total, including {summary['followups_all']-summary['followups_in_period']} outside the period. Overdue as of {period['to']}: {summary['overdue_as_of_report']}. These are report-date figures, not today's queue."+footer
    if re.search(r'\b(?:employees?|team)\b',text):
        return f"Named employees: {summary['employees']}. The source Summary also includes an Unassigned group. Ask using an exact employee name or code for their meetings and follow-ups."+footer
    if re.search(r'\b(?:documents?|updates?|hope leads?)\b',text):
        return f"Documents: {summary['documents']} stored links · updates: {summary['updates']} · HOPE leads: {summary['hope_leads']}. Files are not downloaded or sent by chat."+footer
    statuses=Counter(m.get('meetingStatus') or 'Unspecified' for m in meetings)
    return (f"Provided report: {summary['meetings']} meetings · {summary['employees']} named employees · {summary['hope_leads']} HOPE leads.\n"+
        'Meeting statuses: '+' · '.join(f'{key}: {value}' for key,value in sorted(statuses.items()))+
        f"\nFollow-ups: {summary['followups_in_period']} in period, {summary['followups_all']} retained; {summary['overdue_as_of_report']} overdue at report date.\nQuotations: {summary['quotations']} · INR {summary['quotation_value']} · updates: {summary['updates']} · documents: {summary['documents']}."+footer)
