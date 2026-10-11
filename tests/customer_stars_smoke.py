import os,tempfile,threading,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 os.environ.update(FREELANCE_DATA_DIR=tmp,FREELANCE_AI_KEY='fake-key',FREELANCE_AI_PROVIDER='openai',FREELANCE_AI_AUTO_JOBS='1',FREELANCE_PASSWORD='')
 import server
 clients=[{'rating':5,'totalHires':50,'hireRate':90,'paymentVerified':True},{'rating':3,'totalHires':5,'hireRate':40,'paymentVerified':True},{'rating':1,'totalHires':0,'hireRate':0,'paymentVerified':False},{'rating':5}]
 server.import_jobs({'event':'new_jobs','jobs':[{'id':str(i),'title':'Job '+str(i),'url':'https://www.upwork.com/jobs/~'+str(i),'description':'Design website','client':c} for i,c in enumerate(clients)]})
 http=server.ThreadingHTTPServer(('127.0.0.1',8798),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 review={'summary':'Thiết kế trang web.','budgetScore':20,'clarityScore':18,'safetyScore':14,'priceComment':'Cần xác nhận giá.','clarityComment':'Cần xác nhận phạm vi.','riskComment':'Chưa thấy dấu hiệu đáng ngờ.','warnings':[]}
 try:
  with patch('server.job_radar.evaluate',return_value=review) as evaluate,sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1400,'height':950});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8798');page.wait_for_function('()=>initialized');page.evaluate("changeView('job')");page.wait_for_selector('.customer-star-filters')
   page.locator('[data-radar-job]').first.hover();page.wait_for_timeout(700);assert page.locator('.job-popover').count()==0;assert evaluate.call_count==0
   for group in ['high','mid','low','unknown']:
    page.locator('[data-customer-star-filter='+group+']').click();assert page.locator('[data-radar-job]').count()==1
   page.locator('[data-customer-star-filter=high]').click();page.locator('.primary[data-job-open]').click();page.wait_for_selector('#jobDetailDialog[open]');assert evaluate.call_count==0;assert page.locator('#jobAiContent').is_hidden();assert page.locator('[data-job-detail]').count()==0;page.locator('#runJobAnalysis').click();page.wait_for_selector('.job-ai-saved');assert evaluate.call_count==1
   page.locator('#runJobAnalysis').click();assert page.locator('#jobAiContent').is_hidden();page.locator('#runJobAnalysis').click();assert page.locator('#jobAiContent').is_visible();assert evaluate.call_count==1;page.locator('#closeJobDetail').click();page.locator('.primary[data-job-open]').click();assert page.locator('#jobAiContent').is_hidden();page.locator('#runJobAnalysis').click();page.wait_for_selector('.job-ai-saved');assert evaluate.call_count==1
   page.locator('#closeJobDetail').click();page.locator('[data-customer-star-filter=all]').click();assert page.locator('[data-radar-job]').count()==4
   page.evaluate("document.documentElement.dataset.theme='dark'");assert page.locator('[data-radar-job]').count()==4;assert not errors,errors
   b.close();print('PASS single job analysis button; AI collapsed on open; explicit request once; collapse and cached reopening use no API')
 finally:http.shutdown();http.server_close()
