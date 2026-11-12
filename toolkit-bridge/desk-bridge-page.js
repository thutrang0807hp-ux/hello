const $ = id => document.getElementById(id);
let busy = false;
async function command(action, extra = {}) {
  return chrome.runtime.sendMessage({ target: 'freelance-desk-bridge', action, ...extra });
}
function paint(value) {
  if (!value) { $('error').textContent = 'Cầu nối chưa phản hồi. Vào chrome://extensions và bấm Reload của bản Toolkit kết nối.'; return; }
  if ('enabled' in value) {
    $('status').textContent = value.enabled ? 'Kết nối đã bật' : 'Kết nối đang tắt';
    $('total').textContent = value.total || 0; $('pending').textContent = value.pending || 0;
    $('time').textContent = value.lastSuccess ? `Gửi thành công gần nhất: ${new Date(value.lastSuccess).toLocaleString('vi-VN')}` : 'Chưa có lần gửi thành công.';
    $('notice').textContent = [value.rejected ? `${value.rejected} job trong bộ nhớ thiếu ID hoặc tiêu đề nên chưa gửi.` : '', value.overflow ? `Hàng đợi đầy: ${value.overflow} job hiện có chưa vào hàng đợi. Mở web để giải phóng hàng đợi rồi gửi lại.` : ''].filter(Boolean).join(' ');
    if (value.configured && !$('endpoint').value) $('endpoint').placeholder = 'Đã lưu URL. Dán URL mới khi muốn đổi kết nối.';
  }
  $('error').textContent = value.error || '';
}
async function act(action) {
  if (busy) return; busy = true;
  document.querySelectorAll('button').forEach(button => button.disabled = true);
  try { paint(await command(action, action === 'connect' ? { url: $('endpoint').value.trim() } : {})); }
  catch { $('error').textContent = 'Không liên lạc được với cầu nối. Thử Reload tiện ích và mở lại trang này.'; }
  finally { busy = false; document.querySelectorAll('button').forEach(button => button.disabled = false); }
}
for (const action of ['connect', 'sync', 'stop']) $(action).addEventListener('click', () => act(action));
act('status');
setInterval(() => { if (!busy) act('status'); }, 5000);

let chatTasks=[];
const chatCommand=(action,extra={})=>chrome.runtime.sendMessage({target:'freelance-desk-chatgpt',action,...extra});
async function chatAct(action,extra={}){
 const status=$('chatStatus');
 try{
  const result=await chatCommand(action,extra);if(result?.error)throw Error(result.error);
  if(action==='tasks'){
   chatTasks=result.tasks||[];$('chatTask').replaceChildren(...chatTasks.map(t=>new Option('Workspace '+t.proposalId+' · '+new Date(t.createdAt).toLocaleString('vi-VN'),t.id)));
   $('chatTask').dispatchEvent(new Event('change'));
   status.textContent=chatTasks.length?'Chọn yêu cầu và kiểm tra nội dung trước khi đưa sang ChatGPT.':'Chưa có yêu cầu. Tạo từ node thư trong Proposal Studio.';
  }else if(action==='answers'){
   $('chatAnswer').replaceChildren(...(result.answers||[]).map(a=>new Option(a.preview,a.index)));
   status.textContent=result.answers?.length?'Chọn câu trả lời đúng rồi bấm Lấy câu trả lời về app.':'Chưa có câu trả lời hoàn chỉnh.';
  }else status.textContent=result.message||('enabled' in result?(result.enabled?'Kết nối ChatGPT đã bật.':'Chưa kết nối ChatGPT.'):'Đã mở ChatGPT.');
  if(action==='disconnect'){chatTasks=[];$('chatTask').replaceChildren();$('chatAnswer').replaceChildren();$('chatPrompt').value='';}
 }catch(error){status.textContent=error.message;}
}
$('chatEnable').onclick=async()=>{try{const granted=await chrome.permissions.request({origins:['https://chatgpt.com/*']});if(granted)await chatAct('enable');else $('chatStatus').textContent='Chưa cấp quyền cho trang ChatGPT.';}catch{$('chatStatus').textContent='Hãy Reload bản tiện ích mới có quyền ChatGPT.';}};
$('chatOpen').onclick=()=>chatAct('open');
$('chatDisconnect').onclick=()=>chatAct('disconnect');
$('chatRefresh').onclick=()=>chatAct('tasks');
$('chatTask').onchange=()=>{$('chatPrompt').value=chatTasks.find(t=>t.id===$('chatTask').value)?.prompt||'';};
$('chatPrepare').onclick=()=>chatAct('prepare',{id:$('chatTask').value});
$('chatAnswers').onclick=()=>chatAct('answers');
$('chatTake').onclick=()=>chatAct('take',{index:$('chatAnswer').value===''?-1:Number($('chatAnswer').value)});
chatAct('status');
