// Keep the imported workflows in step with the shared CRM navigation.
(async function(){
 const embedded=document.documentElement.classList.contains('crm-embedded');
 let ready=false;
 let pending=new URLSearchParams(location.search).get('view')||'dashboard';
 const notify=view=>{if(embedded&&ready)parent.postMessage({type:'crm-navigate',view},location.origin);};
 window.addEventListener('crm:workspace-saved',()=>{if(embedded)parent.postMessage({type:'crm-counts-changed'},location.origin);});
 const originalNavigate=window.navigate;
 window.navigate=function(view,el){
  if(!Object.hasOwn(pageInfo,view))return;
  const result=originalNavigate(view,el);
  document.documentElement.dataset.module=view;
  if(ready)notify(view);
  return result;
 };
 function applyView(view){
  if(view==='assistant'){document.documentElement.dataset.module='assistant';toggleChat(true);notify('assistant');return;}
  if(!Object.hasOwn(pageInfo,view))return;
  toggleChat(false);
  if(currentView!==view||document.documentElement.dataset.module!==view)window.navigate(view);
 }
 window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==parent||!event.data||event.data.type!=='crm-module')return;
  pending=event.data.view;if(ready)applyView(pending);
 });
 if(embedded)document.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();event.stopImmediatePropagation();parent.postMessage({type:'crm-search'},location.origin);}
 },true);
 while(document.body.inert)await new Promise(resolve=>setTimeout(resolve,50));
 applyView(pending);ready=true;
 if(embedded)parent.postMessage({type:'crm-ready'},location.origin);
})();

// Escape closes the global assistant when focus is inside its iframe.
if(new URLSearchParams(location.search).get('widget')==='1'){
 document.addEventListener('keydown',event=>{if(event.key==='Escape')parent.postMessage({type:'crm-assistant-close'},location.origin);});
}

// Only record references go to the local assistant. The server resolves saved facts.
window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==parent||event.data?.type!=='crm-assistant-context-request')return;
 let selected_client=null;
 if(document.getElementById('clientDrawer')?.classList.contains('open')){
  const id=document.getElementById('clientEditId').value;if(id)selected_client={id,workspaceScope:formRecordScope};
 }else if(document.getElementById('callDrawer')?.classList.contains('open')){
  const ref=recordReferenceParts(document.getElementById('formClient').value);selected_client={id:ref.id,workspaceScope:ref.scope||recordScopeForId(ref.id)};
 }else if(currentView==='whatsapp'){
  const value=document.getElementById('waClient')?.value;
  if(value){const ref=recordReferenceParts(value);selected_client={id:ref.id,workspaceScope:ref.scope||recordScopeForId(ref.id)};}
 }
 parent.postMessage({type:'crm-assistant-context-response',context:{current_view:currentView,selected_client}},location.origin);
});
