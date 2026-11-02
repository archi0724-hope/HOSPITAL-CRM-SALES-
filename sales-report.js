'use strict';
const SALES_REPORT_SOURCE='original-sales-crm';
const SALES_REPORT_HEADERS={"Summary":["Employee Code","Employee Name","Total Meetings","Pending Meetings","Visited Meetings","Follow Up Meetings","Signed Up Meetings","Cancelled Meetings","Total Follow Ups","Completed Follow Ups","Pending Follow Ups","Overdue Follow Ups","Total Quotations","Quotation Value (INR)","Accepted Quotations","Hope Leads Assigned","Updates Logged","Documents Uploaded"],"Meetings":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Meeting Status","Meeting Type","Lead Type","Location","Contact Person","Contact Number","Contact Email","GST Number","Team Members","Remarks","Updates Count","Record Status","Created By","Created At","Updated At"],"Follow Ups":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Follow Up ID","Follow Up Date","Follow Up Status","Follow Up Type","Outcome","Next Follow Up Date","Assigned To","Remarks","Overdue","Tagged Team","Created At","Updated At"],"Overdue Follow Ups":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Follow Up ID","Follow Up Date","Follow Up Status","Follow Up Type","Assigned To","Remarks","Days Overdue"],"Quotations":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Quotation ID","Quotation Number","Quotation Status","Total Amount (INR)","Valid Until","Prepared By","Remarks","Line Items","Created At","Updated At"],"Updates":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Update ID","Update Summary","Update Status / Type","Created By","Created At","Updated At","Tagged Team"],"Documents":["Employee Code","Employee Name","Meeting ID","Hospital / Client","Document ID","Document Name","Document URL","Uploaded By","Remarks","Tagged Team","Created At","Updated At"],"Hope Leads":["Assigned Employee Code","Assigned Employee Name","Lead ID","Lead Name","Email","Phone Number","Hospital Name","Pincode","Lead Type","Lead Role","Procurement Spend","Lead Status","Record Status","Created By","Created At","Updated At"]};
function mergeOriginalSalesReport(existing,payload){
 const next=structuredClone(existing),stats={meetings:0,leads:0,employees:0,followups:0,quotations:0,updates:0,documents:0,remappedMeetingIds:0};
 for(const [key,source] of [['employee',payload.employees],['sales-meeting',payload.meetings],['hope-lead',payload.leads]]){
  next[key]??=[];const ids=new Set(next[key].map(row=>row.id));let nextId=Math.max(0,...next[key].map(row=>Number(row.id)||0))+1;
  for(const original of source){
   if(next[key].some(row=>row.sourceSystem===SALES_REPORT_SOURCE&&String(row.sourceId)===String(original.sourceId)))continue;
   const record=structuredClone(original);let id=Number(record.sourceId);if(!Number.isSafeInteger(id)||id<=0||ids.has(id)){while(ids.has(nextId))nextId++;id=nextId++;if(key==='sales-meeting')stats.remappedMeetingIds++;}
   ids.add(id);record.id=id;record.sourceSystem=SALES_REPORT_SOURCE;
   if(key==='sales-meeting'){for(const type of ['followups','quotations','updates','documents'])stats[type]+=record[type].length;}
   next[key].push(record);stats[key==='employee'?'employees':key==='sales-meeting'?'meetings':'leads']++;
  }
 }
 next.originalSalesReport={fingerprint:payload.fingerprint,sourceFile:payload.sourceFile,period:payload.period,importedAt:new Date().toISOString(),sourceCounts:payload.counts};
 return {database:next,stats};
}
async function loadOriginalSalesReport(){
 if(location.protocol==='file:')return;
 try{
  const response=await fetch('/api/sales-report/import',{cache:'no-store'});if(!response.ok)return;
  const payload=await response.json();if(db.originalSalesReport?.fingerprint===payload.fingerprint)return;
  const result=mergeOriginalSalesReport(db,payload);
  localStorage.setItem(KEY+'-before-original-report-import',JSON.stringify(db));
  localStorage.setItem(KEY,JSON.stringify(result.database));
  db=result.database;sidebar();renderMain();
  toast('Imported '+result.stats.meetings+' original meetings and linked activities. Existing records were preserved.');
 }catch(error){toast('Original report import could not be saved. Existing records are unchanged. Download a backup and check browser storage, then reload.');}
}
function reportId(value){const text=String(value??'');return /^\d{1,15}$/.test(text)&&Number.isSafeInteger(Number(text))?Number(text):text;}
function reportDay(value){if(!value)return '';const s=String(value);if(/^\d{4}-\d{2}-\d{2}/.test(s))return s.slice(0,10);const m=s.match(/^(\d{2})\/(\d{2})\/(\d{4})/);return m?m[3]+'-'+m[2]+'-'+m[1]:'';}
function reportDate(value,time=false){const day=reportDay(value);if(!day)return '';const [y,m,d]=day.split('-');const t=String(value).match(/(?:T| )(\d{2}:\d{2}(?::\d{2})?)/);return d+'/'+m+'/'+y+(time&&t?' '+t[1]:'');}
function reportJoin(value){return Array.isArray(value)?value.map(v=>typeof v==='object'?(v.name||v.code||''):v).join(', '):String(value??'');}
function buildSalesReport(database,options={}){
 const all=database['sales-meeting']||[],leads=database['hope-lead']||[],employees=database.employee||[];
 const to=options.to||today(),from=options.from||database.originalSalesReport?.period?.from||all.map(r=>reportDay(r.created)).filter(Boolean).sort()[0]||to;
 if(from>to)throw Error('Report start date must not be after the end date.');
 const inPeriod=value=>{const day=reportDay(value);return !!day&&day>=from&&day<=to;};
 const employeeFilter=options.employee||'';
 const selected=m=>(!employeeFilter||[m.employee,m.employeeCode,m.employeeName].includes(employeeFilter))&&(!options.location||m.location===options.location)&&(!options.type||m.type===options.type)&&(!options.meetingStatus||m.meetingStatus===options.meetingStatus)&&(!options.status||m.status===options.status);
 const owner=(row,parent={})=>{const name=row.employeeName||row.employee||parent.employeeName||parent.employee||'';const code=row.employeeCode||parent.employeeCode;const match=employees.find(e=>e.code===code)||employees.find(e=>e.name===name);return {code:String(code||match?.code||(name?'':'N/A')),name:String(row.employeeName||match?.name||name||'Unassigned')};};
 const data=Object.fromEntries(Object.keys(SALES_REPORT_HEADERS).map(name=>[name,[]]));
 const summary=new Map();
 function group(person){const key=person.code+'\0'+person.name;if(!summary.has(key))summary.set(key,[person.code,person.name,...Array(16).fill(0)]);return summary.get(key);}
 for(const e of employees)if(!employeeFilter||[e.name,e.code].includes(employeeFilter))group({code:String(e.code||''),name:String(e.name||'Unassigned')});
 const parentId=m=>m.id;
 for(const m of all.filter(selected)){
  const person=owner(m),g=group(person),base=[person.code,person.name,parentId(m),m.name||''];
  if(inPeriod(m.created)){
   data.Meetings.push([...base,m.meetingStatus||'',m.type||'',m.leadType||m.type||'',m.location||'',m.contact||'',String(m.phone||''),m.email||'',m.gst||'',reportJoin(m.team),m.remarks||'',(m.updates||[]).length,m.status||'',m.createdBy??person.name,reportDate(m.created,true),reportDate(m.updated,true)]);
   g[2]++;const index={'Pending':3,'Visited':4,'Follow Up':5,'Signed Up':6,'Cancelled':7}[m.meetingStatus];if(index!==undefined)g[index]++;
  }
  for(const f of m.followups||[]){const p=owner(f,m),s=group(p),b=[p.code,p.name,parentId(m),m.name||''];const overdue=!['Completed','Cancelled'].includes(f.status)&&reportDay(f.date)&&reportDay(f.date)<to;
   if(inPeriod(f.date)){data['Follow Ups'].push([...b,reportId(f.sourceId||f.id||''),reportDate(f.date),f.status||'',f.type||'',f.outcome||'',reportDate(f.nextDate),f.assignedTo||p.name,f.remarks||'',overdue?'Yes':'No',reportJoin(f.team),reportDate(f.created,true),reportDate(f.updated,true)]);s[8]++;s[f.status==='Completed'?9:10]++;}
   if(overdue){data['Overdue Follow Ups'].push([...b,reportId(f.sourceId||f.id||''),reportDate(f.date),f.status||'',f.type||'',f.assignedTo||p.name,f.remarks||'',Math.floor((Date.parse(to+'T00:00:00Z')-Date.parse(reportDay(f.date)+'T00:00:00Z'))/86400000)]);s[11]++;}
  }
  for(const q of m.quotations||[]){if(!inPeriod(q.created||m.created))continue;const p=owner(q,m),s=group(p),amount=quoteTotal(q);data.Quotations.push([p.code,p.name,parentId(m),m.name||'',reportId(q.sourceId||q.id||''),q.number||q.id||'',q.status||'',amount,reportDate(q.validUntil),q.preparedBy||p.name,q.remarks||'',q.lineItemsText||(q.items||[]).map(i=>(i.product||'')+' x'+i.qty+' @ '+i.price).join(', '),reportDate(q.created,true),reportDate(q.updated,true)]);s[12]++;s[13]=Math.round((s[13]+amount)*100)/100;if(q.status==='Accepted')s[14]++;}
  for(const u of m.updates||[]){if(!inPeriod(u.created||u.date||m.created))continue;const p=owner(u,m);data.Updates.push([p.code,p.name,parentId(m),m.name||'',reportId(u.sourceId||u.id||''),u.description||u.title||'',u.updateType||u.status||'',u.createdBy??p.name,reportDate(u.created||u.date,true),reportDate(u.updated,true),reportJoin(u.team)]);group(p)[16]++;}
  for(const d of m.documents||[]){if(!inPeriod(d.created||m.created))continue;const p=owner(d,m);data.Documents.push([p.code,p.name,parentId(m),m.name||'',reportId(d.sourceId||d.id||''),d.name||d.fileName||'',d.url||d.documentUrl||'',d.uploadedBy||p.name,d.remarks||'',reportJoin(d.team),reportDate(d.created,true),reportDate(d.updated,true)]);group(p)[17]++;}
 }
 for(const l of leads){if(!inPeriod(l.created)||employeeFilter&&![l.employee,l.employeeCode,l.employeeName].includes(employeeFilter))continue;if(options.sourceMeetingIds&&l.sourceMeeting&&!options.sourceMeetingIds.includes(l.sourceMeeting))continue;const p=owner(l);data['Hope Leads'].push([l.employeeCode??p.code,l.employeeName??p.name,reportId(l.sourceId||l.id||''),l.name||'',l.email||'',String(l.phone||''),l.hospitalName||'',String(l.pincode||''),l.facility||'',l.role||'',l.spend||'',l.leadStatus||'',l.status||'',l.createdBy??p.name,reportDate(l.created,true),reportDate(l.updated,true)]);group(p)[15]++;}
 const generated=options.generatedAt||new Date();const generatedText=typeof generated==='string'?generated:new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kolkata',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(generated).replace(',','');
 data.Summary=[['Sales CRM Monthly Report'],['Report Period: '+reportDate(from)+' to '+reportDate(to)],['Generated At: '+generatedText],[],SALES_REPORT_HEADERS.Summary,...[...summary.values()].sort((a,b)=>a[1].localeCompare(b[1]))];
 return {from,to,data,sheets:Object.keys(SALES_REPORT_HEADERS).map(name=>({name,columns:SALES_REPORT_HEADERS[name].length,headerRow:name==='Summary'?5:1,rows:name==='Summary'?data[name]:[SALES_REPORT_HEADERS[name],...data[name]]}))};
}
function exportOriginalSalesReport(){
 try{const result=buildSalesReport(db,{...state.filters,type:SCHEMAS[state.route]?.fixedType||state.filters.type});download(excelWorkbookSheets(result.sheets),'sales-crm-report-'+today()+'.xlsx');toast('Exported the eight-sheet Sales CRM report from current records. Reference dashboard totals are not substituted for records.');}
 catch(error){toast('Report export failed: '+error.message);}
}
