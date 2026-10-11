/* Pure filter rules shared by the UI and focused tests. */
const JobFilters = (() => {
 const options={
  time:[['1h','Trong 1 giờ'],['6h','Trong 6 giờ'],['24h','Trong 24 giờ'],['7d','Trong 7 ngày'],['older','Hơn 7 ngày'],['unknown','Chưa có giờ đăng']],
  proposals:[['under5','Dưới 5'],['5-10','5–10'],['10-20','10–20'],['20-50','20–50'],['50plus','50 trở lên'],['unknown','Chưa có dữ liệu']],
  rating:[['high','4,8–5 sao'],['good','4,5–dưới 4,8'],['low','Dưới 4,5 sao'],['unknown','Chưa có đánh giá']],
  sent:[['sent','Đã gửi thư'],['unsent','Chưa gửi thư']],
 };
 const titles={time:'Thời gian đăng',country:'Quốc gia khách',keywords:'Từ khóa',budget:'Ngân sách',proposals:'Số proposal trên job',rating:'Sao của khách',sent:'Thư của bạn'};
 const defaults=()=>({time:{enabled:false,values:['24h']},country:{enabled:false,values:[]},keywords:{enabled:false,include:'',exclude:'',mode:'any'},budget:{enabled:false,type:'fixed',min:'',max:'',unknown:false},proposals:{enabled:false,values:['under5','5-10']},rating:{enabled:false,values:['high']},sent:{enabled:false,values:['unsent']}});
 const normalizeText=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase();
 const words=v=>String(v||'').split(/[,;\n]/).map(s=>normalizeText(s.trim())).filter(Boolean);
 function sanitize(raw){
  const state=defaults();
  if(!raw||typeof raw!=='object')return state;
  for(const key of Object.keys(state)){
   const value=raw[key];if(!value||typeof value!=='object')continue;
   state[key].enabled=value.enabled===true;
   if('values' in state[key]&&Array.isArray(value.values))state[key].values=[...new Set(value.values.filter(v=>typeof v==='string'&&v.length<=150&&(key==='country'||options[key].some(o=>o[0]===v))))].slice(0,250);
  }
  if(raw.keywords){for(const k of ['include','exclude'])if(typeof raw.keywords[k]==='string')state.keywords[k]=raw.keywords[k].slice(0,2000);state.keywords.mode=raw.keywords.mode==='all'?'all':'any';}
  if(raw.budget){state.budget.type=raw.budget.type==='hourly'?'hourly':'fixed';state.budget.unknown=raw.budget.unknown===true;for(const k of ['min','max'])if(['string','number'].includes(typeof raw.budget[k]))state.budget[k]=String(raw.budget[k]).slice(0,30);}
  return state;
 }
 function validate(state){
  for(const key of ['time','country','proposals','rating','sent'])if(state[key].enabled&&!state[key].values.length)return `Chọn ít nhất một mục trong “${titles[key]}”.`;
  if(state.keywords.enabled&&!words(state.keywords.include).length&&!words(state.keywords.exclude).length)return 'Nhập ít nhất một từ khóa cần có hoặc cần loại trừ.';
  if(state.budget.enabled){
   const {min,max}=state.budget;
   for(const v of [min,max])if(v!==''&&(!Number.isFinite(Number(v))||Number(v)<0))return 'Ngân sách phải là số từ 0 trở lên.';
   if(min!==''&&max!==''&&Number(min)>Number(max))return 'Giá từ không được lớn hơn giá đến.';
  }
  return '';
 }
 function budget(job){
  const raw=String(job.budget||'').trim();
  if(!raw)return null;
  const rate=/\/(?:\s*)(?:hr|hour|h|giờ|gio)(?=\s|$)/i.test(raw);
  const declared=/hourly/i.test(job.jobType||'')?'hourly':/fixed/i.test(job.jobType||'')?'fixed':null;
  if(rate&&declared==='fixed')return null;
  const type=rate?'hourly':declared;if(!type)return null;
  const plain=raw.replace(/\/(?:\s*)(?:hr|hour|h|giờ|gio)(?=\s|$)\s*$/i,'').replace(/\s+/g,'');
  const amount='(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?';
  const prefix='(?:(?:USD|US\\$|\\$))?';
  const match=plain.match(new RegExp(`^${prefix}(${amount})(?:[–—-]${prefix}(${amount}))?$`,'i'));
  if(!match)return null;
  const min=Number(match[1].replace(/,/g,'')),max=Number((match[2]||match[1]).replace(/,/g,''));
  return Number.isFinite(min)&&Number.isFinite(max)&&min<=max?{type,min,max}:null;
 }
 function proposalBucket(value){
  const raw=String(value??'').trim().toLowerCase();
  if(/^less than 5$/.test(raw)||/^<\s*5$/.test(raw))return 'under5';
  if(/^50\s*\+$/.test(raw)||/^more than 50$/.test(raw))return '50plus';
  const range=raw.match(/^(\d+)\s*(?:to|–|-)\s*(\d+)$/),single=raw.match(/^\d+$/);
  if(!range&&!single)return 'unknown';
  const min=Number(range?range[1]:raw),max=Number(range?range[2]:raw);if(min>max)return 'unknown';
  if(max<5)return 'under5';if(min>=5&&max<=10)return '5-10';if(min>=10&&max<=20)return '10-20';if(min>=20&&max<=50)return '20-50';if(min>50)return '50plus';return 'unknown';
 }
 function matches(job,state,now=Date.now()){
  if(state.time.enabled){
   const stamp=Date.parse(job.postedAt),age=(now-stamp)/3600000,known=Number.isFinite(stamp)&&age>=0;
   if(!state.time.values.some(v=>v==='unknown'?!known:known&&(v==='older'?age>168:age<=({ '1h':1,'6h':6,'24h':24,'7d':168 }[v]??-1))))return false;
  }
  const country=typeof job.clientInfo?.country==='string'&&job.clientInfo.country.trim().length<=150?job.clientInfo.country.trim():'';
  if(state.country.enabled&&!state.country.values.includes(country||'__unknown__'))return false;
  if(state.keywords.enabled){
   const haystack=normalizeText([job.name,job.notes,...(job.skills||[])].join(' ')),include=words(state.keywords.include),exclude=words(state.keywords.exclude);
   if(exclude.some(w=>haystack.includes(w)))return false;
   if(include.length&&!(state.keywords.mode==='all'?include.every(w=>haystack.includes(w)):include.some(w=>haystack.includes(w))))return false;
  }
  if(state.budget.enabled){
   const price=budget(job),f=state.budget;
   if(!price){if(!f.unknown)return false;}
   else if(price.type!==f.type||(f.min!==''&&price.min<Number(f.min))||(f.max!==''&&price.max>Number(f.max)))return false;
  }
  if(state.proposals.enabled&&!state.proposals.values.includes(proposalBucket(job.proposalsTier)))return false;
  if(state.rating.enabled){
   const raw=job.clientInfo?.rating,number=Number(raw),known=raw!==null&&raw!==undefined&&raw!==''&&typeof raw!=='boolean'&&Number.isFinite(number)&&number>=0&&number<=5;
   const group=!known?'unknown':number>=4.8?'high':number>=4.5?'good':'low';
   if(!state.rating.values.includes(group))return false;
  }
  if(state.sent.enabled&&!state.sent.values.includes(job.proposalSent===true?'sent':'unsent'))return false;
  return true;
 }
 const count=state=>Object.keys(titles).filter(k=>state[k].enabled).length;
 return {options,titles,defaults,sanitize,validate,matches,budget,proposalBucket,count};
})();
if(typeof module!=='undefined')module.exports=JobFilters;
