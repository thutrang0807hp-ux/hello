const assert=require('node:assert/strict'),F=require('../public/focus.js');
const client=(id,group,extra={})=>({id,kind:'client',name:'Khách '+id,clientGroup:group,...extra});
let r=F.build([], '2026-10-11','free');
assert.equal(r.start,'2026-10-05');assert.equal(r.previousStart,'2026-09-28');assert.equal(r.previousEnd,'2026-10-04');assert.equal(r.priorities[0].title,'Tập trung tìm thêm khách');
assert.equal(F.build([],'2026-10-11','unknown').priorities[0].kind,'capacity');
assert(!F.build([],'2026-10-11','busy').priorities.some(p=>p.kind==='job'));
r=F.build([client(1,'talk'),client(2,'talk')],'2026-10-11','free');assert.equal(r.priorities[0].kind,'client-list');
const records=[client(1,'active',{followup:'2026-10-10',lastReplyDate:'2026-09-29',nextAction:'Duyệt milestone'}),client(2,'archive',{followup:'2026-10-01',lastReplyDate:'2026-09-01'}),client(3,'active')];
r=F.build(records,'2026-10-11','free');assert.equal(r.due.length,1);assert.equal(r.quiet.length,1);assert.equal(r.priorities.filter(p=>p.id===1).length,1);assert(r.priorities.length<=3);
records[0].completedFollowup='2026-10-10';assert.equal(F.build(records,'2026-10-11').due.length,0);
records[0].followup='2026-10-11';assert.equal(F.build(records,'2026-10-11').due.length,1);
r=F.build([{kind:'project',sentAt:'2026-10-04T16:59:00Z',won:true,wonAt:'2026-10-04T17:00:00Z'}],'2026-10-11','free');assert.equal(r.sent,1);assert.equal(r.won,0);
r=F.build([{kind:'project',sentAt:'2026-12-31T18:00:00Z',won:true,wonAt:'2027-01-03T16:00:00Z'}],'2027-01-04','free');assert.equal(r.previousStart,'2026-12-28');assert.equal(r.sent,1);assert.equal(r.won,1);assert(!r.priorities.some(p=>p.title==='Tập trung tìm thêm khách'));
console.log('PASS: previous completed week, Vietnam date boundary, capacity safeguards, sparse pipeline, due/quiet deduplication, archived/missing dates and followup completion.');

const paused=F.build([client(9,'active',{clientStage:'paused',lastReplyDate:'2026-09-01'})],'2026-10-11');assert.equal(paused.active,1);assert.equal(paused.quiet.length,0);
