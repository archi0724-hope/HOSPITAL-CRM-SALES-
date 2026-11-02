let quoteWorkspaceContext={};
let assistantCatalogueAvailable=false;
let quoteSaarthiSession=null;
let quoteSaarthiSubmitting=false;
let quoteKnowledgeLoading=false;
async function refreshQuoteSaarthiKnowledge() {
  if(quoteKnowledgeLoading)return;
  quoteKnowledgeLoading=true;
  const status=document.getElementById('quoteKnowledgeStatus');
  if(status)status.textContent='Checking saved CRM data…';
  try {
    const response=await fetch('/api/quotesaarthi/knowledge',{cache:'no-store',signal:AbortSignal.timeout(20000)});
    const result=await response.json();
    if(!response.ok||!result.ok)throw new Error(result.error||'CRM knowledge unavailable.');
    window.dispatchEvent(new CustomEvent('quotesaarthi:knowledge',{detail:result}));
    if(status)status.textContent='HOSPkart workspace connected · '+result.workspace_records+' records · revision '+result.revision+' · '+(result.checks.passed?'data checks passed':result.checks.issues.length+' data issues to review');
  }catch(error){if(status)status.textContent='Live CRM unavailable. Retry the knowledge check.';window.dispatchEvent(new Event('quotesaarthi:unavailable'));}
  finally{quoteKnowledgeLoading=false;}
}
try{quoteSaarthiSession=sessionStorage.getItem('hk_quotesaarthi_session');}catch(_){}
function rememberQuoteSaarthiSession(value){
  quoteSaarthiSession=value;
  try{if(value)sessionStorage.setItem('hk_quotesaarthi_session',value);else sessionStorage.removeItem('hk_quotesaarthi_session');}catch(_){}
}
function resetQuoteSaarthiConversation(){
  if(quoteSaarthiSubmitting)return;
  rememberQuoteSaarthiSession(null);
  document.getElementById('chatBody').replaceChildren();
  addChatMessage('Namaste! Ask me about saved CRM leads, queries, complaints, follow-ups, or product prices and draft quotations. CRM answers refresh from the shared database automatically.');
}
async function quoteSaarthiRequest(message,context,mode){
  mode=mode||document.getElementById('quoteAnswerSource')?.value||'';
  const widget=new URLSearchParams(location.search).get('widget')==='1';
  const selected=quoteWorkspaceContext.selected_client||(!widget?context?.selected_client:null);
  const references={selected_client:selected?{id:selected.id,workspaceScope:selected.workspaceScope}:null,current_view:quoteWorkspaceContext.current_view||context?.current_view};
  const response=await fetch('/api/quotesaarthi/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,context:references,mode,session_id:quoteSaarthiSession}),signal:AbortSignal.timeout(45000)});
  const result=await response.json();
  if(result.conversation_expired)rememberQuoteSaarthiSession(null);
  if(!response.ok||!result.ok)throw new Error(result.error||'AI Assistance request failed.');
  if(result.session_id)rememberQuoteSaarthiSession(result.session_id);
  if(result.knowledge)refreshQuoteSaarthiKnowledge();
  return result;
}
function renderQuoteSaarthiExports(message,exports){
  if(!exports?.length)return;
  const token=quoteSaarthiSession;
  const controls=document.createElement('div');controls.className='quotation-downloads';
  for(const file of exports){
    const button=document.createElement('button');button.className='btn';button.type='button';button.textContent='Download '+file.format.toUpperCase();
    button.addEventListener('click',async()=>{
      button.disabled=true;
      try{
        const response=await fetch('/api/quotesaarthi/download/'+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:token})});
        if(!response.ok)throw new Error('Export is unavailable. Generate the draft again in this conversation.');
        const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');
        link.href=url;link.download=file.name;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
      }catch(error){toast(error.message);}finally{button.disabled=false;}
    });
    controls.appendChild(button);
  }
  message.appendChild(controls);
}

