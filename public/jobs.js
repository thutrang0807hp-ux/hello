const Jobs = (() => {
 let filter='all', starFilter='all';
 try{const saved=localStorage.getItem('freelanceDesk.customerStars');if(['all','high','mid','low','unknown'].includes(saved))starFilter=saved;}catch{}
 const starMatch=(j,value)=>{const stars=JobFilters.customerStars(j).stars;return value==='all'||value==='unknown'&&stars===null||stars!==null&&(value==='high'&&stars>=4||value==='mid'&&stars===3||value==='low'&&stars<=2);};
 const filterStorageKey='freelanceDesk.jobFilters.v1';
 let advanced=JobFilters.defaults();
 try{advanced=JobFilters.sanitize(JSON.parse(localStorage.getItem(filterStorageKey)));if(JobFilters.validate(advanced))advanced=JobFilters.defaults();}catch{}
 const persistFilters=()=>{try{localStorage.setItem(filterStorageKey,JSON.stringify(advanced));}catch{}};
 const labels={green:'Rất ngon',yellow:'Cần đánh giá',red:'Lướt'};
 const active=j=>j.interested && Date.parse(j.interestExpiresAt)>Date.now();
 function ago(value){
  const stamp=Date.parse(value);if(!Number.isFinite(stamp)||stamp>Date.now())return 'Chưa có dữ liệu';
  const minutes=Math.floor((Date.now()-stamp)/60000);
  return minutes<1?'vừa xong':minutes<60?`${minutes} phút trước`:minutes<1440?`${Math.floor(minutes/60)} giờ trước`:`${Math.floor(minutes/1440)} ngày trước`;
 }
 function fullDate(value){const date=Date.parse(value);return Number.isFinite(date)?new Date(date).toLocaleString('vi-VN'):'Chưa có dữ liệu';}
 function activityLine(j){
  const c=j.clientActivity||{}, state=j.jobAssessment?.activity?.state||'unknown';
  const useActivity=c.lastActivityAt&&(!c.lastViewedAt||Date.parse(c.lastActivityAt)>Date.parse(c.lastViewedAt));
  const latest=useActivity?c.lastActivityAt:c.lastViewedAt;
  const label=useActivity?'Khách hoạt động lần cuối':'Khách xem lần cuối';
  return `<div class="job-client-activity ${state}"><span>${latest?`${label}: ${esc(ago(latest))}`:'Khách xem job: chưa có dữ liệu'}</span>${c.observedAt?`<small>Cập nhật ${esc(ago(c.observedAt))}</small>`:''}${state==='quiet'?'<strong>Khách chưa quay lại · giảm ưu tiên</strong>':state==='outdated'?'<strong>Cần cập nhật hoạt động khách</strong>':''}</div>`;
 }
 function proposalCount(value){
  if(!value)return 'Chưa biết số proposal';
  const raw=String(value);
  const under=raw.match(/^less than (\d+)$/i),range=raw.match(/^(\d+)\s*(?:to|–|-)\s*(\d+)$/i);
  return under?`Dưới ${under[1]} proposal`:range?`${range[1]}–${range[2]} proposal`:`${raw} proposal`;
 }
 function jobType(value){return /fixed/i.test(value||'')?'Trọn gói':/hourly/i.test(value||'')?'Theo giờ':value;}
 function marker(j){
  const sent=j.proposalSent===true;
  return `<button class="proposal-marker ${sent?'is-sent':''}" data-proposal-sent="${j.id}" role="checkbox" aria-checked="${sent}" aria-label="Đã gửi thư báo giá cho ${esc(j.name)}" title="${sent?'Đã gửi thư báo giá · bấm để bỏ dấu':'Chưa gửi thư báo giá · bấm khi bạn đã gửi'}"><svg viewBox="0 0 28 36" aria-hidden="true" focusable="false"><path class="marker-ribbon" d="M1 1H27V34L14 27L1 34Z"/>${sent?'<path class="marker-check" d="M7 13L12 18L21 9"/>':''}</svg></button>`;
 }
 function filterChips(){
  const keys=Object.keys(JobFilters.titles).filter(k=>advanced[k].enabled);
  return keys.length?`<div class="job-filter-chips">${keys.map(k=>`<button data-clear-condition="${k}" title="Bỏ điều kiện ${esc(JobFilters.titles[k])}">${esc(JobFilters.titles[k])}<span aria-hidden="true">×</span></button>`).join('')}<button data-clear-conditions class="clear-all-conditions">Xóa điều kiện</button></div>`:'';
 }
 function openFilters(){
  close();
  let dialog=$('#jobFilterDialog');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='jobFilterDialog';dialog.className='job-filter-dialog';document.body.append(dialog);}
  let draft=structuredClone(advanced);
  const regionNames=new Intl.DisplayNames(['en'],{type:'region'}), vietnameseNames=new Intl.DisplayNames(['vi'],{type:'region'});
  const regionCodes='AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW'.split(' ');
  const standardCountries=regionCodes.map(code=>regionNames.of(code));
  const countryLabels=new Map(regionCodes.map(code=>[regionNames.of(code),vietnameseNames.of(code)]));
  const countries=[...new Set(records.filter(j=>j.kind==='job').map(j=>j.clientInfo?.country).filter(v=>typeof v==='string'&&v.trim()&&v.trim().length<=150).map(v=>v.trim()).concat(standardCountries,draft.country.values.filter(v=>v!=='__unknown__')))].sort((a,b)=>a.localeCompare(b));
  const countryOptions=countries.map(v=>[v,countryLabels.has(v)?`${countryLabels.get(v)} · ${v}`:v]).concat([['__unknown__','Chưa rõ quốc gia']]);
  const checks=(key,items)=>items.map(([value,label])=>`<label class="filter-option"><input type="checkbox" data-filter-value="${key}" value="${esc(value)}" ${draft[key].values.includes(value)?'checked':''}><span>${esc(label)}</span></label>`).join('');
  const section=(key,body)=>`<section class="filter-section" data-filter-section="${key}"><label class="filter-section-toggle"><input type="checkbox" data-filter-enabled="${key}" ${draft[key].enabled?'checked':''}><span>${JobFilters.titles[key]}</span></label><fieldset class="filter-section-fields" data-filter-fields="${key}" ${draft[key].enabled?'':'disabled'}>${body}</fieldset></section>`;
  function paint(){
   dialog.innerHTML=`<form id="jobFilterForm"><div class="job-filter-heading"><div><span class="eyebrow">CƠ HỘI CÔNG VIỆC</span><h2 id="jobFilterTitle">Lọc công việc</h2><p>Tích nhóm muốn lọc, rồi chọn các điều kiện bên dưới.</p></div><button type="button" id="closeJobFilters" aria-label="Đóng bộ lọc">✕</button></div><div class="job-filter-grid">${section('time',checks('time',JobFilters.options.time))}${section('country',`<label class="filter-text-field country-search-label">Tìm quốc gia<input id="filterCountrySearch" type="search" placeholder="Việt Nam, United States…" autocomplete="off"></label><div class="country-filter-options" tabindex="0" aria-label="Danh sách quốc gia, cuộn để chọn nhiều nước">${checks('country',countryOptions)}</div><p id="countrySelectionCount" class="filter-help"></p><p class="filter-help">Cuộn danh sách và tích chọn nhiều quốc gia.</p>`)}${section('keywords',`<label class="filter-text-field">Cần có<input name="includeKeywords" value="${esc(draft.keywords.include)}" placeholder="Figma, dashboard, SaaS" maxlength="2000"></label><div class="keyword-mode"><label class="filter-option"><input type="radio" name="keywordMode" value="any" ${draft.keywords.mode==='any'?'checked':''}><span>Có một trong các từ</span></label><label class="filter-option"><input type="radio" name="keywordMode" value="all" ${draft.keywords.mode==='all'?'checked':''}><span>Có đủ các từ</span></label></div><label class="filter-text-field">Loại trừ<input name="excludeKeywords" value="${esc(draft.keywords.exclude)}" placeholder="crypto, unpaid…" maxlength="2000"></label><p class="filter-help">Ngăn cách bằng dấu phẩy. Tìm trong tên, mô tả và kỹ năng của job.</p>`)}${section('budget',`<label class="filter-text-field">Loại ngân sách<select name="filterBudgetType"><option value="fixed" ${draft.budget.type==='fixed'?'selected':''}>Trọn gói · USD/job</option><option value="hourly" ${draft.budget.type==='hourly'?'selected':''}>Theo giờ · USD/giờ</option></select></label><div class="filter-price-range"><label class="filter-text-field">Từ<input name="filterBudgetMin" type="number" min="0" step="0.01" value="${esc(draft.budget.min)}" placeholder="Không giới hạn"></label><label class="filter-text-field">Đến<input name="filterBudgetMax" type="number" min="0" step="0.01" value="${esc(draft.budget.max)}" placeholder="Không giới hạn"></label></div><label class="filter-option"><input name="includeUnknownBudget" type="checkbox" ${draft.budget.unknown?'checked':''}><span>Kèm job chưa có giá USD đọc được</span></label><p class="filter-help">Cả khoảng giá job phải nằm trong mức bạn chọn. Không so giá trọn gói với giá theo giờ.</p>`)}${section('proposals',`<div class="filter-two-columns">${checks('proposals',JobFilters.options.proposals)}</div>`)}${section('rating',checks('rating',JobFilters.options.rating))}${section('sent',`<div class="filter-two-columns">${checks('sent',JobFilters.options.sent)}</div>`)}</div><div class="job-filter-footer"><div><strong id="jobFilterPreview"></strong><p id="jobFilterError" role="alert"></p><small>Các nhóm kết hợp với nhau; chọn nhiều mục trong một nhóm để lấy một trong các mục đó.</small></div><div class="job-filter-buttons"><button type="button" id="resetJobFilters">Đặt lại</button><button type="button" id="cancelJobFilters">Hủy</button><button type="submit" class="primary" id="applyJobFilters">Áp dụng</button></div></div></form>`;
   dialog.setAttribute('aria-labelledby','jobFilterTitle');
   $('#closeJobFilters').onclick=()=>dialog.close();$('#cancelJobFilters').onclick=()=>dialog.close();
   $('#resetJobFilters').onclick=()=>{draft=JobFilters.defaults();paint();};
   $('#jobFilterForm').oninput=readDraft;$('#jobFilterForm').onchange=readDraft;
   $('#jobFilterForm').onsubmit=e=>{e.preventDefault();readDraft();if(JobFilters.validate(draft))return;advanced=structuredClone(draft);persistFilters();dialog.close();render();$('#openJobFilters').focus({preventScroll:true});};
   $('#filterCountrySearch').oninput=()=>{const query=JobFilters.normalizeText?JobFilters.normalizeText($('#filterCountrySearch').value):$('#filterCountrySearch').value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();for(const item of dialog.querySelectorAll('.country-filter-options .filter-option')){const text=item.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();item.hidden=!text.includes(query);}};
   preview();
  }
  function readDraft(){
   for(const key of Object.keys(JobFilters.titles)){
    draft[key].enabled=dialog.querySelector(`[data-filter-enabled="${key}"]`).checked;
    dialog.querySelector(`[data-filter-fields="${key}"]`).disabled=!draft[key].enabled;
    if('values' in draft[key])draft[key].values=[...dialog.querySelectorAll(`[data-filter-value="${key}"]:checked`)].map(el=>el.value);
   }
   draft.keywords.include=dialog.querySelector('[name=includeKeywords]').value;draft.keywords.exclude=dialog.querySelector('[name=excludeKeywords]').value;
   draft.keywords.mode=dialog.querySelector('[name=keywordMode]:checked').value;
   draft.budget.type=dialog.querySelector('[name=filterBudgetType]').value;draft.budget.min=dialog.querySelector('[name=filterBudgetMin]').value;draft.budget.max=dialog.querySelector('[name=filterBudgetMax]').value;draft.budget.unknown=dialog.querySelector('[name=includeUnknownBudget]').checked;
   preview();
  }
  function preview(){
   $('#countrySelectionCount').textContent=`Đã chọn ${draft.country.values.length} quốc gia`;
   const error=JobFilters.validate(draft),term=$('#search').value.toLowerCase();
   const number=error?0:records.filter(j=>j.kind==='job'&&JSON.stringify(j).toLowerCase().includes(term)&&JobFilters.matches(j,draft)&&starMatch(j,starFilter)&&(filter==='all'||filter==='interest'&&active(j)||j.jobAssessment?.color===filter)).length;
   $('#jobFilterPreview').textContent=`${number} job phù hợp trong nhóm đang xem`;
   $('#jobFilterError').textContent=error;$('#applyJobFilters').disabled=!!error;
  }
  paint();if(!dialog.open)dialog.showModal();
 }
 function close(){document.querySelector('#jobDetailDialog')?.close();}
 function render(){
  const search=$('#search'), focused=search===document.activeElement;
  const selection=[search.selectionStart,search.selectionEnd];
  const term=search.value.toLowerCase();
  const allJobs=records.filter(j=>j.kind==='job');
  const matches=allJobs.filter(j=>JSON.stringify(j).toLowerCase().includes(term)&&JobFilters.matches(j,advanced));
  const inFilter=(j,id)=>id==='all'||id==='interest'&&active(j)||j.jobAssessment?.color===id;
  const jobs=matches.filter(j=>inFilter(j,filter)&&starMatch(j,starFilter)).sort((a,b)=>(JobFilters.customerStars(b).stars||0)-(JobFilters.customerStars(a).stars||0)||b.id-a.id);
  const groups=[['all','Tất cả'],['interest','Quan tâm'],['green','Rất ngon'],['yellow','Cần đánh giá'],['red','Lướt']];
  const cards=jobs.map(j=>{
   const customer=JobFilters.customerStars(j);
   const a=j.jobAssessment||{color:'yellow',state:'unconfigured'},color=a.color||'yellow';
   return `<article class="card radar-job ${color}" data-radar-job="${j.id}">${marker(j)}<div class="radar-main"><div class="radar-top"><span class="customer-star-badge ${customer.stars===null?'unknown':customer.stars>=4?'high':customer.stars===3?'mid':'low'}" title="${esc(customer.explanation)}">${customer.stars===null?'Điểm khách · Chưa đủ dữ liệu':`<span aria-hidden="true">${'★'.repeat(customer.stars)}${'☆'.repeat(5-customer.stars)}</span> Điểm khách · ${customer.stars}/5`}</span><span class="radar-grade ${color}">${a.state==='completed'?`AI · ${labels[color]} · ${a.score}/100`:'AI · Chưa đánh giá'}</span>${j.unread?'<span class="job-unread-dot">Chưa đọc</span>':''}${j.proposalSent===true?'<span class="proposal-sent-label">✓ Đã gửi thư</span>':''}</div><h3><button class="job-title-button" data-job-open="${j.id}">${esc(j.name)}</button></h3><p class="job-row-summary">${esc(j.notes||'Nguồn chưa gửi mô tả công việc.')}</p><div class="job-row-facts"><span>${esc(j.clientInfo?.country||'Chưa rõ quốc gia')}</span><span>Sao Upwork: ${esc(j.clientInfo?.rating??'Chưa có dữ liệu')}</span><span>${j.clientInfo?.totalHires!=null?`Đã thuê: ${esc(j.clientInfo.totalHires)}`:'Chưa rõ lịch sử thuê'}</span><span>${esc(proposalCount(j.proposalsTier))}</span>${active(j)?`<span class="job-interest-until">Quan tâm đến ${new Date(j.interestExpiresAt).toLocaleDateString('vi-VN')}</span>`:''}</div></div><div class="job-price-column"><div><span class="job-fact-label">Ngân sách</span><strong>${esc(j.budget||'Chưa có dữ liệu')}</strong>${j.jobType?`<small>${esc(jobType(j.jobType))}</small>`:''}</div><div class="job-posted-time" title="${esc(fullDate(j.postedAt))}"><span class="job-fact-label">Đăng / làm mới</span><span>${esc(ago(j.postedAt))}</span></div></div><div class="job-row-footer"><div class="job-row-activity">${activityLine(j)}</div><div class="actions">${safeLink(j.url)?`<a class="job-source-link" href="${esc(safeLink(j.url))}" target="_blank" rel="noopener noreferrer" aria-label="Mở ${esc(j.name)} trên Upwork">Upwork ↗</a>`:''}<button class="job-interest-action ${active(j)?'is-interested':''}" data-interest="${j.id}" aria-pressed="${active(j)}">${active(j)?'★ Đã quan tâm':'☆ Quan tâm'}</button><button class="job-assessment-action" data-job-detail="${j.id}">Đánh giá AI</button><button class="primary" data-job-open="${j.id}">Xem chi tiết</button></div></div></article>`;
  }).join('');
  $('#content').innerHTML=`<div class="job-list-tools"><div class="radar-controls" role="group" aria-label="Lọc công việc">${groups.map(([id,label])=>`<button data-job-filter="${id}" class="${filter===id?'selected':''} ${id}" aria-pressed="${filter===id}" ${id==='interest'?'title="Job quan tâm tự bỏ lưu sau 7 ngày"':''}>${['green','yellow','red'].includes(id)?'<span class="filter-dot" aria-hidden="true"></span>':''}${label}<span class="filter-count">${matches.filter(j=>inFilter(j,id)).length}</span></button>`).join('')}</div><div class="job-tool-actions"><div class="job-search-wrap"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"/><path d="M13 13L18 18"/></svg><div id="jobSearchSlot"></div></div><button id="openJobFilters" class="job-funnel-button ${JobFilters.count(advanced)?'has-filters':''}" aria-haspopup="dialog" title="Lọc công việc theo nhiều điều kiện"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M2 3H18L12 10V16L8 18V10Z"/></svg><span>Lọc</span>${JobFilters.count(advanced)?`<strong>${JobFilters.count(advanced)}</strong>`:''}</button></div></div>${filterChips()}<div class="customer-star-filters" role="group" aria-label="Lọc theo điểm khách"><strong>Điểm khách</strong>${[['all','Tất cả'],['high','4–5 sao'],['mid','3 sao'],['low','1–2 sao'],['unknown','Chưa đủ dữ liệu']].map(([id,label])=>`<button data-customer-star-filter="${id}" aria-pressed="${starFilter===id}" class="${starFilter===id?'selected':''}">${label}<span>${matches.filter(j=>inFilter(j,filter)&&starMatch(j,id)).length}</span></button>`).join('')}<small>Theo dữ liệu · Không dùng API</small></div><div class="job-list-caption"><span><strong>${jobs.length}</strong> công việc · Nhận tự động từ Upwork Toolkit</span><span class="job-hover-tip">Bấm Đánh giá AI để đọc sâu · Kết quả được lưu</span></div><div class="radar-list">${cards||`<div class="empty"><h2>${allJobs.length?'Chưa có job phù hợp':'Đang chờ công việc đầu tiên'}</h2><p>${allJobs.length?'Thử đổi bộ lọc hoặc từ khóa tìm kiếm.':'Kết nối webhook của Upwork Toolkit để nhận job tự động.'}</p>${allJobs.length?'':'<button class="primary" data-job-connect>Kết nối Upwork Toolkit</button>'}</div>`}</div>`;
  search.placeholder='Tìm công việc…';search.setAttribute('aria-label','Tìm kiếm công việc');
  $('#jobSearchSlot').append(search);$('#openJobFilters').onclick=openFilters;
  if(focused){search.focus({preventScroll:true});search.setSelectionRange(...selection);}

 }

 function analysisMarkup(j){
  const a=j.jobAssessment||{};
  return `<section class="job-ai-panel" aria-labelledby="jobAiHeading"><div class="job-ai-heading"><div><span class="eyebrow">TRỢ LÝ AI</span><h3 id="jobAiHeading">Phân tích công việc</h3></div>${a.state==='completed'?`<span class="job-ai-score ${a.color||'yellow'}">${a.score}<small>/100</small></span>`:''}</div>${a.state==='completed'?`<p class="job-ai-saved">✓ Đã lưu kết quả · Xem lại không gọi API</p><div class="job-ai-summary"><h4>Tóm tắt tiếng Việt</h4><p>${esc(a.summary)}</p></div><div class="job-ai-insights">${[['Ngân sách có hợp lý?',a.priceComment],['Phạm vi cần làm rõ',a.clarityComment],['Rủi ro cần chú ý',a.riskComment]].map(([label,text])=>`<article><h4>${label}</h4><p>${esc(text)}</p></article>`).join('')}</div>${a.warnings?.length?`<div class="job-ai-warnings"><strong>Cần lưu ý</strong><ul>${a.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></div>`:''}${a.criteria?.length?`<details class="job-ai-criteria"><summary>Xem cách tính điểm AI</summary><div class="job-criteria">${a.criteria.map(c=>`<div><strong>${esc(c.name)} <span>${c.score}/${c.max}</span></strong><small>${esc(c.reason)}</small></div>`).join('')}</div></details>`:''}`:`<div class="job-ai-empty"><p>${a.state==='error'?esc(a.error):'Chưa có phân tích AI. Bấm nút dưới để đọc tóm tắt, ngân sách và rủi ro bằng tiếng Việt.'}</p><button id="runJobAnalysis" class="primary">${a.state==='error'?'Thử phân tích lại':'Phân tích bằng AI'}</button><small>Dùng credit API khi chạy · Kết quả được lưu để xem lại</small><p id="jobAnalysisStatus" role="status"></p></div>`}<p class="job-ai-footnote">Phân tích hỗ trợ quyết định, không bảo đảm job an toàn hoặc chắc chắn có hợp đồng.</p></section>`;
 }
 function details(id){
  const j=records.find(r=>r.kind==='job'&&r.id===Number(id));if(!j)return;
  let dialog=document.querySelector('#jobDetailDialog');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='jobDetailDialog';dialog.className='job-detail-dialog';document.body.append(dialog);}
  dialog.dataset.jobId=String(j.id);
  const a=j.jobAssessment||{}, client=j.clientInfo||{}, customer=JobFilters.customerStars(j);
  const info=(label,value)=>`<div><dt>${label}</dt><dd>${esc(value??'Chưa có thông tin')}</dd></div>`;
  const date=Date.parse(j.postedAt);
  const payment=client.paymentVerified===true?'Đã xác minh':client.paymentVerified===false?'Chưa xác minh':'Chưa có thông tin';
  dialog.innerHTML=`<div class="job-detail-heading"><div><span class="eyebrow">${esc(j.source==='upwork-toolkit'?'CÔNG VIỆC TỪ UPWORK TOOLKIT':'CHI TIẾT CÔNG VIỆC')}</span><h2 id="jobDetailTitle">${esc(j.name)}</h2><div class="job-detail-tags"><span class="customer-star-badge ${customer.stars===null?'unknown':customer.stars>=4?'high':customer.stars===3?'mid':'low'}" title="${esc(customer.explanation)}">${customer.stars===null?'Điểm khách · Chưa đủ dữ liệu':`Điểm khách · ${'★'.repeat(customer.stars)}${'☆'.repeat(5-customer.stars)} · ${customer.stars}/5`}</span>${j.budget?`<span class="badge">${esc(j.budget)}</span>`:''}<span class="radar-grade ${a.color||'yellow'}">${a.state==='completed'?`AI · ${labels[a.color||'yellow']} · ${a.score}/100`:'AI · Chưa phân tích'}</span>${j.jobType?`<span class="badge">${esc(j.jobType)}</span>`:''}</div></div><button id="closeJobDetail" aria-label="Đóng chi tiết công việc">✕</button></div>${analysisMarkup(j)}<div class="job-detail-layout"><section class="job-description-panel"><div class="job-section-heading"><h3>Mô tả công việc</h3><button id="supplementDescription">Bổ sung mô tả</button></div><div class="job-description-text" id="jobDescriptionText">${esc(j.notes||'Chưa có mô tả công việc.')}</div><div id="descriptionEdit" hidden><label for="jobDescriptionInput">Mô tả đầy đủ<textarea id="jobDescriptionInput">${esc(j.notes||'')}</textarea></label><div class="description-edit-actions"><button id="cancelDescription">Hủy</button><button id="saveDescription" class="primary">Lưu mô tả</button></div><p id="descriptionError" role="alert"></p></div>${j.skills?.length?`<div class="job-skill-list">${j.skills.map(skill=>`<span class="badge">${esc(skill)}</span>`).join('')}</div>`:''}${j.source==='upwork-toolkit'?'<p class="job-source-note">Mô tả nhận từ toolkit có thể bị cắt ngắn. Xem bản đầy đủ trên Upwork hoặc bổ sung tại đây.</p>':''}</section><section class="job-facts-panel" aria-label="Thông tin công việc và khách hàng"><h3>Công việc</h3><dl>${info('Ngân sách',j.budget||null)}${info('Người đã nộp',j.proposalsTier||null)}${info('Đăng / làm mới',Number.isFinite(date)?new Date(date).toLocaleString('vi-VN'):null)}${j.duration?info('Thời lượng',j.duration):''}${j.engagement?info('Khối lượng',j.engagement):''}</dl><h3>Khách hàng</h3><dl>${info('Quốc gia',client.country||null)}${info('Sao Upwork',client.rating!=null?`${client.rating}/5`:null)}${info('Tổng chi',client.totalSpent!=null?`${client.totalSpent} USD`:null)}${client.totalHires!=null?info('Số lần thuê',client.totalHires):''}${info('Tỷ lệ thuê',customer.reasons.find(r=>r.startsWith('Tỷ lệ thuê:'))?.replace('Tỷ lệ thuê: ','')||null)}${info('Thanh toán',payment)}${info('Khách xem lần cuối',fullDate(j.clientActivity?.lastViewedAt))}${j.clientActivity?.lastActivityAt?info('Hoạt động trên job',fullDate(j.clientActivity.lastActivityAt)):''}${j.clientActivity?.observedAt?info('Dữ liệu cập nhật',fullDate(j.clientActivity.observedAt)):''}</dl></section></div><section class="job-activity-section"><h3>Khách còn theo dõi job?</h3>${activityLine(j)}<p class="activity-explanation">${esc(a.activity?.reason||'Nguồn chưa gửi dữ liệu hoạt động khách trên job.')} ${a.activity?.penalty?`(−${a.activity.penalty} điểm ưu tiên)`:''}</p><details class="activity-history"><summary>Lịch sử ghi nhận${j.clientActivityHistory?.length?` · ${j.clientActivityHistory.length} mốc`:''}</summary>${j.clientActivityHistory?.length?`<p>Các mốc ứng dụng ghi nhận, không phải toàn bộ lịch sử lượt xem trên Upwork.</p><ol>${[...j.clientActivityHistory].reverse().map(h=>`<li><strong>${h.field==='lastViewedAt'?'Khách xem job':'Khách hoạt động'}: ${esc(fullDate(h.at))}</strong><small>Ghi nhận ${esc(fullDate(h.observedAt))} · ${h.source==='manual'?'Bạn bổ sung từ Upwork':'Nguồn job'}</small></li>`).join('')}</ol>`:'<p>Chưa có mốc hoạt động nào từ nguồn. Đây là các lần ứng dụng ghi nhận, không phải toàn bộ lịch sử lượt xem của Upwork.</p>'}</details><details class="activity-manual"><summary>Bổ sung lần khách xem job từ Upwork</summary><p>Webhook toolkit hiện chưa gửi trường này. Nếu Upwork hiển thị “Last viewed by client”, bạn có thể ghi lại thời điểm tương ứng.</p><label for="clientViewedInput">Khách xem lần cuối<input id="clientViewedInput" type="datetime-local"></label><button id="saveClientActivity">Lưu mốc hoạt động</button><p id="activitySaveError" role="alert"></p></details></section><div class="job-detail-footer"><button id="interestJobDetail" class="job-interest-action ${active(j)?'is-interested':''}">${active(j)?'★ Đã quan tâm':'☆ Quan tâm'}</button><button id="writeJobProposal" class="primary">Viết thư cho job này ↗</button>${safeLink(j.url)?`<a class="primary job-upwork-link" href="${esc(safeLink(j.url))}" target="_blank" rel="noopener noreferrer">Xem trên Upwork ↗</a>`:''}<button id="doneJobDetail">Đóng</button></div>`;
  dialog.setAttribute('aria-labelledby','jobDetailTitle');
  dialog.querySelector('#runJobAnalysis')?.addEventListener('click',async event=>{
   const button=event.currentTarget;button.disabled=true;button.textContent='AI đang phân tích…';dialog.querySelector('#jobAnalysisStatus').textContent='Đang xử lý. Kết quả sẽ được lưu khi hoàn tất.';
   try{await post('/api/jobs/retry',{id:j.id});await refresh();if(dialog.open&&dialog.dataset.jobId===String(j.id)){details(j.id);dialog.scrollTop=0;}}
   catch(error){if(dialog.open&&dialog.dataset.jobId===String(j.id)){dialog.querySelector('#jobAnalysisStatus').textContent=error.message;button.disabled=false;button.textContent='Thử phân tích lại';}}
  });
  dialog.querySelector('#interestJobDetail').onclick=async event=>{const button=event.currentTarget;button.disabled=true;try{await post('/api/jobs/interest',{id:j.id,interested:!active(j)});await refresh();if(dialog.open&&dialog.dataset.jobId===String(j.id))details(j.id);}catch(error){notice(error.message);button.disabled=false;}};
  dialog.onclick=event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}};

  dialog.querySelector('#closeJobDetail').onclick=()=>dialog.close();
  dialog.querySelector('#doneJobDetail').onclick=()=>dialog.close();
  dialog.querySelector('#writeJobProposal').onclick=()=>{if(Studio.openForJob(j))dialog.close();};
  const toggleEdit=editing=>{dialog.querySelector('#descriptionEdit').hidden=!editing;dialog.querySelector('#jobDescriptionText').hidden=editing;dialog.querySelector('#supplementDescription').hidden=editing;if(editing)dialog.querySelector('#jobDescriptionInput').focus();};
  dialog.querySelector('#supplementDescription').onclick=()=>toggleEdit(true);
  dialog.querySelector('#cancelDescription').onclick=()=>{dialog.querySelector('#jobDescriptionInput').value=j.notes||'';dialog.querySelector('#descriptionError').textContent='';toggleEdit(false)};
  dialog.querySelector('#saveDescription').onclick=async e=>{
   const button=e.currentTarget, notes=dialog.querySelector('#jobDescriptionInput').value.trim();button.disabled=true;
   try{await post('/api/records',{id:j.id,kind:'job',name:j.name,notes});j.notes=notes;dialog.querySelector('#jobDescriptionText').textContent=notes||'Chưa có mô tả công việc.';toggleEdit(false);await refresh();details(j.id);notice('Đã lưu mô tả công việc.');}
   catch(error){dialog.querySelector('#descriptionError').textContent=error.message;}
   finally{button.disabled=false;}
  };
  dialog.querySelector('#saveClientActivity').onclick=async e=>{
   const button=e.currentTarget, value=dialog.querySelector('#clientViewedInput').value;
   if(!value){dialog.querySelector('#activitySaveError').textContent='Hãy chọn thời điểm khách xem job.';return}
   button.disabled=true;
   try{await post('/api/jobs/activity',{id:j.id,lastViewedAt:new Date(value).toISOString()});await refresh();details(j.id);notice('Đã ghi nhận hoạt động khách từ Upwork.');}
   catch(error){dialog.querySelector('#activitySaveError').textContent=error.message;}
   finally{button.disabled=false;}
  };
  if(!dialog.open){dialog.showModal();dialog.scrollTop=0;}
  if(j.unread) post('/api/jobs/read',{id:j.id}).then(()=>{j.unread=false;updateTabBadge();return refresh(true)}).catch(error=>notice(error.message));
 }
 $('#content').addEventListener('click',async e=>{
  const mark=e.target.closest('[data-proposal-sent]');
  if(mark){
   const j=records.find(r=>r.kind==='job'&&r.id===Number(mark.dataset.proposalSent));if(!j)return;
   const sent=j.proposalSent!==true;close();mark.disabled=true;
   try{await post('/api/jobs/proposal-sent',{id:j.id,sent});await refresh();notice(sent?'Đã đánh dấu gửi thư báo giá. Job đã xuất hiện trong Tổng quan.':'Đã bỏ dấu gửi thư báo giá.');}
   catch(error){notice(error.message);mark.disabled=false;}
   return;
  }
  const condition=e.target.closest('[data-clear-condition]');if(condition){advanced[condition.dataset.clearCondition].enabled=false;persistFilters();close();render();return}
  if(e.target.closest('[data-clear-conditions]')){advanced=JobFilters.defaults();persistFilters();close();render();return}
  if(e.target.closest('[data-job-connect]')){close();changeView('settings');return}
  const stars=e.target.closest('[data-customer-star-filter]');if(stars){starFilter=stars.dataset.customerStarFilter;try{localStorage.setItem('freelanceDesk.customerStars',starFilter);}catch{}close();render();return;}
  const f=e.target.closest('[data-job-filter]');if(f){filter=f.dataset.jobFilter;close();render();return}
  const bookmark=e.target.closest('[data-interest]');if(bookmark){const j=records.find(r=>r.id===Number(bookmark.dataset.interest));bookmark.disabled=true;try{await post('/api/jobs/interest',{id:j.id,interested:!active(j)});await refresh();notice(active(j)?'Đã bỏ quan tâm.':'Đã lưu quan tâm trong 7 ngày.')}catch(err){notice(err.message);bookmark.disabled=false}return}
  const open=e.target.closest('[data-job-open]');if(open){details(open.dataset.jobOpen);return}
  const detail=e.target.closest('[data-job-detail]');if(detail)details(detail.dataset.jobDetail);
 });

 return {render,close,details,marker};
})();
