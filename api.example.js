/* OPTIONAL SKELETON — not loaded by the app.
   The paths below are proposed examples, NOT discovered production routes.
   Configure only after your tech team supplies verified API contracts. */
'use strict';
function createCRMApi({baseUrl,resourcePaths}) {
  if (!baseUrl || !resourcePaths) throw new Error('Verified API configuration is required.');
  async function request(path,{method='GET',body}={}) {
    const response=await fetch(new URL(path,baseUrl),{
      method,credentials:'include',
      headers:{'Accept':'application/json',...(body?{'Content-Type':'application/json'}:{})},
      ...(body?{body:JSON.stringify(body)}:{})
    });
    if (!response.ok) throw new Error('CRM request failed ('+response.status+').');
    return response.status===204?null:response.json();
  }
  function path(resource,id='') {
    if(!resourcePaths[resource])throw new Error('No verified API mapping for '+resource);
    return resourcePaths[resource]+(id?'/'+encodeURIComponent(id):'');
  }
  return {
    list:(resource,filters={})=>request(path(resource)+'?'+new URLSearchParams(filters)),
    get:(resource,id)=>request(path(resource,id)),
    create:(resource,record)=>request(path(resource),{method:'POST',body:record}),
    update:(resource,id,record)=>request(path(resource,id),{method:'PATCH',body:record}),
    remove:(resource,id)=>request(path(resource,id),{method:'DELETE'})
  };
}
