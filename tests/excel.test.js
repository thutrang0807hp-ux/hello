const assert=require('node:assert/strict');const {spawnSync}=require('node:child_process');const E=require('../public/excel.js');
const records=[{id:1,kind:'project',name:'=1+1 & <job>',sentAt:'2026-09-30T18:00:00Z',won:true,wonAt:'2026-10-10T00:00:00Z'},{id:2,kind:'project',name:'Sent earlier, won now',sentAt:'2026-08-01T00:00:00Z',won:true,wonAt:'2026-10-11T00:00:00Z'},{id:3,kind:'project',name:'Exclude',sentAt:'2026-08-01T00:00:00Z',won:false},{id:4,kind:'client',name:'Khách Việt',clientGroup:'archive'},{id:5,kind:'sentproposal',name:'Thư',sentAt:'2026-10-11T00:00:00Z',body:'Xin chào\nDòng hai',interaction:'replied'}];
const sheets=E.monthSheets(records,'2026',10,'2026-10-11','Gợi ý');assert.equal(sheets[0].rows[2][1],1);assert.equal(sheets[0].rows[3][1],2);assert.equal(sheets[1].rows.length,3);assert.equal(sheets[3].rows[1][4],'Khách đã phản hồi');assert.equal(sheets[1].rows[1][3],'2026-10-01');
const bytes=E.workbook(sheets);
const result=spawnSync('python3',['-c',`import io,zipfile,xml.etree.ElementTree as ET
z=zipfile.ZipFile(io.BytesIO(__import__('sys').stdin.buffer.read()))
assert z.testzip() is None
for name in z.namelist(): ET.fromstring(z.read(name))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
w=ET.fromstring(z.read('xl/workbook.xml')); assert [x.attrib['name'] for x in w.findall('s:sheets/s:sheet',ns)]==['Tổng hợp','Công việc','Khách hàng','Thư đã gửi']
r=ET.fromstring(z.read('xl/worksheets/sheet2.xml')); cells={x.attrib['r']:x for x in r.findall('.//s:c',ns)}
assert cells['A2'].attrib['t']=='inlineStr'; assert cells['A2'].find('s:is/s:t',ns).text=='=1+1 & <job>'; assert not r.findall('.//s:f',ns)
assert r.find('s:sheetViews/s:sheetView/s:pane',ns).attrib['topLeftCell']=='A2'
assert r.find('s:autoFilter',ns) is not None
`],{input:bytes});assert.equal(result.status,0,result.stderr?.toString());
console.log('PASS: real XLSX ZIP/XML, Vietnamese sheets and text, numeric summary, timezone month bounds, deduplicated sent/won rows, frozen headers, filters and formula-like text kept literal.');
