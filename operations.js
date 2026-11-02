'use strict';
const OPS_MODULES=[["overview","Operations Overview","dashboard"],["clients","Hospitals & Clients","clients"],["rghs","RGHS Data","rghs"],["served","Already Served","served"],["doctors","Doctors","doctors"],["potential","Potential Leads","potential"],["leads","Leads & Queries","leads"],["quotes","Sales Quotations","quotes"],["orders","Sales Orders","orders"],["calling","Calling & Follow-up","calling"],["feedback","Feedback","feedback"],["whatsapp","WhatsApp Automation","whatsapp"],["email","Email Follow-ups","email"],["reports","Reports & Export","reports"],["data","Data & Backups","data"],["activity","Activity Log","activity"],["assistant","AI Assistance","assistant"]];
const OPS_DESCRIPTIONS={overview:'Your hospital relationships and sales activity at a glance.',clients:'Manage hospital relationships, contacts, and requirements.',rghs:'Organize RGHS hospitals and track your next steps.',served:'Stay connected with hospitals you have already served.',doctors:'Keep doctor contacts and conversations in one place.',potential:'Turn qualified hospitals into active opportunities.',leads:'Track requirements from first enquiry to a clear next step.',quotes:'Follow quotation value, progress, and customer responses.',orders:'Track confirmed business and delivery progress.',calling:'Plan your outreach and keep every conversation on record.',feedback:'Follow up on service and close the loop with customers.',whatsapp:'Prepare and manage WhatsApp follow-ups.',email:'Prepare customer emails and follow-up schedules.',reports:'Review sales activity and export the records you need.',data:'Manage imports, spreadsheets, and workspace backups.',activity:'Review changes and activity across your workspace.',assistant:'Find CRM answers and prepare your next sales conversation.'};
function selectedOperationsModule(){return OPS_MODULES.find(m=>m[0]===(state.filters.module||'overview'))||OPS_MODULES[0];}
function operationsUrl(id,view,embedded=false){return (id==='activity'?'/activity?':'/operations/?view='+encodeURIComponent(view)+'&')+(embedded?'embedded=1&theme='+(document.body.classList.contains('dark')?'dark':'light'):'');}
function operationsPage(){
 const [id,label,view]=selectedOperationsModule();
 return '<section class="operations-workspace" aria-label="Sales operations"><div class="pagehead"><div><h1 id="operations-title">'+esc(label)+'</h1><p id="operations-description">'+esc(OPS_DESCRIPTIONS[id])+'</p></div><a id="operations-fullscreen" class="btn" target="_blank" rel="noopener" href="'+operationsUrl(id,view)+'" aria-label="Open '+esc(label)+' in a new tab">Open in new tab ↗</a></div><div class="operations-surface" aria-busy="true"><p class="operations-loading" role="status">Loading workspace…</p><iframe id="operations-frame" title="'+esc(label)+'" data-module="'+id+'" src="'+operationsUrl(id,view,true)+'" allow="clipboard-write"></iframe></div></section>';
}
function sendOperationsTheme(frame){if(frame?.contentWindow)frame.contentWindow.postMessage({type:'crm-theme',dark:document.body.classList.contains('dark')},location.origin);}
function renderOperations(){
 const [id,label,view]=selectedOperationsModule();
 document.title=label+' | Hope Admin';
 let frame=$('#operations-frame');
 const activityChanged=frame&&(frame.dataset.module==='activity')!==(id==='activity');
 if(!frame||activityChanged){$('#main').innerHTML=operationsPage();frame=$('#operations-frame');frame.addEventListener('load',()=>sendOperationsTheme(frame));return;}
 $('#operations-title').textContent=label;
 $('#operations-description').textContent=OPS_DESCRIPTIONS[id];
 $('#operations-fullscreen').href=operationsUrl(id,view);
 $('#operations-fullscreen').setAttribute('aria-label','Open '+label+' in a new tab');
 frame.title=label;
 if(frame.dataset.module!==id){frame.dataset.module=id;if(frame.dataset.ready==='true')frame.contentWindow.postMessage({type:'crm-module',view},location.origin);}
 sendOperationsTheme(frame);
}
window.addEventListener('message',event=>{
 const frame=$('#operations-frame');
 if(event.origin!==location.origin||!frame||event.source!==frame.contentWindow)return;
 const data=event.data;
 if(!data||typeof data!=='object')return;
 if(data.type==='crm-ready'){
  frame.dataset.ready='true';frame.closest('.operations-surface').setAttribute('aria-busy','false');
  frame.closest('.operations-surface').querySelector('.operations-loading').hidden=true;
  sendOperationsTheme(frame);
  if(frame.dataset.module!=='activity')frame.contentWindow.postMessage({type:'crm-module',view:selectedOperationsModule()[2]},location.origin);
 }
 if(data.type==='crm-navigate'){
  const module=OPS_MODULES.find(m=>m[2]===data.view);if(!module)return;
  frame.dataset.module=module[0];
  const next='#/operations?module='+module[0];if(location.hash!==next)location.hash=next;
 }
 if(data.type==='crm-search')ACTIONS.search();
});
new MutationObserver(()=>sendOperationsTheme($('#operations-frame'))).observe(document.body,{attributes:true,attributeFilter:['class']});