function updateQuoteAnswerSource(){
 const source=document.getElementById('quoteAnswerSource')?.value,catalogue=source==='';
 const note=document.getElementById('quoteSourceStatus'),button=document.querySelector('.chat-send');
 if(note)note.textContent=source==='web'?'Google opens live search results in a new tab. Only the question you type is sent.':source==='report'?'Answers use the original Excel report snapshot and include its reporting period.':catalogue?(assistantCatalogueAvailable?'Product answers use your uploaded catalogue. Verify quotation details before sharing.':'Upload a verified catalogue for vendor prices and draft quotations. You can also use Google Search for public information.'):'Ask about saved CRM records or your report. For public information, choose Google Search.';
 const tools=document.getElementById('assistantCatalogueTools');if(tools)tools.hidden=!catalogue;
 if(button){button.disabled=quoteSaarthiSubmitting;button.textContent=source==='web'?'Search':'Send';}
}
async function refreshAssistantCatalogue(){
 try{const r=await fetch('/api/assistant/catalogue',{cache:'no-store',signal:AbortSignal.timeout(10000)});const data=await r.json();if(r.ok&&data.ok)assistantCatalogueAvailable=data.available;}catch(_){}
 updateQuoteAnswerSource();
}
function downloadAssistantCatalogueTemplate(){
 const blob=new Blob(['product_name,vendor_name,price,stock,category,manufacturer,specs,warranty\r\n'],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='product-catalogue-template.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function uploadAssistantCatalogue(input){
 const file=input.files?.[0];if(!file)return;
 if(quoteSaarthiSubmitting){toast('Wait for the current answer before uploading a catalogue.');input.value='';return;}
 if(file.size>5*1024*1024){toast('Choose a catalogue of 5 MB or less.');input.value='';return;}
 if(assistantCatalogueAvailable&&!confirm('Replace the saved product catalogue? New conversations will use the uploaded data. Existing quotations stay unchanged.')){input.value='';return;}
 const form=new FormData();form.append('file',file);form.append('replace',String(assistantCatalogueAvailable));
 try{
  const response=await fetch('/api/assistant/catalogue',{method:'POST',headers:{'X-CRM-Request':'1'},body:form});const result=await response.json();
  if(!response.ok||!result.ok){if(response.status===409)await refreshAssistantCatalogue();throw Error(result.error||'Catalogue could not be saved.');}
  assistantCatalogueAvailable=true;rememberQuoteSaarthiSession(null);updateQuoteAnswerSource();addChatMessage('Catalogue ready: '+result.products+' product offers. Ask for a product or vendor comparison. Confirm GST before preparing a draft quotation.');toast('Product catalogue saved.');
 }catch(error){toast(error.message);}finally{input.value='';}
}
function renderAssistantSearchActions(message,actions){
 if(!Array.isArray(actions))return;
 for(const action of actions){
  try{const url=new URL(action.url);if(url.protocol!=='https:'||url.hostname!=='www.google.com'||url.pathname!=='/search')continue;
   const link=document.createElement('a');link.className='btn assistant-search-link';link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';link.textContent=action.label||'Search Google';message.appendChild(link);
  }catch(_){}
 }
}
function searchGoogleFromInput(){
 const input=document.getElementById('chatInput'),text=input.value.trim();if(!text){input.focus();return;}
 const url=new URL('https://www.google.com/search');url.searchParams.set('q',text);
 addChatMessage(text,'user');input.value='';const response=addChatMessage('Google search results for your question (opens in a new tab):');
 renderAssistantSearchActions(response,[{label:'Open Google results',url:url.href}]);
 window.open(url.href,'_blank','noopener,noreferrer');
}

window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==parent)return;
 if(event.data?.type==='crm-assistant-context'&&event.data.context&&typeof event.data.context==='object'){
  quoteWorkspaceContext=event.data.context;
  const label=document.getElementById('quoteWorkspaceFocus');
  const names={clients:'Hospitals & Clients',rghs:'RGHS Data',served:'Already Served',doctors:'Doctors',potential:'Potential Leads',leads:'Leads & Queries',quotes:'Quotations',orders:'Orders',calling:'Calling & Follow-up'};
  if(label)label.textContent='Current view: '+(names[quoteWorkspaceContext.current_view]||'All HOSPkart workspaces')+(quoteWorkspaceContext.selected_client?' · selected record':'');
 }
 if(event.data?.type==='crm-workspace-updated')refreshQuoteSaarthiKnowledge();
});
