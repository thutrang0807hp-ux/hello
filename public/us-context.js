/* US dates are evaluated in the selected client's timezone. */
const USCalendar = (() => {
 const zones=[['America/New_York','Miền Đông · New York'],['America/Chicago','Miền Trung · Chicago'],['America/Denver','Miền Núi · Denver'],['America/Los_Angeles','Miền Tây · Los Angeles'],['America/Phoenix','Arizona · Phoenix'],['America/Anchorage','Alaska'],['Pacific/Honolulu','Hawaii']];
 const iso=d=>d.toISOString().slice(0,10), date=(y,m,d)=>new Date(Date.UTC(y,m-1,d));
 function nth(y,m,weekday,n){const d=date(y,m,1);return date(y,m,1+(weekday-d.getUTCDay()+7)%7+7*(n-1));}
 function last(y,m,weekday){const d=date(y,m+1,0);d.setUTCDate(d.getUTCDate()-(d.getUTCDay()-weekday+7)%7);return d;}
 const translations={
 'Năm mới':['New Year’s Day','Tết Dương lịch'],
 'Martin Luther King Jr. Day':['Martin Luther King Jr. Day','Ngày tưởng niệm Martin Luther King Jr.'],
 'Presidents’ Day':['Presidents’ Day','Ngày Tổng thống'],
 'Valentine':['Valentine’s Day','Ngày lễ Tình nhân'],
 'Ngày của Mẹ · Mother’s Day':['Mother’s Day','Ngày của Mẹ'],
 'Memorial Day':['Memorial Day','Ngày tưởng niệm quân nhân hy sinh'],
 'Juneteenth':['Juneteenth','Ngày kỷ niệm chấm dứt chế độ nô lệ ở Mỹ'],
 'Ngày của Cha · Father’s Day':['Father’s Day','Ngày của Cha'],
 'Ngày Độc lập · Independence Day':['Independence Day','Ngày Quốc khánh Mỹ'],
 'Labor Day':['Labor Day','Ngày Lao động Mỹ'],
 'Columbus Day / Indigenous Peoples’ Day':['Columbus Day / Indigenous Peoples’ Day','Ngày Columbus / Ngày các dân tộc bản địa'],
 'Halloween':['Halloween','Lễ hội hóa trang'],
 'Veterans Day':['Veterans Day','Ngày Cựu chiến binh'],
 'Lễ Tạ ơn · Thanksgiving':['Thanksgiving','Lễ Tạ ơn'],
 'Black Friday':['Black Friday','Thứ Sáu Đen · Ngày mua sắm giảm giá'],
 'Giáng sinh · Christmas':['Christmas Day','Lễ Giáng sinh']
 };
 function holidays(y){const out=[];
 function add(d,name,type,description,fixed=false){const [english,vietnamese]=translations[name]||[name,name];out.push({date:iso(d),name,english,vietnamese,type,description});if(fixed&&[0,6].includes(d.getUTCDay())){const observed=new Date(d);observed.setUTCDate(d.getUTCDate()+(d.getUTCDay()===6?-1:1));out.push({date:iso(observed),name:name+' · nghỉ bù',english:english+' (observed)',vietnamese:vietnamese+' · nghỉ bù',type,description:'Ngày nghỉ bù của '+name+'. '+description});}}
 const federal='Lễ liên bang', cultural='Dịp văn hóa';
 add(date(y,1,1),'Năm mới',federal,'Nhiều cơ quan và doanh nghiệp nghỉ.',true);
 add(nth(y,1,1,3),'Martin Luther King Jr. Day',federal,'Ngày tưởng nhớ nhà hoạt động dân quyền Martin Luther King Jr.');
 add(nth(y,2,1,3),'Presidents’ Day',federal,'Ngày Washington’s Birthday, thường được gọi là Ngày Tổng thống.');
 add(date(y,2,14),'Valentine',cultural,'Ngày lễ tình nhân; không phải ngày nghỉ liên bang.');
 add(nth(y,5,0,2),'Ngày của Mẹ · Mother’s Day',cultural,'Chủ nhật thứ hai tháng 5. Khách có thể dành thời gian cho gia đình; không phải ngày nghỉ liên bang.');
 add(last(y,5,1),'Memorial Day',federal,'Tưởng niệm quân nhân hy sinh; thường có kỳ nghỉ cuối tuần dài.');
 add(date(y,6,19),'Juneteenth',federal,'Kỷ niệm việc chấm dứt chế độ nô lệ ở Mỹ.',true);
 add(nth(y,6,0,3),'Ngày của Cha · Father’s Day',cultural,'Chủ nhật thứ ba tháng 6; dịp dành cho gia đình.');
 add(date(y,7,4),'Ngày Độc lập · Independence Day',federal,'Quốc khánh Mỹ; thường có nghỉ lễ và pháo hoa.',true);
 add(nth(y,9,1,1),'Labor Day',federal,'Ngày Lao động của Mỹ, khác ngày 1/5.');
 add(nth(y,10,1,2),'Columbus Day / Indigenous Peoples’ Day',federal,'Tên gọi và việc nghỉ khác nhau theo bang, địa phương và doanh nghiệp.');
 add(date(y,10,31),'Halloween',cultural,'Lễ hóa trang; không phải ngày nghỉ liên bang.');
 add(date(y,11,11),'Veterans Day',federal,'Ngày tri ân cựu chiến binh.',true);
 const thanks=nth(y,11,4,4);add(thanks,'Lễ Tạ ơn · Thanksgiving',federal,'Thứ năm thứ tư tháng 11; nhiều người nghỉ để sum họp gia đình.');
 const friday=new Date(thanks);friday.setUTCDate(friday.getUTCDate()+1);add(friday,'Black Friday',cultural,'Ngày mua sắm sau Lễ Tạ ơn; một số doanh nghiệp nghỉ thêm.');
 add(date(y,12,25),'Giáng sinh · Christmas',federal,'Nhiều người nghỉ lễ và nghỉ cuối năm.',true);
 return out.sort((a,b)=>a.date.localeCompare(b.date));
 }
 function localDate(now,zone){const parts=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);const get=t=>parts.find(p=>p.type===t).value;return `${get('year')}-${get('month')}-${get('day')}`;}
 function upcoming(now,zone){const day=localDate(now,zone),year=Number(day.slice(0,4));return [year-1,year,year+1].flatMap(holidays).filter(h=>h.date>=day).sort((a,b)=>a.date.localeCompare(b.date)).map(h=>({...h,days:Math.round((Date.parse(h.date)-Date.parse(day))/86400000)}));}
 return {zones,holidays,localDate,upcoming};
})();
if(typeof module!=='undefined') module.exports=USCalendar;
const USContext = (()=>{
 let zone='America/New_York',widget,timer;
 try{const saved=localStorage.getItem('freelance-us-zone');if(USCalendar.zones.some(z=>z[0]===saved))zone=saved;}catch{}
 const e=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const pretty=s=>s.split('-').reverse().join('/');
 function update(){if(!widget||widget.hidden)return;const now=new Date(),next=USCalendar.upcoming(now,zone)[0];widget.querySelector('.us-clock').textContent=new Intl.DateTimeFormat('en-US',{timeZone:zone,hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(now);widget.querySelector('.us-clock-date').textContent=pretty(USCalendar.localDate(now,zone))+' · '+new Intl.DateTimeFormat('en-US',{timeZone:zone,timeZoneName:'short'}).formatToParts(now).find(p=>p.type==='timeZoneName').value;widget.querySelector('.us-next').innerHTML=`<span>${next.days===0?'HÔM NAY':next.days<=7?'SẮP TỚI · '+next.days+' NGÀY NỮA':'DỊP LỄ TIẾP THEO'}</span><strong>${e(next.english)}</strong><div class="us-holiday-vietnamese">${e(next.vietnamese)}</div><small>${pretty(next.date)} · ${e(next.type)}</small>`;widget.querySelector('.us-next').title=next.description;}
 function mount(){if(!widget)return;document.body.classList.remove('us-clock-header');const slot=document.querySelector('#overviewUSSlot');if(view==='overview'&&slot){widget.hidden=false;slot.append(widget);update();}else widget.hidden=true;}
 function sync(){if(!widget){widget=document.createElement('section');widget.className='us-context';widget.setAttribute('aria-label','Giờ và ngày lễ Mỹ');widget.innerHTML=`<div class="us-context-top"><label><span>GIỜ MỸ</span><select aria-label="Múi giờ Mỹ">${USCalendar.zones.map(([id,label])=>`<option value="${id}" ${id===zone?'selected':''}>${label}</option>`).join('')}</select></label><button type="button" class="us-calendar-open">Lịch lễ ↗</button></div><div class="us-context-body"><div><strong class="us-clock"></strong><small class="us-clock-date"></small></div><div class="us-next"></div></div>`;widget.querySelector('select').onchange=event=>{zone=event.target.value;try{localStorage.setItem('freelance-us-zone',zone);}catch{}update();};widget.querySelector('button').onclick=open;timer=setInterval(update,10000);window.addEventListener('resize',mount);}mount();}
 function open(){let dialog=document.querySelector('#usHolidayDialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='usHolidayDialog';dialog.className='us-holiday-dialog';document.body.append(dialog);}const current=Number(USCalendar.localDate(new Date(),zone).slice(0,4));dialog.innerHTML=`<div class="us-dialog-head"><div><span class="eyebrow">LỊCH MỸ · GIẢI THÍCH TIẾNG VIỆT</span><h2>Những dịp cần biết</h2></div><button aria-label="Đóng lịch lễ">✕</button></div><div class="us-calendar-tools"><label>Năm <select aria-label="Năm lịch lễ">${[current-1,current,current+1,current+2].map(y=>`<option ${y===current?'selected':''}>${y}</option>`).join('')}</select></label><button type="button" class="us-calendar-today">Hôm nay</button><p>Lễ liên bang không có nghĩa mọi khách đều nghỉ. Dịp văn hóa có thể ảnh hưởng lịch sinh hoạt.</p></div><div class="us-holiday-list"></div>`;dialog.setAttribute('aria-label','Lịch ngày lễ Mỹ');dialog.querySelector('button').onclick=()=>dialog.close();const paint=()=>{const day=USCalendar.localDate(new Date(),zone);dialog.querySelector('.us-holiday-list').innerHTML=USCalendar.holidays(Number(dialog.querySelector('select').value)).map(h=>`<article class="${h.date===day?'is-today':''}"><time datetime="${h.date}">${pretty(h.date)}</time><div><h3>${e(h.english)}</h3><div class="us-holiday-vietnamese">${e(h.vietnamese)}</div><span>${e(h.type)}${h.date===day?' · Hôm nay':''}</span><p>${e(h.description)}</p></div></article>`).join('');};const jumpToToday=()=>{const day=USCalendar.localDate(new Date(),zone);dialog.querySelector('select').value=day.slice(0,4);paint();const dates=[...dialog.querySelectorAll('.us-holiday-list time')];const target=dates.find(t=>t.dateTime>=day)||dates.at(-1);if(target){const row=target.closest('article');dialog.scrollTo({top:dialog.scrollTop+row.getBoundingClientRect().top-dialog.getBoundingClientRect().top-24,behavior:'instant'});}};dialog.querySelector('select').onchange=()=>{paint();dialog.scrollTop=0;};dialog.querySelector('.us-calendar-today').onclick=jumpToToday;paint();dialog.showModal();requestAnimationFrame(jumpToToday);}
 return {sync};
})();
