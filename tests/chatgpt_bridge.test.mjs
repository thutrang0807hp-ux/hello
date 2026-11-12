import test from 'node:test';
import assert from 'node:assert/strict';
import {installChatGPT,CHAT_KEY,bridgeURL,chatURL} from '../toolkit-bridge/desk-bridge-chatgpt.mjs';
import {KEY} from '../toolkit-bridge/desk-bridge-core.mjs';

test('only local app endpoint and real ChatGPT origin are allowed',()=>{
 assert.equal(bridgeURL('http://127.0.0.1:8000/api/webhook/'+'x'.repeat(24)),'http://127.0.0.1:8000/api/chatgpt-bridge/'+'x'.repeat(24));
 for(const url of ['https://evil.example/api/webhook/'+ 'x'.repeat(24),'http://127.0.0.1:8000/api/webhook/x?secret=y'])assert.throws(()=>bridgeURL(url));
 assert.equal(chatURL('https://chatgpt.com/c/test'),true);
 for(const url of ['https://chatgpt.com.evil.example/','https://chatgpt.com@evil.example/','http://chatgpt.com'])assert.equal(chatURL(url),false);
});

test('user-driven handoff, no cookie access, disconnect preserves job bridge',async()=>{
 const data={[KEY]:{enabled:true,url:'http://127.0.0.1:8000/api/webhook/'+'x'.repeat(24)}};
 const posts=[];let listener,action;
 const api={runtime:{id:'a'.repeat(32),getURL:p=>'chrome-extension://'+'a'.repeat(32)+'/'+p,onMessage:{addListener:l=>listener=l}},storage:{local:{get:async key=>({[key]:data[key]}),set:async obj=>Object.assign(data,obj),remove:async key=>delete data[key]}},tabs:{query:async()=>[{id:7,url:'https://chatgpt.com/',active:true}],create:async()=>{},update:async()=>{},sendMessage:async(id,message)=>{action=message.action;return {ok:true,answer:'The selected proposal',answers:[{index:0,preview:'The selected'}]};}},scripting:{executeScript:async()=>{}}};
 const bridge=installChatGPT(api,async(url,options)=>{posts.push({url,options});return {ok:true,json:async()=>options.method==='GET'?{tasks:[{id:'task1',prompt:'Prompt fixture'}]}:{ok:true}};});
 await assert.rejects(()=>bridge.run({action:'tasks'}));
 await bridge.run({action:'enable'});await bridge.run({action:'prepare',id:'task1'});
 assert.equal(action,'prepare');assert.equal(data[CHAT_KEY].taskId,'task1');
 await bridge.run({action:'answers'});await bridge.run({action:'take',index:0});
 assert.equal(JSON.parse(posts.at(-1).options.body).answer,'The selected proposal');
 assert.equal(posts.at(-1).options.credentials,'omit');
 await bridge.run({action:'disconnect'});assert.equal(data[CHAT_KEY],undefined);assert.equal(data[KEY].enabled,true);
 let replied=false;assert.equal(listener({target:'freelance-desk-chatgpt',action:'enable'},{id:api.runtime.id,tab:{id:7},url:'https://chatgpt.com/'},()=>{replied=true}),undefined);assert.equal(replied,false);
});
