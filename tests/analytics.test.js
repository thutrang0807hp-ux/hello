const assert=require('node:assert/strict');const A=require('../public/analytics.js');const day='2026-10-11';
assert.equal(A.parts('2025-12-31T18:00:00Z').day,'2026-01-01');
let m=A.build([{id:1,kind:'job',postedAt:'2026-10-10T18:30:00Z',receivedAt:'2026-10-11T04:00:00Z'},{id:2,kind:'job',receivedAt:'2026-10-10T00:00:00Z'}],day,7);
assert.equal(m.heat[6][1],1);assert.equal(m.jobs,1);assert.equal(m.missing,1);assert.equal(m.dates.at(-1).count,1);
m=A.build([{kind:'job',postedAt:'2026-10-12T00:00:00Z'},{kind:'job',postedAt:'invalid'}],day,7);assert.equal(m.jobs,0);assert.equal(m.missing,1);
m=A.build([{id:1,kind:'job',postedAt:'2026-10-10T18:30:00Z',receivedAt:'2026-10-11T04:00:00Z'}],day,7,'received');assert.equal(m.heat[6][11],1);
const records=[{id:1,kind:'project',jobId:9,sentAt:'2026-10-06T09:00:00+07:00',won:true},{id:2,kind:'sentproposal',jobId:9,sentAt:'2026-10-06T09:00:00+07:00',outcome:'won',interaction:'unknown'},{id:3,kind:'sentproposal',jobId:9,sentAt:'2026-10-08T09:00:00+07:00',outcome:'pending',interaction:'replied'},{id:4,kind:'project',jobId:10,sentAt:'2026-10-07T00:00:00Z',won:false},{id:5,kind:'sentproposal',sentAt:'2026-10-07T00:00:00Z',outcome:'lost',interaction:'not_viewed'}];
m=A.build(records,day,7);assert.deepEqual(m.letterViews,{sent:3,viewed:1,notViewed:1,unknown:1,replied:1});assert.deepEqual(m.funnel,{sent:3,viewed:1,notViewed:1,unknown:1,replied:1,won:1,lost:1,pending:1});
m=A.build([{kind:'project',jobId:1,sentAt:'2026-09-01T00:00:00Z'},{kind:'sentproposal',jobId:1,sentAt:'2026-10-08T00:00:00Z'}],day,7);assert.equal(m.funnel.sent,0);
const snapshot={nodes:[{id:'used',type:'template',sourceId:22,title:'Used',content:'Hi'},{id:'unused',type:'template',title:'Ignore',content:'X'},{id:'draft',type:'draft'},{id:'final',type:'final'}],edges:[{from:'used',to:'draft'},{from:'draft',to:'final'}]};
let r={kind:'sentproposal',sentAt:'2026-10-07T00:00:00Z',workspaceSnapshot:snapshot,finalNodeId:'final',outcome:'pending'};m=A.build([r],day,7);assert.equal(m.templates.length,1);assert.equal(m.templates[0].name,'Used');assert.equal(m.templates[0].pending,1);assert.equal(m.templates[0].won,0);
assert.equal(A.templates({workspaceSnapshot:{nodes:[...snapshot.nodes,{id:'f2',type:'final'}],edges:snapshot.edges}}).length,0);
m=A.build([{kind:'client',clientTalkAt:'2026-10-06T00:00:00Z',clientGroup:'archive',clientStage:'closed-no-contract',clientLostReason:'price'},{kind:'client',clientTalkAt:'2026-10-07T00:00:00Z',clientGroup:'talk'},{kind:'client',clientTalkAt:'2026-10-08T00:00:00Z',clientContractAt:'2026-10-10T00:00:00Z',clientGroup:'archive',clientStage:'closed-contract'},{kind:'client',clientGroup:'active'}],day,7);
assert.equal(m.talk.nonCloseRate,50);assert.equal(m.talk.pending,1);assert.equal(m.talk.unknownDates,1);assert.equal(m.talk.reasons.find(r=>r.key==='price').count,1);
m=A.build([],day,30);assert.equal(m.funnel.unknown,0);assert.equal(m.talk.nonCloseRate,null);assert.match(m.suggestions[0],/Chưa đủ/);assert(m.suggestions.length<=3);
const few=[{kind:'job',postedAt:'2026-10-10T00:00:00Z',jobAssessment:{state:'unconfigured',color:'yellow'}},{kind:'job',postedAt:'2026-10-10T00:00:00Z',jobAssessment:{state:'completed',color:'green'}}];assert.equal(A.build(few,day,30,'posted',true).jobs,1);
assert(A.build([],day,30,'posted',false,'free').suggestions.some(s=>s.includes('tìm thêm')));assert(!A.build([],day,30,'posted',false,'busy').suggestions.some(s=>s.includes('tìm thêm')));

assert.equal(A.build([{kind:'project',jobId:1,sentAt:''},{kind:'sentproposal',jobId:1,sentAt:'2026-10-10T00:00:00Z'}],day,7).funnel.sent,1);
console.log('PASS: Vietnam hours/date boundaries, separate posted/received, missing/future dates, deduplicated sent cohorts, unknown view states, snapshot-only connected template attribution, unresolved conversation exclusion, evidence limits and capacity safeguards.');

const librarySnapshot={nodes:[{id:'library',type:'template',libraryMode:true,content:'Generic library fallback'},{id:'draft',type:'draft',referenceShortlist:[{id:'t-77',sourceId:77,name:'Shortlisted template'}]},{id:'final',type:'final'}],edges:[{from:'library',to:'draft'},{from:'draft',to:'final'}]};
m=A.build([{kind:'sentproposal',sentAt:'2026-10-07T00:00:00Z',workspaceSnapshot:librarySnapshot,finalNodeId:'final',outcome:'pending'}],day,7);assert.equal(m.templates.length,1);assert.equal(m.templates[0].name,'Shortlisted template');

assert.equal(A.build([], '2026-10-14',180).from,'2026-04-15');
assert.equal(A.build([], '2026-10-14',365).from,'2025-10-15');
assert.equal(A.build([], '2024-02-29',365).from,'2023-03-01');
