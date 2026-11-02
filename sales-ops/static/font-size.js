/* Text-only sizing: explicit pixel font sizes scale once; layout dimensions stay fixed. */
(function(){
 'use strict';
 const key='hospkart-crm-font-percent',min=80,max=150,step=10;
 const valid=value=>Number.isInteger(value)&&value>=min&&value<=max&&value%step===0;
 let percent=100;
 try{const stored=Number(localStorage.getItem(key));if(valid(stored))percent=stored;}catch(_){}
 const scaleStyle=style=>{const value=style?.getPropertyValue('font-size');if(value&&/^\d+(?:\.\d+)?px$/.test(value.trim()))style.setProperty('font-size',`calc(${value} * var(--crm-font-scale, 1))`,style.getPropertyPriority('font-size'));};
 function scaleRules(rules){for(const rule of rules||[]){if(rule.style)scaleStyle(rule.style);try{if(rule.cssRules)scaleRules(rule.cssRules);}catch(_){}}}
 function scaleSheets(){for(const sheet of document.styleSheets)try{scaleRules(sheet.cssRules);}catch(_){}}
 function inlineFonts(node){if(node.nodeType!==1)return;if(node.hasAttribute('style'))scaleStyle(node.style);node.querySelectorAll('[style]').forEach(el=>scaleStyle(el.style));}
 function controls(){
  document.querySelectorAll('[data-font-step]').forEach(button=>{button.disabled=Number(button.dataset.fontStep)<0?percent===min:percent===max;});
  document.querySelectorAll('[data-font-reset]').forEach(button=>{if(button.textContent!==percent+'%')button.textContent=percent+'%';button.setAttribute('aria-label','Reset text size, currently '+percent+' percent');});
 }
 function broadcast(){for(const frame of document.querySelectorAll('iframe'))try{if(new URL(frame.src,location.href).origin===location.origin)frame.contentWindow.postMessage({type:'crm-font-size',percent},location.origin);}catch(_){}}
 function apply(value,persist=false){if(!valid(value))return;percent=value;document.documentElement.style.setProperty('--crm-font-scale',String(percent/100));controls();if(persist)try{localStorage.setItem(key,String(percent));}catch(_){}broadcast();}
 scaleSheets();inlineFonts(document.documentElement);apply(percent);
 document.addEventListener('click',event=>{const button=event.target.closest('[data-font-step],[data-font-reset]');if(!button||button.disabled)return;event.preventDefault();apply(button.hasAttribute('data-font-reset')?100:Math.min(max,Math.max(min,percent+Number(button.dataset.fontStep)*step)),true);});
 document.addEventListener('load',event=>{if(event.target.tagName==='IFRAME')broadcast();if(event.target.tagName==='LINK')scaleSheets();},true);
 window.addEventListener('message',event=>{if(event.origin===location.origin&&event.source===parent&&event.data?.type==='crm-font-size')apply(event.data.percent);});
 window.addEventListener('storage',event=>{if(event.key===key)apply(event.newValue===null?100:Number(event.newValue));});
 new MutationObserver(records=>{let sheets=false;for(const record of records){if(record.type==='attributes')scaleStyle(record.target.style);for(const node of record.addedNodes){inlineFonts(node);if(node.nodeType===1&&['LINK','STYLE'].includes(node.tagName))sheets=true;}}if(sheets)scaleSheets();controls();}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style']});
})();
