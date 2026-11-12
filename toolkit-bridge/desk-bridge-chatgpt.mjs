import { validateEndpoint, KEY } from './desk-bridge-core.mjs';
export const CHAT_KEY='__FREELANCE_DESK_CHATGPT_V1';
export function bridgeURL(value){const url=new URL(validateEndpoint(value));url.pathname=url.pathname.replace('/api/webhook/','/api/chatgpt-bridge/');return url.href;}
export function chatURL(value){try{const u=new URL(value);return u.protocol==='https:'&&u.hostname==='chatgpt.com'&&!u.username&&!u.password;}catch{return false;}}
export function installChatGPT(api,request=fetch){
  let chain=Promise.resolve();
  const load=async()=>(await api.storage.local.get(CHAT_KEY))[CHAT_KEY]||{enabled:false};
  const store=state=>api.storage.local.set({[CHAT_KEY]:state});
  async function remote(body){
    const settings=(await api.storage.local.get(KEY))[KEY];
    if(!settings?.url)throw Error('Lưu URL nhận job ở phần kết nối phía trên trước.');
    const response=await request(bridgeURL(settings.url),{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},...(body?{body:JSON.stringify(body)}:{}),credentials:'omit',redirect:'error',cache:'no-store',signal:AbortSignal.timeout(10000)});
    if(!response.ok)throw Error('Freelance Desk chưa phản hồi hoặc URL đã đổi. Mở app và kiểm tra kết nối.');
    return response.json();
  }
  async function tab(state){
    const tabs=await api.tabs.query({url:'https://chatgpt.com/*'});
    const found=tabs.find(t=>t.id===state.tabId)||tabs.find(t=>t.active)||tabs[0];
    if(!found||!chatURL(found.url))throw Error('Mở tab chatgpt.com và đăng nhập bằng Chrome trước.');
    return found;
  }
  async function content(state,action,extra={}){
    const current=await tab(state);
    await api.scripting.executeScript({target:{tabId:current.id},files:['desk-bridge-chatgpt-content.js']});
    const result=await api.tabs.sendMessage(current.id,{target:'freelance-desk-chatgpt-page',action,...extra});
    if(!result?.ok)throw Error(result?.error||'Trang ChatGPT đã thay đổi hoặc chưa sẵn sàng. Thử tải lại trang.');
    return {current,result};
  }
  async function run(message){
    let state=await load();
    if(message.action==='status')return {enabled:!!state.enabled,taskId:state.taskId||''};
    if(message.action==='enable'){await store({enabled:true});return {enabled:true};}
    if(message.action==='disconnect'){await api.storage.local.remove(CHAT_KEY);return {enabled:false};}
    if(!state.enabled)throw Error('Bật kết nối ChatGPT trước.');
    if(message.action==='open'){await api.tabs.create({url:'https://chatgpt.com/',active:true});return {ok:true};}
    if(message.action==='tasks')return remote();
    if(message.action==='prepare'){
      const tasks=(await remote()).tasks;const task=tasks.find(t=>t.id===message.id);
      if(!task)throw Error('Yêu cầu đã đổi. Bấm Làm mới yêu cầu.');
      const {current}=await content(state,'prepare',{prompt:task.prompt});
      state={enabled:true,tabId:current.id,taskId:task.id};await store(state);
      await api.tabs.update(current.id,{active:true});
      return {ok:true,message:'Đã điền nội dung. Kiểm tra rồi tự bấm Gửi trong ChatGPT.'};
    }
    if(!state.taskId)throw Error('Đưa một yêu cầu từ Freelance Desk vào ChatGPT trước.');
    if(message.action==='answers')return (await content(state,'answers',{id:state.taskId})).result;
    if(message.action==='take'){
      const {result}=await content(state,'take',{id:state.taskId,index:message.index});
      await remote({id:state.taskId,answer:result.answer});
      return {ok:true,message:'Đã đưa câu trả lời về app. Trong node thư, bấm Kiểm tra câu trả lời để xem trước.'};
    }
    throw Error('Thao tác không hợp lệ.');
  }
  api.runtime.onMessage.addListener((message,sender,reply)=>{
    if(message?.target!=='freelance-desk-chatgpt'||sender.id!==api.runtime.id||sender.tab||sender.url!==api.runtime.getURL('desk-bridge.html'))return;
    const result=chain.then(()=>run(message));chain=result.catch(()=>{});
    result.then(reply).catch(error=>reply({error:error.message||'Chưa kết nối được. Giữ bản nháp trong app rồi thử lại.'}));return true;
  });
  return {run};
}
