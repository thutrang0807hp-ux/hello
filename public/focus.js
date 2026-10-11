/* Weekly priorities use explicit dates and capacity; no guessed response rates or AI output. */
const FocusInsights=(()=>{
 const stage=c=>['talk','active','archive'].includes(c.clientGroup)?c.clientGroup:({'Đang làm việc':'active','Đang làm':'active','Hợp đồng đang mở':'active','Đã hoàn thành':'archive','Lưu trữ':'archive'}[c.status]||'talk');
 const shift=(day,n)=>{const d=new Date(day+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10);};
 const localDate=value=>{if(!value)return '';const d=new Date(value);if(!Number.isFinite(d.getTime()))return '';const parts=new Intl.DateTimeFormat('en',{timeZone:'Asia/Bangkok',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d);return ['year','month','day'].map(k=>parts.find(v=>v.type===k).value).join('-');};
 function build(records,day,capacity='unknown'){
  const weekday=new Date(day+'T00:00:00Z').getUTCDay(),start=shift(day,-((weekday+6)%7)),previousStart=shift(start,-7),next=shift(start,7);
  const inPrevious=value=>{const d=localDate(value);return d>=previousStart&&d<start;};
  const projects=records.filter(r=>r.kind==='project'),customers=records.filter(r=>r.kind==='client'&&stage(r)!=='archive'),talk=customers.filter(c=>stage(c)==='talk'),active=customers.filter(c=>stage(c)==='active');
  const due=customers.filter(c=>/^\d{4}-\d{2}-\d{2}$/.test(c.followup||'')&&c.followup<=day&&c.completedFollowup!==c.followup).sort((a,b)=>a.followup.localeCompare(b.followup));
  const quiet=active.filter(c=>/^\d{4}-\d{2}-\d{2}$/.test(c.lastReplyDate||'')&&c.lastReplyDate<=shift(day,-7));
  const sent=projects.filter(p=>inPrevious(p.sentAt)).length,won=projects.filter(p=>p.won&&inPrevious(p.wonAt)).length,priorities=[];
  if(due.length){const c=due[0];priorities.push({kind:'client',id:c.id,title:c.nextAction||'Liên hệ '+c.name,reason:`${c.name} · ${due.length} việc đến hạn cần xử lý.`,action:'Mở hồ sơ'});}
  const quietNext=quiet.find(c=>!priorities.some(p=>p.id===c.id));if(quietNext)priorities.push({kind:'client',id:quietNext.id,title:'Kiểm tra tiến độ với '+quietNext.name,reason:`Hợp đồng đang mở; chưa phản hồi từ ${quietNext.lastReplyDate}.`,action:'Mở hồ sơ'});
  if(capacity==='free'&&talk.length<=1&&won===0){priorities.push({kind:'job',title:'Tập trung tìm thêm khách',reason:`Tuần trước chốt ${won} hợp đồng; hiện có ${talk.length} khách đang trao đổi. Bạn đã xác nhận còn thời gian.`,action:'Chọn job phù hợp'});}
  else if(talk.length>=2){priorities.push({kind:'client-list',title:'Theo sát những khách đang trao đổi',reason:`Có ${talk.length} khách đang trao đổi hoặc test. Ưu tiên làm rõ bước tiếp theo trước khi tìm thêm.`,action:'Mở khách hàng'});}
  if(capacity==='busy'&&!priorities.length)priorities.push({kind:'client-list',title:'Giữ nhịp công việc đang làm',reason:'Bạn đã chọn đang bận bàn giao. Kiểm tra milestone và lịch duyệt với khách.',action:'Mở khách hàng'});
  if(!priorities.length)priorities.push({kind:'capacity',title:capacity==='unknown'?'Xác nhận sức tải tuần này':'Dành thời gian chọn cơ hội phù hợp',reason:capacity==='unknown'?'Chọn còn thời gian hay đang bận để gợi ý không thúc bạn tìm khách khi đang quá tải.':'Chưa có việc đến hạn; giữ nhịp tìm khách phù hợp với thời gian còn trống.',action:capacity==='unknown'?'Chọn sức tải':'Mở cơ hội công việc'});
  return {start,end:shift(next,-1),previousStart,previousEnd:shift(start,-1),sent,won,talk:talk.length,active:active.length,due,quiet,priorities:priorities.slice(0,3),capacity};
 }
 return {build,localDate,shift};
})();
if(typeof module!=='undefined')module.exports=FocusInsights;
