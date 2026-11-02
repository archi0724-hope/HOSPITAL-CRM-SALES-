"""Convert the supplied report into additive import records. Never writes CRM databases."""
import argparse,hashlib,json,re
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('workbook',type=Path,help='Private original Sales CRM report (.xlsx)')
SOURCE=parser.parse_args().workbook
(ROOT/'imports').mkdir(exist_ok=True)
def text(value):return '' if value is None else str(value)
def date(value):
    value=text(value)
    for fmt in ('%d/%m/%Y %H:%M:%S','%d/%m/%Y'):
        try:return datetime.strptime(value,fmt).isoformat(timespec='seconds' if '%H' in fmt else 'auto')
        except ValueError:pass
    return value
def records(sheet):
    rows=list(sheet.iter_rows(values_only=True));headers=rows[0]
    return [dict(zip(headers,row)) for row in rows[1:] if any(v is not None for v in row)]
def owner(row):return {'employeeCode':text(row.get('Employee Code')),'employeeName':text(row.get('Employee Name'))}
def tags(value):return [v.strip() for v in re.split(r'[,;]',text(value)) if v.strip()]
w=load_workbook(SOURCE,data_only=True)
summary=w['Summary'];employees=[]
for row in summary.iter_rows(min_row=6,values_only=True):
    if row[0] is not None and row[0]!='N/A':employees.append({'sourceId':text(row[0]),'code':text(row[0]),'name':text(row[1]),'status':'Active','role':'No role','email':''})
meetings=[];lookup={}
for row in records(w['Meetings']):
    m={'sourceId':text(row['Meeting ID']),**owner(row),'name':text(row['Hospital / Client']),'type':text(row['Meeting Type']),'leadType':text(row['Lead Type']),'meetingStatus':text(row['Meeting Status']),'location':text(row['Location']),'contact':text(row['Contact Person']),'phone':text(row['Contact Number']),'email':text(row['Contact Email']),'gst':text(row['GST Number']),'team':tags(row['Team Members']),'remarks':text(row['Remarks']),'status':text(row['Record Status']),'createdBy':text(row['Created By']),'created':date(row['Created At']),'updated':date(row['Updated At']),'followups':[],'quotations':[],'updates':[],'documents':[]}
    m['employee']=m['employeeName'];meetings.append(m);lookup[m['sourceId']]=m
followups={}
for row in records(w['Follow Ups']):
    f={'sourceId':text(row['Follow Up ID']),**owner(row),'date':date(row['Follow Up Date'])[:10],'status':text(row['Follow Up Status']),'type':text(row['Follow Up Type']),'outcome':text(row['Outcome']),'nextDate':date(row['Next Follow Up Date'])[:10],'assignedTo':text(row['Assigned To']),'remarks':text(row['Remarks']),'team':tags(row['Tagged Team']),'created':date(row['Created At']),'updated':date(row['Updated At'])}
    lookup[text(row['Meeting ID'])]['followups'].append(f);followups[f['sourceId']]=f
for row in records(w['Overdue Follow Ups']):
    if text(row['Follow Up ID']) in followups:continue
    f={'sourceId':text(row['Follow Up ID']),**owner(row),'date':date(row['Follow Up Date'])[:10],'status':text(row['Follow Up Status']),'type':text(row['Follow Up Type']),'assignedTo':text(row['Assigned To']),'remarks':text(row['Remarks']),'outcome':'','nextDate':'','team':[],'created':'','updated':'','overdueOnly':True}
    lookup[text(row['Meeting ID'])]['followups'].append(f);followups[f['sourceId']]=f
for row in records(w['Quotations']):
    lookup[text(row['Meeting ID'])]['quotations'].append({'sourceId':text(row['Quotation ID']),**owner(row),'id':text(row['Quotation Number']) or text(row['Quotation ID']),'number':text(row['Quotation Number']),'status':text(row['Quotation Status']),'totalAmount':float(row['Total Amount (INR)'] or 0),'validUntil':date(row['Valid Until'])[:10],'preparedBy':text(row['Prepared By']),'remarks':text(row['Remarks']),'lineItemsText':text(row['Line Items']),'items':[],'created':date(row['Created At']),'updated':date(row['Updated At'])})
for row in records(w['Updates']):
    lookup[text(row['Meeting ID'])]['updates'].append({'sourceId':text(row['Update ID']),**owner(row),'title':text(row['Update Summary'])[:100],'description':text(row['Update Summary']),'updateType':text(row['Update Status / Type']),'createdBy':text(row['Created By']),'date':date(row['Created At'])[:10],'created':date(row['Created At']),'updated':date(row['Updated At']),'team':tags(row['Tagged Team'])})
for row in records(w['Documents']):
    lookup[text(row['Meeting ID'])]['documents'].append({'sourceId':text(row['Document ID']),**owner(row),'name':text(row['Document Name']),'url':text(row['Document URL']),'uploadedBy':text(row['Uploaded By']),'remarks':text(row['Remarks']),'team':tags(row['Tagged Team']),'created':date(row['Created At']),'updated':date(row['Updated At']),'file':''})
leads=[]
for row in records(w['Hope Leads']):
    leads.append({'sourceId':text(row['Lead ID']),'employeeCode':text(row['Assigned Employee Code']),'employeeName':text(row['Assigned Employee Name']),'employee':text(row['Assigned Employee Name']),'name':text(row['Lead Name']),'email':text(row['Email']),'phone':text(row['Phone Number']),'hospitalName':text(row['Hospital Name']),'pincode':text(row['Pincode']),'facility':text(row['Lead Type']),'role':text(row['Lead Role']),'spend':text(row['Procurement Spend']),'leadStatus':text(row['Lead Status']),'status':text(row['Record Status']),'createdBy':text(row['Created By']),'created':date(row['Created At']),'updated':date(row['Updated At'])})
period=re.findall(r'\d{2}/\d{2}/\d{4}',text(summary['A2'].value))
result={'sourceSystem':'original-sales-crm','sourceFile':SOURCE.name,'fingerprint':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'period':{'from':date(period[0])[:10],'to':date(period[1])[:10]},'employees':employees,'meetings':meetings,'leads':leads,'counts':{s.title:s.max_row-(5 if s.title=='Summary' else 1) for s in w},'allFollowups':len(followups)}
(ROOT/'imports/original-sales-report.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf8')
schema={s.title:[c.value for c in s[5 if s.title=='Summary' else 1]] for s in w}
(ROOT/'imports/report-schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'source_counts':result['counts'],'all_imported_followups':len(followups),'quotation_value':sum(q['totalAmount'] for m in meetings for q in m['quotations'])}))
