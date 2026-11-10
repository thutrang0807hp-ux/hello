const assert=require('node:assert/strict');const A=require('../public/analytics.js');const day='2026-10-11';
// Removed jobs ('jobstat') still count in the job rhythm chart, and respect the quality filter.
const records=[{id:1,kind:'job',postedAt:'2026-10-10T03:00:00Z'},{kind:'jobstat',postedAt:'2026-10-09T03:00:00Z',jobAssessment:{state:'completed',color:'green'}},{kind:'jobstat',postedAt:'2026-10-08T03:00:00Z',jobAssessment:{state:'not_evaluated',color:'yellow'}}];
assert.equal(A.build(records,day,7).jobs,3);
assert.equal(A.build(records,day,7,'posted',true).jobs,1);
