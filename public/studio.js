/* Node workspace and immutable sent-letter archive. No third-party UI dependencies. */
const Studio = (() => {
  const labels = {job:'Thông tin công việc',template:'Kho mẫu tham khảo',draft:'AI chắt lọc & viết',review:'AI đánh giá',final:'Thư cuối'};
  const icons = {job:'▤',template:'▧',draft:'✎',review:'✦',final:'↗'};
  const outcomes = {pending:'Đang chờ kết quả',won:'Có hợp đồng',lost:'Không có hợp đồng',no_reply:'Không phản hồi'};
  let state = null, saveTask = null, archiveFilter = 'all', archiveSearch = '', connecting = null, inspectorOpen=false, undoGraph=null;
  const clone = value => structuredClone(value);
  const get = id => state.nodes.find(n => n.id === id);
  const unique = () => 'n-' + crypto.randomUUID();
  function fresh(item = {}) {
    const job = records.find(r => r.kind === 'job' && String(r.id) === String(item.jobId));
    const nodes = [
      {id:'job',type:'job',x:60,y:60,title:job?.name || 'Job đang ứng tuyển',content:item.requirements || job?.notes || '',jobId:job?.id || '',budget:item.budget || job?.budget || ''},
      {id:'template',type:'template',x:60,y:325,title:'Kho mẫu tham khảo',libraryMode:true,libraryExcluded:[],libraryPinned:[],content:'1. Nêu đúng mục tiêu của khách\n2. Kinh nghiệm liên quan có thật\n3. Cách giải quyết và phạm vi\n4. Giá / thời gian nếu đã rõ\n5. Câu hỏi để bắt đầu trao đổi'},
      {id:'draft',type:'draft',x:430,y:60,title:'Bản nháp đầu tiên',content:item.body || '',approach:item.approach || '',budget:item.budget || '',timeline:item.timeline || '',signature:item.signature || config?.profile?.name || '',language:item.language || 'English',instructions:item.instructions || ''},
      {id:'review',type:'review',x:800,y:60,title:'Chấm điểm & cải thiện',content:''},
      {id:'final',type:'final',x:1170,y:60,title:'Bản sẵn sàng gửi',content:item.body || ''},
    ];
    return {record:clone(item),nodes,edges:[['job','draft'],['template','draft'],['draft','review'],['review','final'],['draft','final']].map(([from,to])=>({from,to})),selected:'job',scale:1,edgeStyle:'curve',dirty:!item.id,busy:false};
  }
  function fromRecord(record) {
    const value = fresh(record);
    if (record.workspace?.version === 1 && Array.isArray(record.workspace.nodes)) {
      value.nodes = clone(record.workspace.nodes); value.edges = clone(record.workspace.edges || []);
      value.selected = value.nodes[0]?.id || null;value.edgeStyle=['curve','straight','step'].includes(record.workspace.edgeStyle)?record.workspace.edgeStyle:'curve'; value.scale = record.workspace.scale || 1;
    }
    return value;
  }
  function ancestors(id) {
    const seen = new Set(), result = [];
    function visit(target) {for (const edge of state.edges.filter(e=>e.to===target)) {if (!seen.has(edge.from)) {seen.add(edge.from); const node=get(edge.from); if(node) {result.push(node); visit(node.id);}}}}
    visit(id); return result;
  }
  function context(node) {
    const upstream = ancestors(node.id), job = upstream.find(n=>n.type==='job'), draft = upstream.find(n=>['draft','final'].includes(n.type));
    const review = upstream.find(n=>n.type==='review');
    const source = node.type === 'draft' ? node : draft || node;
    const drafting = upstream.find(n=>n.type==='draft') || {};
    const input = key => source[key] || drafting[key] || '';
    const libraryNodes=upstream.filter(n=>n.type==='template'&&n.libraryMode);
    const referenceSelection=TemplateLibrary.choose(records,upstream,upstream.filter(n=>n.type==='job').map(n=>n.title+' '+n.content).join(' '));
    return {jobId:job?.jobId || '',requirements:upstream.filter(n=>n.type==='job').map(n=>n.content).join('\n\n'),templates:libraryNodes.length?upstream.filter(n=>n.type==='template'&&!n.libraryMode).map(n=>n.content||''):referenceSelection.selected.map(r=>r.body),referenceLibrary:libraryNodes.length?libraryNodes.map(n=>({mode:n.librarySelectionMode||'auto',selectedIds:n.librarySelected||[],excludedIds:n.libraryExcluded||[],pinnedIds:n.libraryPinned||[]})):undefined,referenceShortlist:referenceSelection.selected.map(({id,name,reason,sourceId,key})=>({id,name,reason,sourceId,key})),approach:input('approach'),budget:input('budget') || job?.budget || '',timeline:input('timeline'),signature:input('signature') || config?.profile?.name || '',language:input('language') || 'English',instructions:input('instructions'),body:draft?.content || '',existingDraft:node.type==='final' ? draft?.content || '' : '',feedback:review?.evaluation ? JSON.stringify(review.evaluation) : ''};
  }
  function signature(node) {const c=context(node);return JSON.stringify({requirements:c.requirements,body:c.body,budget:c.budget,profile:config?.profile || {}});}
  function stale(node) {return !!node.evaluation && node.inputSignature !== signature(node);}
  function dirty() {state.dirty=true;const el=$('#studioSaveState');if(el)el.textContent='Có thay đổi chưa lưu';}
  function open(item = {}) {
    if (state?.busy || saveTask) return notice('Đợi thao tác hiện tại hoàn thành trước khi đổi workspace.');
    if (state?.dirty && (!state.record.id || state.record.id !== item.id) && !confirm('Workspace hiện tại chưa lưu. Bỏ thay đổi để mở workspace khác?')) return;
    state = fromRecord(item); connecting=null;undoGraph=null; view='proposal'; render(); fit();return true;
  }
  function openForJob(job){
    const linked=workspace=>String(workspace?.jobId||'')===String(job.id)||workspace?.workspace?.nodes?.some(n=>n.type==='job'&&String(n.jobId||'')===String(job.id));
    const current=state&&(linked(state.record)||state.nodes.some(n=>n.type==='job'&&String(n.jobId||'')===String(job.id)));
    if(state?.busy||saveTask){notice('Đợi thao tác hiện tại hoàn thành trước khi mở job.');return false;}
    if(current){view='proposal';render();}
    else {const saved=records.find(r=>r.kind==='proposal'&&linked(r));if(!open(saved||{name:'Proposal · '+job.name,jobId:job.id,clientId:job.clientId||'',requirements:job.notes||'',budget:job.budget||''}))return false;}
    let node=state.nodes.find(n=>n.type==='job'&&String(n.jobId||'')===String(job.id));
    if(!node){if(state.nodes.length>=30){notice('Workspace đã đủ 30 node. Xóa một node rồi thêm thông tin job.');return true;}node={id:unique(),type:'job',title:job.name,content:job.notes||'',budget:job.budget||'',jobId:job.id,...freePosition()};state.nodes.push(node);const draft=state.nodes.find(n=>n.type==='draft');if(draft)state.edges.push({from:node.id,to:draft.id});dirty();}
    state.selected=node.id;setInspector(true);draw();inspect();fit();window.scrollTo({top:0,behavior:'instant'});notice('Đã mở workspace cho job này. Mô tả và ngân sách nằm trong node Thông tin công việc.');return true;
  }
  function renderStudio() {
    if (!state) state = records.find(r=>r.kind==='proposal') ? fromRecord(records.find(r=>r.kind==='proposal')) : fresh();
    const proposals=records.filter(r=>r.kind==='proposal');
    $('#content').innerHTML = `<div class="studio-shell"><div class="studio-top"><div><span class="studio-kicker">PROPOSAL STUDIO / NODE WORKSPACE</span><input id="workspaceName" aria-label="Tên workspace" value="${esc(state.record.name || 'Proposal mới')}" maxlength="1000"></div><div class="studio-top-actions"><span id="studioSaveState">${state.dirty?'Có thay đổi chưa lưu':state.record.id?'Đã lưu':'Workspace mới'}</span><button id="openStudioLibrary">Kho mẫu</button><button id="newWorkspace">+ Workspace</button><button id="saveWorkspace" class="primary">Lưu workspace</button></div></div><div class="studio-controls"><select id="workspacePicker" aria-label="Mở workspace"><option value="">Chọn workspace đã lưu…</option>${proposals.map(p=>`<option value="${p.id}" ${p.id===state.record.id?'selected':''}>${esc(p.name)}</option>`).join('')}</select><div class="studio-node-tools">${Object.keys(labels).map(type=>`<button data-add-node="${type}">${icons[type]} + ${labels[type]}</button>`).join('')}</div></div><div class="studio-workarea ${inspectorOpen?'inspector-open':''}"><div class="canvas-column"><div class="canvas-toolbar"><span id="connectionHint">Kéo nền để di chuyển · Ctrl + lăn chuột để zoom</span><div><button id="zoomOut" aria-label="Thu nhỏ">−</button><span id="zoomLabel">${Math.round(state.scale*100)}%</span><button id="zoomIn" aria-label="Phóng to">+</button><button id="fitCanvas">Vừa khung</button><button id="arrangeNodes">Xếp luồng</button><select id="edgeStyle" aria-label="Kiểu đường nối"><option value="curve">Đường cong</option><option value="straight">Đường thẳng</option><option value="step">Gấp khúc</option></select><button id="undoGraph" ${undoGraph?'':'disabled'}>Hoàn tác</button><button id="toggleInspector" aria-expanded="${inspectorOpen}" aria-controls="nodeInspector">${inspectorOpen?'Đóng nội dung':'Nội dung node'}</button><button id="expandStudio" aria-label="Mở rộng workspace">Mở rộng</button></div></div><div id="canvasViewport" class="canvas-viewport" tabindex="0" aria-label="Không gian nối node"><div id="canvasSizer"><div id="nodeCanvas"><svg id="connections" aria-label="Các đường kết nối"></svg><div id="nodeLayer"></div></div></div></div><div id="studioMinimap" class="studio-minimap" aria-label="Bản đồ node"></div><div class="canvas-foot"><span>${state.nodes.length} node · ${state.edges.length} kết nối</span><span>Điểm AI là đánh giá nội dung, không phải khả năng thắng job.</span></div></div><section id="nodeInspector" class="node-inspector" aria-label="Nội dung node"></section></div></div>`;
    $('#workspaceName').oninput=e=>{state.record.name=e.target.value;dirty();};
    $('#workspacePicker').onchange=e=>{if(e.target.value)open(records.find(r=>r.id===Number(e.target.value)));};
    $('#openStudioLibrary').onclick=()=>{let node=state.nodes.find(n=>n.type==='template');if(!node){addNode('template');node=get(state.selected);}if(node)library(node);};
    $('#newWorkspace').onclick=()=>open({name:'Proposal mới'});
    $('#saveWorkspace').onclick=()=>save().catch(e=>notice(e.message));
    document.querySelectorAll('[data-add-node]').forEach(b=>b.onclick=()=>addNode(b.dataset.addNode));
    $('#zoomOut').onclick=()=>zoom(state.scale-.1); $('#zoomIn').onclick=()=>zoom(state.scale+.1); $('#fitCanvas').onclick=fit;
    $('#toggleInspector').onclick=()=>setInspector(!inspectorOpen);
    $('#arrangeNodes').onclick=arrange;
    $('#edgeStyle').value=state.edgeStyle||'curve';$('#edgeStyle').onchange=e=>{state.edgeStyle=e.target.value;dirty();draw();};
    $('#undoGraph').onclick=()=>{if(state.busy||!undoGraph)return;state.nodes=undoGraph.nodes;state.edges=undoGraph.edges;state.selected=undoGraph.selected;undoGraph=null;dirty();draw();inspect();$('#undoGraph').disabled=true;};
    $('#expandStudio').onclick=()=>{const shell=$('.studio-shell');shell.classList.toggle('studio-expanded');$('#expandStudio').setAttribute('aria-label',shell.classList.contains('studio-expanded')?'Thu gọn workspace':'Mở rộng workspace');$('#expandStudio').textContent=shell.classList.contains('studio-expanded')?'Thu gọn':'Mở rộng';requestAnimationFrame(fit);};
    const viewport=$('#canvasViewport');
    viewport.addEventListener('wheel',event=>{if(!event.ctrlKey&&!event.metaKey)return;event.preventDefault();zoom(state.scale*(event.deltaY<0?1.12:1/1.12),event.clientX,event.clientY);},{passive:false});
    viewport.onkeydown=event=>{if(event.target!==viewport)return;if(event.key==='Escape'){connecting=null;$('#connectionHint').textContent='Đã hủy nối node';}if(event.key==='0'){event.preventDefault();fit();}if(event.key==='+'||event.key==='='){event.preventDefault();zoom(state.scale+.1);}if(event.key==='-'){event.preventDefault();zoom(state.scale-.1);}};

    viewport.onpointerdown=event=>{if(event.button!==0||event.target.closest('.flow-node,.edge-hit,.edge-delete'))return;const x=event.clientX,y=event.clientY,sx=viewport.scrollLeft,sy=viewport.scrollTop;const move=e=>{viewport.scrollLeft=sx-(e.clientX-x);viewport.scrollTop=sy-(e.clientY-y);};const stop=()=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',stop);};document.addEventListener('pointermove',move);document.addEventListener('pointerup',stop);};
    draw(); inspect();requestAnimationFrame(fit);
  }
  document.addEventListener('keydown',event=>{if(view==='proposal'&&event.key==='Escape'&&$('.studio-expanded')){$('.studio-expanded').classList.remove('studio-expanded');$('#expandStudio').textContent='Mở rộng';$('#expandStudio').setAttribute('aria-label','Mở rộng workspace');requestAnimationFrame(fit);}});
  function fit() {
    if(view!=='proposal'||!$('#canvasViewport'))return;
    if(!state.nodes.length){zoom(1);return;}
    const maxX=Math.max(...state.nodes.map(n=>n.x+290))+40,maxY=Math.max(...state.nodes.map(n=>n.y+220))+40;
    const v=$('#canvasViewport');zoom(Math.min(1.05,Math.max(.35,Math.min(v.clientWidth/maxX,v.clientHeight/maxY))));v.scrollLeft=0;v.scrollTop=0;
  }
  function setInspector(open){inspectorOpen=open;$('.studio-workarea').classList.toggle('inspector-open',open);$('#toggleInspector').textContent=open?'Đóng nội dung':'Nội dung node';$('#toggleInspector').setAttribute('aria-expanded',String(open));if(open)inspect();}
  function arrange(){if(state.busy)return;const levels=new Map();function level(id,seen=new Set()){if(levels.has(id))return levels.get(id);if(seen.has(id))return 0;const next=new Set(seen);next.add(id);const incoming=state.edges.filter(e=>e.to===id&&get(e.from));const value=incoming.length?1+Math.max(...incoming.map(e=>level(e.from,next))):0;levels.set(id,value);return value;}const counts=new Map();for(const node of state.nodes){const col=level(node.id),row=counts.get(col)||0;node.x=60+col*370;node.y=60+row*265;counts.set(col,row+1);}dirty();draw();fit();}
  function zoom(value,cx,cy) {const v=$('#canvasViewport'),rect=v.getBoundingClientRect(),px=cx==null?v.clientWidth/2:cx-rect.left,py=cy==null?v.clientHeight/2:cy-rect.top,wx=(v.scrollLeft+px)/state.scale,wy=(v.scrollTop+py)/state.scale;state.scale=Math.max(.25,Math.min(2,value));draw();v.scrollLeft=wx*state.scale-px;v.scrollTop=wy*state.scale-py;}
  function minimap(maxX,maxY){const map=$('#studioMinimap');if(!map)return;map.innerHTML=`<span>TOÀN BỘ LUỒNG</span><svg viewBox="0 0 ${maxX} ${maxY}" role="group" aria-label="Đi đến node">${state.edges.map(e=>{const a=get(e.from),b=get(e.to);return a&&b?`<line x1="${a.x+280}" y1="${a.y+100}" x2="${b.x}" y2="${b.y+100}"/>`:'';}).join('')}${state.nodes.map(n=>`<rect data-map-node="${esc(n.id)}" x="${n.x}" y="${n.y}" width="280" height="210" rx="18" tabindex="0" role="button" aria-label="Đi đến ${esc(n.title)}" class="map-${n.type} ${n.id===state.selected?'selected':''}"/>`).join('')}</svg>`;map.querySelectorAll('[data-map-node]').forEach(el=>{const go=()=>{const n=get(el.dataset.mapNode),v=$('#canvasViewport');state.selected=n.id;if(state.scale<.65)zoom(.85);else draw();if(inspectorOpen)inspect();v.scrollLeft=(n.x+140)*state.scale-v.clientWidth/2;v.scrollTop=(n.y+105)*state.scale-v.clientHeight/2;};el.onclick=go;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}};});}

  function draw() {
    if(!$('#nodeLayer'))return;
    const maxX=Math.max(1350,...state.nodes.map(n=>n.x+340)),maxY=Math.max(850,...state.nodes.map(n=>n.y+260));
    $('#canvasSizer').style.width=maxX*state.scale+'px';$('#canvasSizer').style.height=maxY*state.scale+'px';
    const canvas=$('#nodeCanvas');canvas.style.width=maxX+'px';canvas.style.height=maxY+'px';canvas.style.transform=`scale(${state.scale})`;
    $('#zoomLabel').textContent=Math.round(state.scale*100)+'%';minimap(maxX,maxY);
    $('#nodeLayer').innerHTML=state.nodes.map(n=>`<article class="flow-node node-${n.type} ${n.id===state.selected?'selected':''}" data-node="${esc(n.id)}" tabindex="0" role="button" aria-label="Mở ${esc(n.title)}"><div class="node-heading" data-drag="${esc(n.id)}"><span class="node-icon">${icons[n.type]}</span><span>${labels[n.type]}</span><small>⋮⋮</small><button class="node-delete" data-delete-node="${esc(n.id)}" aria-label="Xóa ${esc(n.title)}" title="Xóa node">×</button></div><div class="node-preview"><strong>${esc(n.title)}</strong>${n.type==='template'&&n.libraryMode?`<div class=library-node-count>${TemplateLibrary.entries(records).length}<small>thư tham khảo</small></div><p>Tự tìm mẫu phù hợp với mô tả job · Mở node để xem kho.</p><span class=won-tag>${n.librarySelectionMode==='manual'?'Tôi chọn mẫu · '+(n.librarySelected||[]).length+' thư':'AI tự chắt lọc'}</span>${n.libraryPinned?.length?`<span class=won-tag>${n.libraryPinned.length} mẫu ghim</span>`:''}`:n.type==='review'?n.evaluation?`<div class="node-score">${n.evaluation.score}<small>/100</small><span>${stale(n)?'Cần chấm lại':'Đã đánh giá'}</span></div><p>${esc(n.evaluation.summary.slice(0,95))}</p>`:'<div class="node-score muted">—<small>/100</small></div><p>Chấm điểm, điểm mạnh, điểm yếu và hướng cải thiện.</p>':`<p>${esc((n.content||'Bấm để nhập nội dung hoặc chọn từ thư viện.').slice(0,145))}</p>${n.sourceOutcome==='won'?'<span class="won-tag">✓ Từng có hợp đồng</span>':''}`}</div><button class="port port-in" data-port-in="${esc(n.id)}" aria-label="Nối vào ${labels[n.type]}">●</button><button class="port port-out" data-port-out="${esc(n.id)}" aria-label="Nối ra ${labels[n.type]}">●</button></article>`).join('');
    document.querySelectorAll('[data-node]').forEach(el=>{const n=get(el.dataset.node);el.style.left=n.x+'px';el.style.top=n.y+'px';});
    const svg=$('#connections');svg.setAttribute('width',maxX);svg.setAttribute('height',maxY);
    svg.innerHTML=`<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#85988e"/></marker></defs>`+state.edges.map((edge,i)=>{const path=edgePath(edge);return path?`<g class="edge-group"><path class="flow-edge" data-edge-line="${i}" d="${path}" marker-end="url(#arrow)"/><path class="edge-hit" data-edge="${i}" d="${path}" tabindex="0" role="button" aria-label="Bỏ kết nối ${esc(get(edge.from)?.title)} đến ${esc(get(edge.to)?.title)}"><title>Bấm để bỏ nối · có thể Hoàn tác</title></path><g class="edge-delete" data-delete-edge="${i}" role="button" tabindex="0" aria-label="Bỏ nối ${esc(get(edge.from)?.title)} đến ${esc(get(edge.to)?.title)}"><circle r="14"/><text text-anchor="middle" dominant-baseline="central">×</text></g></g>`:'';}).join('');
    document.querySelectorAll('[data-delete-node]').forEach(b=>{b.onpointerdown=e=>e.stopPropagation();b.onclick=e=>{e.stopPropagation();deleteNode(b.dataset.deleteNode);};});
    svg.querySelectorAll('[data-edge]').forEach(path=>{path.onclick=e=>{e.stopPropagation();removeEdge(Number(path.dataset.edge));};path.onkeydown=e=>{if(['Enter',' ','Delete','Backspace'].includes(e.key)){e.preventDefault();removeEdge(Number(path.dataset.edge));}};});
    document.querySelectorAll('[data-node]').forEach(el=>el.onclick=e=>{if(e.target.closest('[data-port-in],[data-port-out],[data-delete-node]'))return;state.selected=el.dataset.node;setInspector(true);draw();inspect();});
    document.querySelectorAll('[data-node]').forEach(el=>el.onkeydown=e=>{if(e.target!==el)return;if(e.key==='Enter'||e.key===' '){e.preventDefault();state.selected=el.dataset.node;setInspector(true);draw();inspect();}});
    svg.querySelectorAll('[data-delete-edge]').forEach(button=>{button.onclick=e=>{e.stopPropagation();removeEdge(Number(button.dataset.deleteEdge));};button.onkeydown=e=>{if(['Enter',' ','Delete','Backspace'].includes(e.key)){e.preventDefault();e.stopPropagation();removeEdge(Number(button.dataset.deleteEdge));}};});
    updateEdges();
    document.querySelectorAll('[data-port-out]').forEach(el=>el.onclick=e=>{e.stopPropagation();connecting=el.dataset.portOut;$('#connectionHint').textContent='Chọn cổng vào ● của node đích';});
    document.querySelectorAll('[data-port-in]').forEach(el=>el.onclick=e=>{e.stopPropagation();if(connecting){connect(connecting,el.dataset.portIn);connecting=null;}});
    document.querySelectorAll('[data-port-out]').forEach(el=>el.onpointerdown=event=>{
      if(event.button!==0||state.busy)return;event.stopPropagation();const from=el.dataset.portOut,a=get(from),sx=event.clientX,sy=event.clientY;let moved=false;
      const ghost=document.createElementNS('http://www.w3.org/2000/svg','path');ghost.setAttribute('class','flow-edge flow-edge-preview');$('#connections').append(ghost);
      const move=e=>{if(Math.hypot(e.clientX-sx,e.clientY-sy)<5&&!moved)return;moved=true;const rect=$('#nodeCanvas').getBoundingClientRect(),x=a.x+280,y=a.y+100,tx=(e.clientX-rect.left)/state.scale,ty=(e.clientY-rect.top)/state.scale,d=Math.max(65,Math.abs(tx-x)/2);ghost.setAttribute('d',`M ${x} ${y} C ${x+d} ${y}, ${tx-d} ${ty}, ${tx} ${ty}`);};
      const stop=e=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',stop);document.removeEventListener('pointercancel',cancel);ghost.remove();if(moved){const target=document.elementFromPoint(e.clientX,e.clientY)?.closest('[data-port-in]');if(target)connect(from,target.dataset.portIn);connecting=null;}};
      const cancel=()=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',stop);document.removeEventListener('pointercancel',cancel);ghost.remove();connecting=null;};
      document.addEventListener('pointermove',move);document.addEventListener('pointerup',stop);document.addEventListener('pointercancel',cancel);
    });
    document.querySelectorAll('[data-drag]').forEach(el=>el.onpointerdown=event=>{
      if(event.button!==0||event.target.closest('[data-delete-node]'))return;event.preventDefault();const n=get(el.dataset.drag);state.selected=n.id;inspect();const x=event.clientX,y=event.clientY,sx=n.x,sy=n.y;let moved=false;
      const move=e=>{n.x=Math.max(0,sx+(e.clientX-x)/state.scale);n.y=Math.max(0,sy+(e.clientY-y)/state.scale);moved=true;const card=document.querySelector(`[data-node="${n.id}"]`);card.style.left=n.x+'px';card.style.top=n.y+'px';updateEdges();};
      const stop=()=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',stop);document.removeEventListener('pointercancel',stop);if(moved)dirty();else setInspector(true);draw();};
      document.addEventListener('pointermove',move);document.addEventListener('pointerup',stop);document.addEventListener('pointercancel',stop);
    });
  }
  function edgePath(e){const a=get(e.from),b=get(e.to);if(!a||!b)return '';const x=a.x+280,y=a.y+100,tx=b.x,ty=b.y+100,d=Math.max(65,Math.abs(tx-x)/2);if(state.edgeStyle==='straight')return `M ${x} ${y} L ${tx} ${ty}`;if(state.edgeStyle==='step'){const mid=(x+tx)/2;return `M ${x} ${y} L ${mid} ${y} L ${mid} ${ty} L ${tx} ${ty}`;}return `M ${x} ${y} C ${x+d} ${y}, ${tx-d} ${ty}, ${tx} ${ty}`;}
  function updateEdges(){state.edges.forEach((edge,i)=>{const line=$(`#connections [data-edge-line="${i}"]`);line?.setAttribute('d',edgePath(edge));$(`#connections [data-edge="${i}"]`)?.setAttribute('d',edgePath(edge));if(line){const point=line.getPointAtLength(line.getTotalLength()/2);$(`#connections [data-delete-edge="${i}"]`)?.setAttribute('transform',`translate(${point.x},${point.y})`);}});}

  function checkpoint(){undoGraph={nodes:clone(state.nodes),edges:clone(state.edges),selected:state.selected};if($('#undoGraph'))$('#undoGraph').disabled=false;}
  function deleteNode(id){if(state.busy)return notice('Đợi AI hoàn thành trước khi xóa node.');if(!get(id))return;checkpoint();state.nodes=state.nodes.filter(n=>n.id!==id);state.edges=state.edges.filter(e=>e.from!==id&&e.to!==id);if(state.selected===id)state.selected=state.nodes[0]?.id||null;connecting=null;dirty();draw();inspect();notice('Đã xóa node và đường nối liên quan. Bấm Hoàn tác nếu xóa nhầm.');}
  function removeEdge(index){if(state.busy)return notice('Đợi AI hoàn thành trước khi bỏ nối.');if(!state.edges[index])return;checkpoint();state.edges.splice(index,1);connecting=null;dirty();draw();inspect();notice('Đã bỏ nối. Bấm Hoàn tác nếu bỏ nhầm.');}

  function connect(from,to) {
    if(state.busy)return notice('Đợi AI hoàn thành trước khi thay đổi kết nối.');
    const a=get(from),b=get(to);if(!a||!b||from===to)return notice('Chọn hai node khác nhau.');
    const allowed={job:['draft','final'],template:['draft','final'],draft:['review','final'],review:['final'],final:['review']};
    if(!allowed[a.type].includes(b.type))return notice('Hai loại node này không có luồng dữ liệu phù hợp.');
    if(ancestors(from).some(n=>n.id===to))return notice('Kết nối này tạo vòng lặp. Hãy chọn luồng một chiều.');
    if(state.edges.length>=100)return notice('Workspace hỗ trợ tối đa 100 kết nối.');
    if(!state.edges.some(e=>e.from===from&&e.to===to)){state.edges.push({from,to});dirty();}draw();inspect();
    $('#connectionHint').textContent='Đã nối node. Bấm đường nối hoặc dấu × để bỏ nối.';return true;
  }
  function freePosition() {
    for(let y=65;y<19000;y+=290)for(let x=45;x<=1405;x+=340){
      const overlaps=state.nodes.some(n=>x<n.x+300&&x+300>n.x&&y<n.y+230&&y+230>n.y);
      if(!overlaps)return {x,y};
    }
    return {x:45,y:Math.max(...state.nodes.map(n=>n.y))+290};
  }
  function addNode(type) {
    if(state.busy)return;
    if(state.nodes.length>=30)return notice('Workspace hỗ trợ tối đa 30 node.');
    const node={id:unique(),type,...freePosition(),title:labels[type],content:'',...(type==='template'?{libraryMode:true,libraryExcluded:[],libraryPinned:[]}: {})};
    state.nodes.push(node);state.selected=node.id;inspectorOpen=true;dirty();renderStudio();document.querySelector(`[data-node="${node.id}"]`).scrollIntoView({block:'nearest',inline:'nearest'});
  }
  function inspect() {
    const node=get(state.selected);if(!node){$('#nodeInspector').innerHTML='<div class=inspector-fields>Chưa có node. Chọn loại node ở thanh công cụ để bắt đầu.</div>';return;}const up=state.edges.filter(e=>e.to===node.id);
    let content=field('Tên node','nodeTitle',node.title);
    if(node.type==='job')content+=choice('Chọn job đã lưu','nodeJob',[['','Nhập job thủ công'],...records.filter(r=>r.kind==='job').map(r=>[r.id,r.name])],node.jobId)+area('Yêu cầu / mô tả công việc','nodeContent',node.content)+field('Ngân sách của job','nodeBudget',node.budget);
    if(node.type==='template') {
      content+=choice('Cách tham khảo mẫu','librarySelectionMode',[['auto','AI tự chắt lọc'],['manual','Tôi chọn mẫu']],node.librarySelectionMode||'auto');
      content+=`<div class=library-node-summary><strong>${TemplateLibrary.entries(records).length} thư trong kho</strong><p>AI viết theo job, tham khảo các mẫu liên quan. Bạn có thể ghim hoặc bỏ qua mẫu.</p><button type=button id=openTemplateLibrary class=primary>Mở kho mẫu</button><label class=library-check><input type=checkbox id=useTemplateLibrary ${node.libraryMode?'checked':''}> Tự tìm mẫu trong toàn bộ kho</label></div>`;
      const sources=[...records.filter(r=>r.kind==='template').map(r=>['t-'+r.id,r.name]),...records.filter(r=>r.kind==='sentproposal').map(r=>['s-'+r.id,(r.outcome==='won'?'✓ Có hợp đồng · ':'')+r.name])];
      content+=choice('Thêm mẫu từ thư viện / thư đã gửi','templateSource',[['','Chọn thư tham khảo…'],...sources],'')+area('Khung / nội dung mẫu','nodeContent',node.content)+`<p class="hint">${node.sourceOutcome==='won'?'Mẫu này từng đi cùng một hợp đồng thành công. ':''}Dùng làm tham khảo cấu trúc; thông tin và giá cần phù hợp job mới.</p><button type="button" id="saveTemplate">Lưu thành mẫu dùng lại</button>`;
    }
    if(node.referenceSynthesis)content+=`<details class=library-synthesis open><summary>AI đã chắt lọc ${node.referenceSynthesis.readCount} thư</summary><p>${esc(node.referenceSynthesis.plan||'Không có mẫu đầu vào; viết theo job và hồ sơ.')}</p></details>`;
    if(['draft','final'].includes(node.type)&&node.referenceShortlist?.length)content+=`<details class=library-reference-history><summary>Mẫu đã cung cấp khi viết · ${node.referenceShortlist.length}</summary>${node.referenceShortlist.map(r=>`<p><strong>${esc(r.name)}</strong><small>${esc(r.reason)}</small></p>`).join('')}<p class=hint>Đây là mẫu đầu vào, không khẳng định AI dùng mọi mẫu.</p></details>`;
    if(node.type==='draft')content+=area('Cách giải quyết / kinh nghiệm','nodeApproach',node.approach)+field('Giá đề xuất','nodeBudget',node.budget)+field('Thời gian','nodeTimeline',node.timeline)+field('Tên ký thư','nodeSignature',node.signature)+choice('Ngôn ngữ','nodeLanguage',[['English','Tiếng Anh'],['Vietnamese','Tiếng Việt']],node.language||'English')+area('Ý muốn của tôi','nodeInstructions',node.instructions)+`<div class=writing-presets><button data-writing-preset="Viết ngắn gọn, đi thẳng vào giải pháp.">Ngắn gọn</button><button data-writing-preset="Mở đầu bằng vấn đề cụ thể của khách.">Đi thẳng vấn đề</button><button data-writing-preset="Kết thúc bằng một câu hỏi rõ ràng để khách trả lời.">Câu hỏi kết thúc</button></div>`+`<button type="button" id="runNodeAI" class="primary">✦ Chắt lọc & viết nháp</button>`+area('Bản nháp có thể chỉnh sửa','nodeContent',node.content);
    if(node.type==='review') {
      const review=node.evaluation;
      content+=`<p class="hint">Chấm thư ở node được nối vào, đối chiếu yêu cầu job và hồ sơ của bạn.</p><button type="button" id="runNodeAI" class="primary">✦ Chấm điểm thư</button>`;
      if(review)content+=`<div class="review-score">${review.score}<span>/100</span></div>${stale(node)?'<p class="review-stale">Nội dung đầu vào đã đổi. Cần chấm lại trước khi dùng kết quả này.</p>':''}<p class="hint">${esc(review.summary)}</p>${review.criteria.map(c=>`<div class="review-criterion"><div><span>${esc(c.name)}</span><strong>${c.score}/100</strong></div><meter min="0" max="100" value="${c.score}"></meter><p>${esc(c.reason)}</p></div>`).join('')}${[['Điểm mạnh','strengths'],['Điểm yếu','weaknesses'],['Đề xuất sửa','suggestions']].map(([label,key])=>`<h3 class="review-label">${label}</h3><ul class="review-list">${review[key].map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`).join('')}`;
      else content+='<div class="review-empty">Chưa có điểm đánh giá.<br>Viết bản nháp rồi chấm để xem phản hồi.</div>';
    }
    if(node.type==='final')content+=`<div class="final-tools"><button type="button" id="copyDraftToFinal">Lấy nội dung thư nháp</button><button type="button" id="runNodeAI" class="primary">✦ Hoàn thiện theo đánh giá</button></div>`+area('Nội dung thư cuối','nodeContent',node.content)+`<button type="button" id="copyFinal">Sao chép thư</button><button type="button" id="archiveFinal" class="primary">Tôi đã gửi → Lưu vào kho</button><p class="hint">Chỉ ghi nhận sau khi bạn gửi trên Upwork. Kho sẽ giữ nguyên nội dung của lần gửi này.</p>`;
    if(['draft','final'].includes(node.type))content+=`<div class=writing-tools><button id=focusWriting>${$('.studio-workarea')?.classList.contains('writing-focus')?'Quay lại node':'Tập trung viết'}</button><button id=saveDraftVersion>Lưu phiên bản</button></div><details class=writing-versions><summary>Phiên bản đã lưu · ${(node.versions||[]).length}</summary>${(node.versions||[]).map((v,i)=>`<div><span>${esc(v.label)} · ${esc(new Date(v.at).toLocaleString('vi-VN'))}</span><button data-restore-version=${i}>Khôi phục</button></div>`).join('')||'<p>Chưa có phiên bản. Bản hiện tại tự được giữ lại trước khi AI sửa.</p>'}</details><label>Muốn sửa đoạn đã chọn thế nào?<input id=paragraphInstruction placeholder="Ví dụ: gọn hơn, bớt sáo rỗng"></label><button id=rewriteParagraph>✦ Sửa đoạn bôi đen</button><p class=hint>Bôi đen đoạn trong ô thư rồi bấm sửa. Những đoạn khác được giữ nguyên.</p>`;
    content+=`<div class="node-inputs"><h3>Node đầu vào (${up.length})</h3>${up.map(e=>`<div><span>${esc(get(e.from)?.title || '')}</span><button type="button" data-disconnect="${esc(e.from)}" aria-label="Bỏ kết nối">×</button></div>`).join('')}${choice('Nối thêm đầu vào','connectSource',[['','Chọn node…'],...state.nodes.filter(n=>n.id!==node.id).map(n=>[n.id,labels[n.type]+' · '+n.title])],'')}</div><button type="button" id="deleteNode" class="delete-node">Xóa node này</button>`;
    $('#nodeInspector').className='node-inspector inspector-'+node.type;
    $('#nodeInspector').innerHTML=`<div class="inspector-heading"><span>${icons[node.type]} ${labels[node.type]}</span><button type="button" id="closeNodeInspector" aria-label="Đóng nội dung node">✕</button></div><div class="inspector-fields">${content}<p id="nodeMessage" role="status"></p></div>`;
    // Put the letter first; reveal secondary controls only when needed.
    const fields=$('#nodeInspector .inspector-fields');
    function fold(title,els,klass){const d=document.createElement('details');d.className='editor-section '+(klass||'');const summary=document.createElement('summary');summary.textContent=title;d.append(summary);const body=document.createElement('div');body.className='editor-section-body';d.append(body);els.filter(Boolean).forEach(el=>body.append(el));return d;}
    const titleField=$('[name=nodeTitle]')?.closest('label');
    const inputs=$('.node-inputs'),deleteButton=$('#deleteNode');
    const connections=fold('Kết nối & quản lý node · '+up.length,[titleField,inputs,deleteButton],'editor-connections');
    fields.append(connections);
    if(['draft','final'].includes(node.type)){
      const letter=$('[name=nodeContent]').closest('label');letter.classList.add('letter-editor');
      const tools=$('.writing-tools'),focus=$('#focusWriting');
      const head=document.createElement('div');head.className='letter-editor-head';head.innerHTML='<strong>'+ (node.type==='final'?'Thư sẵn sàng gửi':'Soạn thư báo giá')+'</strong>';head.append(focus);
      const versions=$('.writing-versions');versions.classList.add('editor-section');
      const versionBody=document.createElement('div');versionBody.className='editor-section-body';
      [...versions.children].filter(el=>el.tagName!=='SUMMARY').forEach(el=>versionBody.append(el));versionBody.prepend($('#saveDraftVersion'));versions.append(versionBody);
      const rewrite=$('#rewriteParagraph'),rewriteLabel=$('#paragraphInstruction').closest('label'),hint=rewrite.nextElementSibling;
      const rewriteSection=fold('✦ Sửa một đoạn với AI',[rewriteLabel,rewrite,hint],'editor-rewrite');
      let options;
      if(node.type==='draft'){
        const controls=['nodeApproach','nodeBudget','nodeTimeline','nodeSignature','nodeLanguage','nodeInstructions'].map(name=>$('[name='+name+']')?.closest('label'));
        options=fold('Yêu cầu viết & thông tin báo giá',[...controls,$('.writing-presets')],'editor-options');
      }else options=fold('Lấy nháp & hoàn thiện bằng AI',[$('.final-tools')],'editor-options');
      const research=[$('.library-synthesis'),$('.library-reference-history')].filter(Boolean);
      const references=research.length?fold('Nguồn tham khảo & chắt lọc',research,'editor-references'):null;
      const actions=document.createElement('div');actions.className='letter-primary-actions';
      if(node.type==='final'){const note=$('#archiveFinal').nextElementSibling;actions.append($('#copyFinal'),$('#archiveFinal'));if(note?.classList.contains('hint'))actions.append(note);}
      else actions.append($('#runNodeAI'));
      tools.remove();
      fields.prepend(head,letter,actions,rewriteSection,versions,options,...(references?[references]:[]));
    }
    $('#closeNodeInspector').onclick=()=>setInspector(false);
    if($('[name=librarySelectionMode]'))$('[name=librarySelectionMode]').onchange=e=>{node.librarySelectionMode=e.target.value;node.libraryMode=true;dirty();draw();inspect();};
    if($('#openTemplateLibrary'))$('#openTemplateLibrary').onclick=()=>library(node);
    if($('#useTemplateLibrary'))$('#useTemplateLibrary').onchange=e=>{node.libraryMode=e.target.checked;dirty();draw();};
    const mapping={nodeTitle:'title',nodeContent:'content',nodeApproach:'approach',nodeBudget:'budget',nodeTimeline:'timeline',nodeSignature:'signature',nodeLanguage:'language',nodeInstructions:'instructions'};
    for(const [name,key]of Object.entries(mapping)){const el=$(`[name=${name}]`);if(el)el.oninput=()=>{node[key]=el.value;dirty();draw();};}
    if($('[name=nodeJob]'))$('[name=nodeJob]').onchange=e=>{const r=records.find(r=>r.kind==='job'&&String(r.id)===e.target.value);node.jobId=r?.id||'';if(r){node.title=r.name;node.content=r.notes||'';node.budget=r.budget||'';state.record.jobId=r.id;state.record.clientId=r.clientId||'';}dirty();draw();inspect();};
    if($('[name=templateSource]'))$('[name=templateSource]').onchange=e=>{const id=Number(e.target.value.slice(2)),r=records.find(r=>r.id===id);if(r){node.content=r.body||'';node.title=r.name;node.sourceId=r.id;node.sourceOutcome=r.outcome||'';dirty();draw();inspect();}};
    $('[name=connectSource]').onchange=e=>{if(e.target.value)connect(e.target.value,node.id);};
    document.querySelectorAll('[data-disconnect]').forEach(b=>b.onclick=()=>{if(state.busy)return;checkpoint();state.edges=state.edges.filter(e=>!(e.from===b.dataset.disconnect&&e.to===node.id));dirty();draw();inspect();});
    $('#deleteNode').onclick=()=>deleteNode(node.id);
    document.querySelectorAll('[data-writing-preset]').forEach(b=>b.onclick=()=>{node.instructions=[node.instructions,b.dataset.writingPreset].filter(Boolean).join('\n');dirty();inspect();});
    if($('#focusWriting'))$('#focusWriting').onclick=()=>{const area=$('.studio-workarea');area.classList.toggle('writing-focus');$('#focusWriting').textContent=area.classList.contains('writing-focus')?'Quay lại node':'Tập trung viết';};
    if($('#saveDraftVersion'))$('#saveDraftVersion').onclick=()=>{remember(node,'Lưu thủ công');dirty();inspect();};
    document.querySelectorAll('[data-restore-version]').forEach(b=>b.onclick=()=>{const v=node.versions[Number(b.dataset.restoreVersion)];if(!v)return;const restored=JSON.parse(JSON.stringify(v));remember(node,'Trước khôi phục');node.content=restored.content;node.referenceShortlist=restored.referenceShortlist;node.referenceSynthesis=restored.referenceSynthesis;dirty();draw();inspect();});
    if($('#rewriteParagraph'))$('#rewriteParagraph').onclick=()=>rewriteParagraph(node);
    if($('#runNodeAI'))$('#runNodeAI').onclick=()=>runAI(node);
    if($('#copyDraftToFinal'))$('#copyDraftToFinal').onclick=()=>{const c=context(node);if(!c.existingDraft)return notice('Nối node thư nháp hoặc AI đánh giá vào thư cuối.');if(node.content&&!confirm('Thay nội dung thư cuối bằng thư nháp?'))return;remember(node,'Trước lấy nháp');node.content=c.existingDraft;dirty();draw();inspect();};
    if($('#copyFinal'))$('#copyFinal').onclick=async()=>{try{await navigator.clipboard.writeText(node.content||'');notice('Đã sao chép thư cuối.');}catch{notice('Chọn nội dung thư để sao chép thủ công.');}};
    if($('#archiveFinal'))$('#archiveFinal').onclick=()=>sendSnapshot(node);
    if($('#saveTemplate'))$('#saveTemplate').onclick=async()=>{if(!node.content?.trim())return notice('Nhập nội dung mẫu trước khi lưu.');try{await post('/api/records',{kind:'template',name:node.title,body:node.content,sourceId:node.sourceId||'',sourceOutcome:node.sourceOutcome||''});await refresh();notice('Đã lưu mẫu; bạn có thể thêm vào workspace khác.');}catch(e){notice(e.message);}};
    if(state.busy)$('#nodeInspector').querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=true);
  }
  function library(node){
    if(!node.libraryMode){node.libraryMode=true;dirty();draw();}
    let dialog=$('#templateLibraryDialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='templateLibraryDialog';dialog.className='template-library-dialog';document.body.append(dialog);}dialog.setAttribute('aria-label','Kho mẫu tham khảo');let query='',source='all',limit=30;
    function paint(){const refs=TemplateLibrary.entries(records),target=state.edges.filter(e=>e.from===node.id).map(e=>get(e.to)).find(n=>n?.type==='draft'||n?.type==='final'),up=target?ancestors(target.id).filter(n=>n.type==='job'):[],selection=TemplateLibrary.choose(records,[node],up.map(n=>n.title+' '+n.content).join(' ')),manual=node.librarySelectionMode==='manual',picked=new Set(node.librarySelected||[]),available=refs.filter(r=>manual?picked.has(r.id):!(node.libraryExcluded||[]).includes(r.id)),excluded=new Set(node.libraryExcluded||[]),pinned=new Set(node.libraryPinned||[]),filtered=refs.filter(r=>(source==='all'||source==='won'&&r.outcome==='won'||r.source===source)&&(r.name+' '+r.body).toLowerCase().includes(query.toLowerCase()));
    dialog.innerHTML=`<div class=library-dialog-head><div><span class=eyebrow>MỘT KHO · NHIỀU THƯ THAM KHẢO</span><h2>Kho mẫu tham khảo <small>${refs.length}</small></h2><p>Lưu nhiều mẫu; mỗi lần viết chỉ lấy một nhóm liên quan với job.</p></div><button id=closeTemplateLibrary aria-label="Đóng kho mẫu">×</button></div><div class=library-mode-tabs role=group aria-label="Cách chọn mẫu"><button data-library-mode=auto aria-pressed="${!manual}">AI tự chắt lọc</button><button data-library-mode=manual aria-pressed="${manual}">Tôi chọn mẫu</button></div><div class=library-dialog-grid><section><div class=library-search><input id=librarySearch aria-label="Tìm mẫu thư" placeholder="Tìm tên hoặc nội dung mẫu…" value="${esc(query)}"><select id=librarySource aria-label="Nguồn mẫu">${[['all','Tất cả nguồn'],['sentproposal','Thư đã gửi'],['template','Mẫu lưu riêng'],['won','Từng có hợp đồng']].map(([id,label])=>`<option value=${id} ${id===source?'selected':''}>${label}</option>`).join('')}</select></div><div class=library-list>${filtered.slice(0,limit).map(r=>`<article class="library-letter ${(manual?!picked.has(r.id):excluded.has(r.id))?'excluded':''}"><div><h3>${esc(r.name)}</h3><span>${r.source==='sentproposal'?'Thư đã gửi':'Mẫu lưu riêng'}${r.outcome==='won'?' · Có hợp đồng':''}</span></div><div class=library-letter-actions><label><input type=checkbox data-library-use="${r.id}" ${(manual?picked.has(r.id):!excluded.has(r.id))?'checked':''}>${manual?'Chọn':'Cho đọc'}</label><button data-library-pin="${r.id}" aria-pressed="${pinned.has(r.id)}">${pinned.has(r.id)?'★ Đã ghim':'☆ Ghim'}</button></div><details><summary>Xem nội dung</summary><p>${esc(r.body)}</p></details></article>`).join('')||'<p class=library-empty>Chưa có mẫu phù hợp. Thêm mẫu ngoài hoặc lưu thư đã gửi vào kho.</p>'}</div>${filtered.length>limit?'<button id=moreLibraryLetters>Xem thêm mẫu</button>':''}<details class=library-add-form><summary>+ Thêm mẫu từ bên ngoài</summary><label>Tên mẫu<input id=externalTemplateName maxlength=1000></label><label>Nội dung thư<textarea id=externalTemplateBody></textarea></label><button id=saveExternalTemplate class=primary>Lưu vào kho</button><p id=externalTemplateError role=status></p></details></section><div class=library-selection role=complementary><span class=eyebrow>JOB → CHẮT LỌC → THƯ NHÁP</span><h3>${manual?'Bạn chọn '+available.length+' thư':'AI sẽ đọc '+available.length+' thư trong kho'}</h3><p>${manual?'AI chỉ đọc những thư bạn tích chọn, tổng hợp điểm phù hợp từ nhiều mẫu rồi viết.':'AI đọc các thư được cho phép theo từng nhóm, tổng hợp điểm phù hợp với job rồi viết thư mới.'}</p><strong class=library-mode-job>${esc(up[0]?.title||'Chưa nối thông tin job')}</strong>${manual?available.slice(0,20).map(r=>`<article><strong>${esc(r.name)}</strong></article>`).join(''): '<ol><li>Đối chiếu mô tả công việc.</li><li>Chắt lọc cách mở đầu, giải pháp và câu hỏi kết thúc.</li><li>Viết nháp bằng thông tin thật của bạn.</li></ol>'}<small>${manual?'Không bắt buộc chọn đúng 3–4 mẫu.':'Không chỉ chọn một thư và không dừng ở 8 mẫu. Kho lớn được xử lý theo nhiều nhóm.'}</small><button id=libraryWriteDraft class=primary>Chắt lọc & viết nháp</button><p id=libraryWriteError role=status></p></div></div>`;
    dialog.querySelectorAll('[data-library-mode]').forEach(button=>button.onclick=()=>{node.librarySelectionMode=button.dataset.libraryMode;node.libraryMode=true;dirty();paint();draw();});
    $('#libraryWriteDraft').onclick=()=>{if(manual&&!available.length){$('#libraryWriteError').textContent='Tích chọn ít nhất một mẫu.';return;}if(!target){$('#libraryWriteError').textContent='Nối kho mẫu vào node viết nháp trước.';return;}dialog.close();state.selected=target.id;setInspector(true);draw();inspect();runAI(target);};
    $('#closeTemplateLibrary').onclick=()=>{dialog.close();draw();inspect();};$('#librarySearch').oninput=e=>{query=e.target.value;const cursor=e.target.selectionStart;paint();$('#librarySearch').focus();$('#librarySearch').setSelectionRange(cursor,cursor);};$('#librarySource').onchange=e=>{source=e.target.value;paint();};if($('#moreLibraryLetters'))$('#moreLibraryLetters').onclick=()=>{limit+=30;paint();};
    dialog.querySelectorAll('[data-library-use]').forEach(input=>input.onchange=()=>{if(manual){const ids=new Set(node.librarySelected||[]);if(input.checked)ids.add(input.dataset.libraryUse);else ids.delete(input.dataset.libraryUse);node.librarySelected=[...ids];}else{const ids=new Set(node.libraryExcluded||[]);if(input.checked)ids.delete(input.dataset.libraryUse);else ids.add(input.dataset.libraryUse);node.libraryExcluded=[...ids];if(!input.checked)node.libraryPinned=(node.libraryPinned||[]).filter(id=>id!==input.dataset.libraryUse);}node.libraryMode=true;dirty();paint();draw();});
    dialog.querySelectorAll('[data-library-pin]').forEach(button=>button.onclick=()=>{const values=new Set(node.libraryPinned||[]),id=button.dataset.libraryPin;if(values.has(id))values.delete(id);else values.add(id);node.libraryPinned=[...values];node.libraryExcluded=(node.libraryExcluded||[]).filter(v=>v!==id);node.libraryMode=true;dirty();paint();draw();});
    $('#saveExternalTemplate').onclick=async()=>{const name=$('#externalTemplateName').value.trim(),body=$('#externalTemplateBody').value.trim();if(!name||!body){$('#externalTemplateError').textContent='Nhập tên mẫu và nội dung thư.';return;}const button=$('#saveExternalTemplate');button.disabled=true;try{await post('/api/records',{kind:'template',name,body});await refresh();node.libraryMode=true;dirty();paint();draw();}catch(error){$('#externalTemplateError').textContent=error.message;button.disabled=false;}};
    }paint();dialog.showModal();
  }
  function remember(node,label){
    if(!node.content?.trim())return;
    const versions=node.versions||[];
    if(versions[0]?.content===node.content)return;
    node.versions=[{content:node.content,label,at:new Date().toISOString(),referenceShortlist:node.referenceShortlist,referenceSynthesis:node.referenceSynthesis},...versions].slice(0,12);
  }
  async function rewriteParagraph(node){
    if(state.busy)return;
    const editor=$('[name=nodeContent]'),start=editor.selectionStart,end=editor.selectionEnd;
    if(start===end)return notice('Bôi đen đoạn muốn sửa trong ô thư trước.');
    const request=$('#paragraphInstruction').value.trim();
    if(!request)return notice('Ghi ngắn gọn điều bạn muốn sửa.');
    const original=node.content||'',c=context(node),holder=state;
    state.busy=true;$('#rewriteParagraph').disabled=true;
    try{
      const result=await post('/api/ai/proposal',{requirements:c.requirements,language:c.language,instructions:request,existingDraft:original,selectedParagraph:original.slice(start,end),rewriteParagraph:true});
      if(state!==holder||node.content!==original)throw Error('Nội dung đã thay đổi; giữ nguyên thư để tránh ghi đè.');
      if(!result.body?.trim())throw Error('AI chưa trả về đoạn sửa.');
      remember(node,'Trước sửa đoạn');node.content=original.slice(0,start)+result.body+original.slice(end);dirty();notice('Đã sửa riêng đoạn chọn; bản cũ nằm trong Phiên bản đã lưu.');
    }catch(e){notice(e.message);}finally{holder.busy=false;if(state===holder&&view==='proposal'){draw();inspect();}}
  }
  async function runAI(node) {
    if(state.busy)return;
    const c=context(node);if(!c.requirements)return notice('Nối node thông tin job vào luồng này và nhập yêu cầu công việc.');
    if(node.type!=='review'&&c.referenceLibrary?.length&&c.referenceLibrary.every(x=>x.mode==='manual'&&!x.selectedIds.length)){notice('Chọn mẫu trong kho hoặc chuyển sang AI tự chắt lọc.');return;}
    if(node.type==='review'&&!c.body)return notice('Node đầu vào chưa có thư. Viết hoặc nhập bản nháp trước.');
    if(node.type==='final') {const review=ancestors(node.id).find(n=>n.type==='review');if(review&&(!review.evaluation||stale(review)))return notice('Chấm lại node AI đánh giá trước khi hoàn thiện thư.');if(!c.existingDraft)return notice('Nối thư nháp vào luồng trước khi hoàn thiện.');}
    if(node.type!=='review'&&node.content&&!confirm('Thay nội dung node này bằng bản AI mới?'))return;
    state.busy=true;inspect();const holder=state;const stamp=signature(node);$('#nodeMessage').textContent=node.type==='review'?'AI đang chấm điểm…':c.referenceLibrary?.length?'AI đang đọc kho theo nhóm, chắt lọc và viết nháp…':'AI đang viết nháp…';
    try {const result=await post(node.type==='review'?'/api/ai/review':'/api/ai/proposal',c);if(state!==holder)return;if(node.type==='review'){node.evaluation=result.review;node.inputSignature=stamp;node.reviewedAt=new Date().toISOString();}else {remember(node,'Trước AI viết');node.content=result.body;node.referenceShortlist=result.referenceShortlist||c.referenceShortlist;if(result.referenceSynthesis)node.referenceSynthesis=result.referenceSynthesis;else delete node.referenceSynthesis;}node.model=result.model;dirty();notice(node.type==='review'?'Đã chấm điểm bản thư hiện tại.':'Đã tạo nội dung AI. Hãy kiểm tra trước khi gửi.');}
    catch(e){notice(e.message);}finally{holder.busy=false;if(view==='proposal'&&state===holder){draw();inspect();}}
  }
  async function save(internal = false) {
    if(saveTask)return saveTask;
    if(state.busy&&!internal)throw Error('Đợi AI hoàn thành trước khi lưu workspace.');
    if(!state.record.name?.trim())state.record.name=$('#workspaceName')?.value?.trim()||'Proposal mới';
    const holder=state, revision=JSON.stringify({name:state.record.name,nodes:state.nodes,edges:state.edges});
    const final=state.nodes.find(n=>n.type==='final'),draft=state.nodes.find(n=>n.type==='draft'),job=state.nodes.find(n=>n.type==='job');
    const payload={...state.record,kind:'proposal',name:state.record.name,body:final?.content||draft?.content||'',requirements:job?.content||'',jobId:job?.jobId||state.record.jobId||'',workspace:{version:1,nodes:state.nodes,edges:state.edges,scale:state.scale,edgeStyle:state.edgeStyle},status:state.record.status||'Bản nháp'};
    const button=$('#saveWorkspace');if(button)button.disabled=true;
    saveTask=(async()=>{
      const saved=await post('/api/records',payload);
      if(state===holder){const changed=revision!==JSON.stringify({name:state.record.name,nodes:state.nodes,edges:state.edges});const name=state.record.name;state.record=saved;if(changed)state.record.name=name;state.dirty=changed;}
      await refresh();if($('#studioSaveState'))$('#studioSaveState').textContent=state.dirty?'Có thay đổi chưa lưu':'Đã lưu';notice('Đã lưu workspace và các kết nối.');return saved;
    })();
    try{return await saveTask;}finally{saveTask=null;if(button)button.disabled=false;}
  }
  async function sendSnapshot(node) {
    if(state.busy||saveTask)return notice('Đợi thao tác hiện tại hoàn thành.');
    if(!node.content?.trim())return notice('Thư cuối đang trống.');
    if(!confirm('Bạn đã gửi thư này trên Upwork? Lưu nguyên văn vào kho thư đã gửi.'))return;
    state.busy=true;inspect();const holder=state;
    try {await save(true);const result=await post('/api/proposals/send',{id:state.record.id,finalNodeId:node.id});await refresh();state.record.status='Đã gửi';notice(result.duplicate?'Lần gửi với nội dung này đã có trong kho.':'Đã lưu bản thư đã gửi. Cập nhật kết quả tại tab Thư đã gửi.');}
    catch(e){notice(e.message);}finally{holder.busy=false;if(view==='proposal'){draw();inspect();}}
  }
  function renderArchive() {
    const sent=records.filter(r=>r.kind==='sentproposal'),won=sent.filter(r=>r.outcome==='won').length,closed=sent.filter(r=>['won','lost'].includes(r.outcome)).length;
    const filtered=sent.filter(r=>(archiveFilter==='all'||r.outcome===archiveFilter)&&JSON.stringify(r).toLowerCase().includes(archiveSearch.toLowerCase()));
    $('#content').innerHTML=`<div class="sent-archive-heading"><div><span class="studio-kicker">PROPOSAL STUDIO / KHO THƯ</span><h2>Thư đã gửi</h2></div></div><div class="archive-stats"><div><span>Thư đã gửi</span><strong>${sent.length}</strong></div><div><span>Có hợp đồng</span><strong>${won}</strong></div><div><span>Đang chờ</span><strong>${sent.filter(r=>r.outcome==='pending').length}</strong></div><div><span>Thắng / kết quả đã chốt</span><strong>${closed?Math.round(won/closed*100)+'%':'—'}</strong><small>Chỉ tính có / không có hợp đồng</small></div></div><div class="archive-toolbar"><div>${[['all','Tất cả'],...Object.entries(outcomes)].map(([k,v])=>`<button data-outcome-filter="${k}" class="${archiveFilter===k?'active':''}">${v}</button>`).join('')}</div><input id="archiveSearch" placeholder="Tìm thư, job hoặc ghi chú…" value="${esc(archiveSearch)}"></div><div class="archive-list">${filtered.length?filtered.map(r=>`<article class="archive-card archive-result-${esc(r.outcome||'pending')}"><div class="archive-card-head"><div><span class="archive-date">${esc(new Date(r.sentAt).toLocaleDateString('vi-VN'))}</span><h3>${esc(r.name)}</h3><span class="badge outcome-${r.outcome}">${outcomes[r.outcome]||outcomes.pending}</span>${r.reviewAtSend?`<span class="badge">Điểm lúc gửi: ${r.reviewAtSend.score}/100</span>`:''}</div><button data-open-sent="${r.id}">Xem thư & kết quả</button></div><p>${esc(r.body.slice(0,230))}${r.body.length>230?'…':''}</p><div class="archive-card-bottom"><span>${esc(r.jobName||'Job nhập thủ công')}</span><button data-template-from-sent="${r.id}">+ Dùng làm node mẫu</button></div></article>`).join(''):'<div class="empty"><h2>Kho lưu từng lời chào hàng của bạn.</h2><p>Ở node Thư cuối, chọn “Tôi đã gửi” để lưu một bản nguyên văn và theo dõi kết quả.</p></div>'}</div>`;
    document.querySelectorAll('[data-outcome-filter]').forEach(b=>b.onclick=()=>{archiveFilter=b.dataset.outcomeFilter;renderArchive();});
    $('#archiveSearch').oninput=e=>{const pos=e.target.selectionStart;archiveSearch=e.target.value;renderArchive();$('#archiveSearch').focus();$('#archiveSearch').setSelectionRange(pos,pos);};
    document.querySelectorAll('[data-open-sent]').forEach(b=>b.onclick=()=>openSent(records.find(r=>r.id===Number(b.dataset.openSent))));
    document.querySelectorAll('[data-template-from-sent]').forEach(b=>b.onclick=()=>useSent(records.find(r=>r.id===Number(b.dataset.templateFromSent))));
  }
  function useSent(record) {if(state?.nodes.length>=30)return notice('Workspace hỗ trợ tối đa 30 node.');if(!state)state=fresh({name:'Proposal mới'});if(state.busy)return notice('Đợi AI hoàn thành trước khi thêm mẫu.');const node={id:unique(),type:'template',title:record.name,content:record.body,sourceId:record.id,sourceOutcome:record.outcome,...freePosition()};state.nodes.push(node);const draft=state.nodes.find(n=>n.type==='draft');if(draft)state.edges.push({from:node.id,to:draft.id});state.selected=node.id;dirty();view='proposal';render();fit();notice('Đã thêm thư đã gửi làm node mẫu, nối vào thư nháp.');}
  function openSent(record) {
    $('#formTitle').textContent='Thư đã gửi · '+record.name;
    $('#fields').innerHTML=`<p class="hint">Bản nguyên văn được giữ cố định; bạn có thể cập nhật kết quả hợp đồng.</p><label>Nội dung đã gửi<textarea readonly class="sent-body">${esc(record.body)}</textarea></label>${choice('Kết quả','sentOutcome',Object.entries(outcomes),record.outcome)}${choice('Thông tin lượt xem / phản hồi (tùy chọn)','sentInteraction',[['unknown','Chưa rõ'],['not_viewed','Chưa được xem · theo thông tin bạn có'],['viewed','Đã được xem'],['replied','Khách đã phản hồi']],record.interaction||'unknown')}${field('Giá trị hợp đồng (nếu có)','contractValue',record.contractValue)}${area('Ghi chú phản hồi / lý do','outcomeNotes',record.outcomeNotes)}<button type="button" id="saveOutcome" class="primary">Lưu kết quả</button><button type="button" id="sentAsTemplate">Dùng làm node mẫu</button>`;
    $('#editor .dialog-actions').hidden=true;$('#editor').showModal();
    $('#saveOutcome').onclick=async()=>{try{await post('/api/records',{id:record.id,kind:'sentproposal',name:record.name,outcome:$('[name=sentOutcome]').value,interaction:$('[name=sentInteraction]').value,contractValue:$('[name=contractValue]').value,outcomeNotes:$('[name=outcomeNotes]').value});await refresh();$('#editor').close();renderArchive();notice('Đã cập nhật kết quả hợp đồng.');}catch(e){notice(e.message);}};
    $('#sentAsTemplate').onclick=()=>{$('#editor').close();useSent(record);};
  }
  $('#editor').addEventListener('close',()=>{$('#editor .dialog-actions').hidden=false;});
  window.addEventListener('beforeunload',e=>{if(state?.dirty){e.preventDefault();e.returnValue='';}});
  return {render:which=>{if(which==='archive')renderArchive();else renderStudio();const tabs=document.createElement('div');tabs.className='work-view-tabs';tabs.setAttribute('role','group');tabs.setAttribute('aria-label','Proposal Studio');tabs.innerHTML=`<button data-studio-tab="proposal" class="${which==='archive'?'':'active'}" aria-pressed="${which!=='archive'}">Không gian viết thư</button><button data-studio-tab="archive" class="${which==='archive'?'active':''}" aria-pressed="${which==='archive'}">Thư đã gửi <span>${records.filter(r=>r.kind==='sentproposal').length}</span></button>`;$('#studioNavigation').replaceChildren(tabs);$('#studioNavigation').hidden=false;tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>changeView(b.dataset.studioTab));},open,openForJob};
})();
boot();
