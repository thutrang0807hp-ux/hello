// Runs only when the user operates the extension on an authorized chatgpt.com tab.
(()=>{
 if(globalThis.__freelanceDeskChatGPT)return;
 globalThis.__freelanceDeskChatGPT=true;
 let lastPreview=null;
 function answers(id){
  if(document.querySelector('[data-testid="stop-button"],button[aria-label="Stop streaming"]'))throw Error('ChatGPT vẫn đang viết. Chờ xong rồi thử lại.');
  const marker='[Freelance Desk task: '+id+']';
  const messages=[...document.querySelectorAll('[data-message-author-role]')];
  const start=messages.findIndex(el=>el.dataset.messageAuthorRole==='user'&&(el.innerText||'').includes(marker));
  if(start<0)throw Error('Đây chưa phải cuộc chat của yêu cầu đang nối. Mở đúng cuộc chat hoặc đưa yêu cầu vào lại.');
  return messages.slice(start+1).filter(el=>el.dataset.messageAuthorRole==='assistant').map(el=>(el.querySelector('.markdown')||el).innerText?.trim()).filter(Boolean);
 }
 chrome.runtime.onMessage.addListener((message,sender,reply)=>{
  if(sender.id!==chrome.runtime.id||message?.target!=='freelance-desk-chatgpt-page')return;
  try{
   if(location.origin!=='https://chatgpt.com')throw Error('Chỉ dùng trên chatgpt.com.');
   if(message.action==='prepare'){
    const input=document.querySelector('#prompt-textarea,textarea[data-id="root"]');
    if(!input)throw Error('Chưa thấy ô chat. Đăng nhập ChatGPT và mở một cuộc chat thường trước.');
    const existing=(input.value??input.innerText??'').trim();
    if(existing)throw Error('Ô chat đang có nội dung. Gửi hoặc giữ lại nội dung đó trước; extension không ghi đè.');
    if(typeof message.prompt!=='string'||message.prompt.length>80000)throw Error('Nội dung không hợp lệ.');
    input.focus();
    if(input.tagName==='TEXTAREA'){
     Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,message.prompt);
     input.dispatchEvent(new Event('input',{bubbles:true}));
    }else{
     if(!document.execCommand('insertText',false,message.prompt)){
      input.textContent=message.prompt;input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:message.prompt}));
     }
    }
    reply({ok:true});return;
   }
   const list=answers(message.id);
   if(message.action==='answers'){lastPreview={id:message.id,list};reply({ok:true,answers:list.map((text,index)=>({index,preview:text.slice(0,180)}))});return;}
   if(message.action==='take'){
    if(!Number.isInteger(message.index)||!list[message.index])throw Error('Chọn câu trả lời hợp lệ.');
    const answer=list[message.index];if(!lastPreview||lastPreview.id!==message.id||lastPreview.list[message.index]!==answer)throw Error('Câu trả lời đã đổi. Xem danh sách lại trước khi lấy.');if(answer.length>20000)throw Error('Câu trả lời quá dài. Rút gọn trong chat trước.');
    reply({ok:true,answer});return;
   }
   throw Error('Thao tác không hợp lệ.');
  }catch(error){reply({ok:false,error:error.message});}
 });
})();