let workspaceNavCounts=null;
let workspaceNavCheckedAt=0;
let workspaceNavRequest=null;
const WORKSPACE_NAV=[['clients','Hospitals & Clients','users'],['rghs','RGHS Data','list'],['served','Already Served','check'],['doctors','Doctors','users'],['potential','HOSPkart Potential Leads','pin'],['leads','Leads & Queries','hand'],['quotes','Quotations','rupee'],['orders','Orders','box'],['calling','Calling & Follow-up','hand'],['feedback','Feedback','check'],['whatsapp','WhatsApp Automation','hand'],['email','Email Follow-ups','file'],['reports','Reports & Export','chart'],['data','Data & Backups','download'],['activity','Activity Log','list'],['assistant','AI Assistance','spark'],['overview','Operations Overview','chart']];
function operationsNavigation(){
 const dashboardActive=state.route==='dashboard';
 return '<div class="navgroup">WORKSPACE</div><a class="navrow '+(dashboardActive?'active':'')+'" href="'+link('dashboard')+'"'+(dashboardActive?' aria-current="page"':'')+'>'+icon('chart')+'Dashboard</a>'+WORKSPACE_NAV.map(([id,label,ico],index)=>{
  const active=state.route==='operations'&&(state.filters.module||'overview')===id;
  const countable=['clients','rghs','served','doctors','potential','leads','quotes','orders'].includes(id);
  const count=workspaceNavCounts?.[id];
  return (index===8?'<div class="workspace-nav-divider" aria-hidden="true"></div>':'')+'<a class="navrow '+(active?'active':'')+'" href="#/operations?module='+id+'"'+(active?' aria-current="page"':'')+'>'+icon(ico)+'<span class="workspace-nav-label">'+esc(label)+'</span>'+(countable?'<small class="workspace-nav-count" data-workspace-count="'+id+'" aria-label="'+esc(label)+' record count">'+(Number.isInteger(count)?count.toLocaleString('en-IN'):'—')+'</small>':'')+'</a>';
 }).join('');
}
async function refreshWorkspaceNavigation(force=false){
 if(workspaceNavRequest)return workspaceNavRequest;
 if(!force&&Date.now()-workspaceNavCheckedAt<30000)return;
 workspaceNavRequest=(async()=>{
  try{
   const response=await fetch('/api/workspace/navigation',{cache:'no-store',signal:AbortSignal.timeout(10000)});
   if(!response.ok)throw Error('Counts unavailable');
   const result=await response.json();
   if(!result.ok||!result.counts)throw Error('Counts unavailable');
   const keys=['clients','rghs','served','doctors','potential','leads','quotes','orders'];
   if(!keys.every(key=>Number.isInteger(result.counts[key])&&result.counts[key]>=0))throw Error('Invalid counts');
   workspaceNavCounts=result.counts;workspaceNavCheckedAt=Date.now();
   document.querySelectorAll('[data-workspace-count]').forEach(node=>{const count=workspaceNavCounts[node.dataset.workspaceCount];node.textContent=count.toLocaleString('en-IN');node.title=count+' records';});
  }catch(_){/* Keep previous counts; an unavailable count is never shown as zero. */}
  finally{workspaceNavRequest=null;}
 })();
 return workspaceNavRequest;
}
window.addEventListener('focus',()=>refreshWorkspaceNavigation(true));
window.addEventListener('message',event=>{
 const frame=$('#operations-frame');
 if(event.origin!==location.origin||!frame||event.source!==frame.contentWindow)return;
 if(event.data?.type==='crm-counts-changed'||event.data?.type==='crm-ready')refreshWorkspaceNavigation(true);
});
