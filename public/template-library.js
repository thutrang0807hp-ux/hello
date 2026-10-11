/* Local shortlist retrieval; the AI then chooses how to use the supplied references. */
const TemplateLibrary=(()=>{
 const stop=new Set('a an and are as at be been by can for from have i in is it its looking me my of on or our please project that the their this to we will with work you your cần có của cho công việc một là và với tôi bạn khách hàng muốn làm'.split(' '));
 const tokens=value=>[...new Set(String(value||'').toLowerCase().normalize('NFKC').match(/[\p{L}\p{N}]+/gu)||[])].filter(t=>t.length>2&&!stop.has(t));
 function entries(records){return records.filter(r=>['template','sentproposal'].includes(r.kind)&&String(r.body||'').trim()).map(r=>({id:(r.kind==='template'?'t-':'s-')+r.id,sourceId:r.id,name:r.name||'Mẫu chưa đặt tên',body:r.body,source:r.kind,outcome:r.outcome||r.sourceOutcome||''}));}
 function choose(records,nodes,requirements){const all=entries(records),libraries=nodes.filter(n=>n.type==='template'&&n.libraryMode),pinned=new Set(libraries.flatMap(n=>n.libraryPinned||[])),eligible=new Map();
 for(const n of libraries){const excluded=new Set(n.libraryExcluded||[]);const selected=new Set(n.librarySelected||[]);for(const r of all)if(n.librarySelectionMode==='manual'?selected.has(r.id):!excluded.has(r.id))eligible.set(r.id,r);}
 for(const n of nodes.filter(n=>n.type==='template'&&String(n.content||'').trim()))eligible.set('node-'+n.id,{id:'node-'+n.id,name:n.title||'Khung riêng',body:n.content,sourceId:n.sourceId||null,source:'node',outcome:n.sourceOutcome||'',explicit:!n.libraryMode});
 const query=tokens(requirements),ranked=[...eligible.values()].map(r=>{const title=new Set(tokens(r.name)),body=new Set(tokens(r.body)),matches=query.filter(t=>title.has(t)||body.has(t));let code=2166136261;for(const char of r.body)code=Math.imul(code^char.charCodeAt(0),16777619);return {...r,key:r.sourceId?'source-'+r.sourceId:'custom-'+(code>>>0).toString(16),score:matches.reduce((sum,t)=>sum+(title.has(t)?3:1),0)+(matches.length&&r.outcome==='won'?.25:0),matches,pinned:pinned.has(r.id)};}).filter(r=>r.pinned||r.explicit||r.score>0).sort((a,b)=>Number(b.pinned)-Number(a.pinned)||Number(b.explicit)-Number(a.explicit)||b.score-a.score||a.id.localeCompare(b.id));
 const seen=new Set(),selected=[];for(const r of ranked){const key=r.body.trim().replace(/\s+/g,' ').toLowerCase();if(seen.has(key))continue;seen.add(key);selected.push({...r,reason:r.pinned?'Bạn ghim ưu tiên':r.explicit?'Mẫu nối riêng vào luồng':'Liên quan: '+r.matches.slice(0,5).join(', ')});if(selected.length===8)break;}
 return {total:all.length,eligible:eligible.size,selected,method:'Lọc theo nội dung job; AI vận dụng khi viết'};
 }
 return {entries,choose,tokens};
})();
if(typeof module!=='undefined')module.exports=TemplateLibrary;
