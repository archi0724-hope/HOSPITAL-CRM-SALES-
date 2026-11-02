// Accept appearance updates only from the containing application on this origin.
(function(){
 window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==window.parent||!event.data||event.data.type!=='crm-theme')return;
  document.documentElement.classList.toggle('crm-dark',event.data.dark===true);
 });
 if(document.documentElement.classList.contains('crm-embedded')&&document.body.classList.contains('admin-page'))parent.postMessage({type:'crm-ready'},location.origin);
})();
