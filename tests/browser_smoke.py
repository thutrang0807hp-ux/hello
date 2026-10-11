"""Run with Playwright and a local Chromium installed; uses isolated test data."""
import json
import os
import secrets
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def navigate(page, target):
    if page.locator('#mobileMenu').is_visible() and page.locator('#mobileMenu').get_attribute('aria-expanded')!='true':
        page.locator('#mobileMenu').click()
    if not page.locator('#mobileMenu').is_visible():
        page.locator('#appSidebar').hover()
        page.wait_for_function("()=>document.querySelector('#appSidebar').getBoundingClientRect().width>=244")
    page.locator('[data-view='+('job' if target=='project' else target)+']').click()
    if not page.locator('#mobileMenu').is_visible():
        page.mouse.move(1000,100)
        page.wait_for_function("()=>document.querySelector('#appSidebar').getBoundingClientRect().width<77")
    if target=='project':page.locator('[data-work-view=project]').click()

with tempfile.TemporaryDirectory() as data:
    password = secrets.token_urlsafe(24)
    env = dict(os.environ, FREELANCE_DATA_DIR=data, FREELANCE_PASSWORD=password, PORT='8766')
    for key in ['FREELANCE_AI_KEY', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_TELEGRAM_TOKEN']:
        env.pop(key, None)
    process = subprocess.Popen(['python3', 'server.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen('http://127.0.0.1:8766/api/auth', timeout=1)
                break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1360, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:8766/')
            page.locator('#login input').fill(password)
            page.locator('#login button[type=submit]').click()
            page.wait_for_selector('#login', state='hidden')
            created=page.request.post('http://127.0.0.1:8766/api/records',data={'kind':'messageTemplate','name':'Greeting','category':'Chào hỏi','body':'Hello [Client]'}).json()
            assert created.get('id') and created['body']=='Hello [Client]'
            updated=page.request.post('http://127.0.0.1:8766/api/records',data={'id':created['id'],'kind':'messageTemplate','name':'Greeting','category':'Custom','body':'Updated'}).json()
            assert updated['category']=='Custom' and updated['body']=='Updated'
            assert page.request.post('http://127.0.0.1:8766/api/records',data={'kind':'messageTemplate','name':'Empty','category':'Test','body':''}).status==400
            assert page.request.delete('http://127.0.0.1:8766/api/records/'+str(created['id'])).ok
            page.locator('#themeToggle').click()
            assert page.locator('html').get_attribute('data-theme')=='dark'
            page.reload()
            page.wait_for_selector('#themeToggle')
            assert page.locator('html').get_attribute('data-theme')=='light'
            navigate(page,'client')
            page.locator('#add').click()
            page.locator('#form input[name=name]').fill('Demo client')
            page.locator('#form textarea[name=notes]').fill('Discussed a dashboard project')
            page.locator('#form button[type=submit]').click()
            page.wait_for_selector('.card h3:text-is("Demo client")')
            assert page.locator('.client-column').count()==3
            assert page.locator('.client-column.talk .client-card').count()==1
            page.locator('[data-client-open]').click()
            page.locator('#editClientDetail').click()
            page.locator('[name=clientGroup]').select_option('active')
            page.locator('[name=situation]').fill('Milestone đang mở, chờ khách duyệt')
            page.locator('[name=nextAction]').fill('Nhắc khách duyệt thiết kế')
            page.locator('[name=followup]').fill('2020-01-01')
            page.locator('[name=lastReplyDate]').fill('2026-01-01')
            page.locator('#form button[type=submit]').click()
            page.wait_for_selector('.client-column.active .client-card')
            assert page.locator('.client-card').count()==1
            page.locator('[data-client-replied]').click()
            page.wait_for_selector('.client-response:has-text("Khách phản hồi hôm nay")')
            page.reload()
            navigate(page,'client')
            page.wait_for_selector('.client-column.active .client-card')
            assert 'Khách phản hồi hôm nay' in page.locator('.client-response').inner_text()
            navigate(page,'overview')
            assert page.locator('[data-task-kind=due]').count()==1
            assert page.locator('.sent-overview,.radar-job').count()==0
            page.locator('[data-overview-done]').click()
            page.wait_for_selector('[data-task-kind=due]',state='detached')
            page.reload()
            page.wait_for_selector('.overview-workspace')
            assert page.locator('[data-task-kind=due]').count()==0
            navigate(page,'client')

            page.locator('[data-client-open]').click()
            page.locator('#editClientDetail').click()
            page.locator('[name=clientGroup]').select_option('archive')
            page.locator('#form button[type=submit]').click()
            page.wait_for_selector('.client-column.archive .client-card')
            assert page.locator('.client-card').count()==1
            page.locator('#clientGmail').click()
            assert 'Chưa cấu hình đăng nhập Google' in page.locator('#clientGmailDialog').inner_text()
            assert page.locator('#linkClientMail').count()==0
            page.locator('#clientGmailDialog [data-client-close]').click()

            navigate(page,'settings')
            page.wait_for_selector('#profileForm')
            page.locator('#profileForm input[name=name]').fill('Trang')
            page.locator('#profileForm textarea[name=services]').fill('Web application development')
            page.locator('#profileForm textarea[name=experience]').fill('Built a portfolio dashboard')
            page.locator('#profileForm button[type=submit]').click()
            page.wait_for_selector('#profileMessage:text-is("Đã lưu hồ sơ.")')
            path = page.request.get('http://127.0.0.1:8766/api/settings').json()['webhookPath']
            payload = {'event': 'new_jobs', 'count': 1, 'jobs': [{'id': '~browser-test', 'title': 'Customer dashboard with search', 'url': 'https://www.upwork.com/jobs/~browser-test', 'description': 'Build a CRM with search and export.', 'budget': '$500', 'type':'Fixed', 'skills': ['Python', 'SQLite'], 'client': {'country': 'United States', 'paymentVerified': True}}]}
            assert page.request.post('http://127.0.0.1:8766' + path, data=payload).json()['created'] == 1
            page.reload()
            page.wait_for_selector('.overview-workspace')
            navigate(page,'job')
            assert not page.locator('#stats').is_visible()
            assert not page.locator('#add').is_visible()
            assert not page.locator('.toolbar').is_visible()
            assert page.locator('.job-list-tools #search').is_visible()
            page.locator('#search').fill('not-a-matching-job')
            assert page.locator('.radar-job').count()==0
            assert page.locator('#search').input_value()=='not-a-matching-job'
            assert page.locator('#search').evaluate('(el)=>el===document.activeElement')
            page.locator('#search').fill('dashboard')
            assert page.locator('.radar-job').count()==1
            page.locator('#search').fill('')
            page.set_viewport_size({'width':980,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            assert page.locator('.radar-job').bounding_box()['height']<280
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            assert page.locator('.radar-job .actions [data-job-open]').is_visible()
            page.set_viewport_size({'width':1360,'height':1000})
            page.locator('#openJobFilters').click()
            page.locator('[data-filter-enabled=country]').check()
            assert page.locator('#applyJobFilters').is_disabled()
            page.locator('[data-filter-value=country][value="United States"]').check()
            page.locator('[data-filter-enabled=keywords]').check()
            page.locator('[name=includeKeywords]').fill('dashboard, search')
            page.locator('[name=keywordMode][value=all]').check()
            page.locator('[data-filter-enabled=budget]').check()
            page.locator('[name=filterBudgetMin]').fill('400')
            page.locator('[name=filterBudgetMax]').fill('600')
            page.locator('[data-filter-enabled=sent]').check()
            assert '1 job phù hợp' in page.locator('#jobFilterPreview').inner_text()
            page.locator('[name=filterBudgetMin]').fill('700')
            assert page.locator('#applyJobFilters').is_disabled()
            page.locator('[name=filterBudgetMin]').fill('400')
            page.locator('#applyJobFilters').click()
            assert page.locator('.radar-job').count()==1
            assert page.locator('[data-clear-condition]').count()==4
            page.reload()
            navigate(page,'job')
            assert page.locator('[data-clear-condition]').count()==4
            page.locator('#openJobFilters').click()
            page.locator('[name=includeKeywords]').fill('no-match')
            assert '0 job phù hợp' in page.locator('#jobFilterPreview').inner_text()
            page.locator('#cancelJobFilters').click()
            assert page.locator('.radar-job').count()==1
            page.locator('#openJobFilters').click()
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('#jobFilterDialog').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            page.keyboard.press('Escape')
            page.set_viewport_size({'width':1360,'height':1000})
            page.locator('[data-clear-conditions]').click()
            assert page.locator('[data-clear-condition]').count()==0
            marker=page.locator('[data-proposal-sent]')
            assert marker.get_attribute('aria-checked')=='false'
            marker.click()
            page.wait_for_selector('[data-proposal-sent][aria-checked=true]')
            assert 'is-sent' in page.locator('[data-proposal-sent]').get_attribute('class')
            navigate(page,'overview')
            assert page.locator('.overview-metric').first.locator('strong').text_content()=='1'
            assert page.locator('.sent-overview,.radar-job').count()==0
            navigate(page,'project')
            assert page.locator('.project-card').count()==1
            contract=page.locator('[data-project-contract]')
            contract.check()
            page.wait_for_selector('.project-card.won')
            page.reload()
            navigate(page,'project')
            assert page.locator('[data-project-contract]').is_checked()
            current_month=page.locator('#projectMonth').input_value()
            current_year=page.locator('#projectMonthYear').input_value()
            previous_month='12' if current_month=='01' else str(int(current_month)-1).zfill(2)
            page.locator('#projectPreviousMonth').click()
            assert page.locator('#projectMonth').input_value()==previous_month
            assert page.locator('.project-card').count()==0
            page.locator('[data-project-section=won]').click()
            assert page.locator('.project-card.won').count()==1
            assert page.locator('#projectMonth').count()==0
            page.locator('[data-project-section=tracking]').click()
            page.locator('#projectNextMonth').click()
            assert page.locator('#projectMonth').input_value()==current_month
            assert page.locator('#projectMonthYear').input_value()==current_year
            page.locator('#projectMonth').select_option(previous_month)
            assert page.locator('.project-card').count()==0
            page.locator('#projectMonthYear').select_option(str(int(current_year)-1))
            assert page.locator('.project-card').count()==0
            page.locator('#projectCurrentMonth').click()
            assert page.locator('.project-card.won').count()==1
            page.locator('[data-project-contract]').uncheck()
            page.wait_for_selector('.project-card:not(.won)')
            navigate(page,'overview')
            assert page.locator('[data-overview-month]').count()==12
            page.locator('[data-overview-month="1"]').click()
            assert 'Tháng 1' in page.locator('.overview-month-summary h3').inner_text()

            page.reload()
            page.wait_for_selector('.overview-workspace')
            navigate(page,'job')
            page.locator('[data-proposal-sent]').click()
            page.wait_for_selector('[data-proposal-sent][aria-checked=false]')
            page.locator('[data-interest]').click()
            page.wait_for_selector('[data-interest][aria-pressed=true]')
            page.locator('[data-job-filter=interest]').click()
            assert page.locator('.radar-job').count()==1
            page.locator('[data-job-detail]').click()
            page.wait_for_selector('.job-popover')
            assert 'Chưa bật AI' in page.locator('.job-popover').inner_text()
            page.keyboard.press('Escape')
            assert page.locator('[data-draft]').count()==0
            page.locator('.radar-job .actions [data-job-open]').click()
            page.wait_for_selector('#jobDetailDialog[open]')
            assert 'Khách xem job: chưa có dữ liệu' in page.locator('#jobDetailDialog').inner_text()
            assert page.locator('#jobDescriptionText').inner_text()=='Build a CRM with search and export.'
            assert page.locator('#jobDetailDialog input:visible').count()==0
            assert not page.locator('#descriptionEdit').is_visible()
            page.locator('#supplementDescription').click()
            page.locator('#jobDescriptionInput').fill('This change will be cancelled.')
            page.locator('#cancelDescription').click()
            assert page.locator('#jobDescriptionText').inner_text()=='Build a CRM with search and export.'
            page.locator('#supplementDescription').click()
            page.locator('#jobDescriptionInput').fill('Build a CRM with search and export. Two dashboard screens.')
            page.locator('#saveDescription').click()
            page.wait_for_selector('#descriptionEdit',state='hidden')
            assert 'Two dashboard screens.' in page.locator('#jobDescriptionText').inner_text()
            page.locator('.activity-manual summary').click()
            page.locator('#clientViewedInput').fill('2026-10-10T12:00')
            page.locator('#saveClientActivity').click()
            page.wait_for_selector('#notice:text-is("Đã ghi nhận hoạt động khách từ Upwork.")')
            assert 'Khách chưa quay lại' in page.locator('#jobDetailDialog').inner_text()
            page.locator('.activity-history summary').click()
            assert page.locator('.activity-history li').count()==1
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            assert page.locator('#jobDetailDialog').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            page.keyboard.press('Escape')
            page.set_viewport_size({'width':1360,'height':1000})
            page.evaluate('(id)=>Jobs.details(id)', next(r['id'] for r in page.request.get('http://127.0.0.1:8766/api/records').json() if r['kind']=='job'))
            page.locator('#writeJobProposal').click()
            page.wait_for_selector('#nodeCanvas')
            assert page.locator('#nodeInspector').is_visible()
            page.locator('[name=nodeJob]').select_option(str(next(r['id'] for r in page.request.get('http://127.0.0.1:8766/api/records').json() if r['kind']=='job')))
            assert page.locator('[name=nodeContent]').input_value() == 'Build a CRM with search and export. Two dashboard screens.'
            page.locator('[data-node="draft"]').click()
            assert page.locator('[name=nodeSignature]').input_value() == 'Trang'
            page.locator('#runNodeAI').click()
            page.wait_for_selector('#notice:text-matches("Chưa cấu hình khóa AI")')
            letter='Hi, I can build your CRM with search and export. Shall we confirm the scope?'
            page.route('**/api/ai/proposal', lambda route: route.fulfill(content_type='application/json', body=json.dumps({'body':letter, 'model':'UI-test-stub'})))
            page.locator('#runNodeAI').click()
            page.wait_for_function("()=>document.querySelector('[name=nodeContent]').value.includes('confirm the scope')")
            page.locator('[data-node="review"]').click()
            review={'score':84,'summary':'Specific and concise','strengths':['Matches the job'],'weaknesses':['Timeline missing'],'suggestions':['Confirm timeline'],'criteria':[{'name':str(i),'score':84,'reason':'From supplied text'} for i in range(4)]}
            page.route('**/api/ai/review', lambda route: route.fulfill(content_type='application/json', body=json.dumps({'review':review,'model':'UI-test-stub'})))
            page.locator('#runNodeAI').click()
            page.wait_for_selector('.review-score')
            assert '84' in page.locator('.review-score').inner_text()
            page.locator('[data-node="draft"]').click()
            page.locator('[name=nodeContent]').fill(letter+' Updated wording.')
            page.locator('[data-node="review"]').click()
            page.wait_for_selector('.review-stale')
            page.locator('#runNodeAI').click()
            page.wait_for_selector('.review-stale',state='hidden')
            page.locator('[data-add-node=template]').click()
            page.locator('.editor-connections > summary').click()
            page.locator('[name=nodeTitle]').fill('My second template')
            page.locator('[name=nodeContent]').fill('A reusable opening and evidence framework.')
            new_node=page.locator('.flow-node.selected').get_attribute('data-node')
            page.locator('[data-port-out="'+new_node+'"]').click()
            page.locator('[data-port-in=draft]').click()
            page.locator('#saveTemplate').click()
            page.wait_for_selector('#notice:text-matches("Đã lưu mẫu")')
            page.locator('[data-node=final]').click()
            page.locator('.editor-options > summary').click()
            page.locator('#copyDraftToFinal').click()
            assert 'Updated wording' in page.locator('[name=nodeContent]').input_value()
            page.locator('#saveWorkspace').click()
            page.wait_for_selector('#studioSaveState:text-is("Đã lưu")')
            heading=page.locator('[data-drag=job]')
            heading.scroll_into_view_if_needed()
            box=heading.bounding_box()
            page.mouse.move(box['x']+30,box['y']+20)
            page.mouse.down();page.mouse.move(box['x']+70,box['y']+55,steps=5);page.mouse.up()
            page.locator('#saveWorkspace').click()
            page.wait_for_selector('#studioSaveState:text-is("Đã lưu")')
            page.reload()
            page.wait_for_selector('.overview-workspace')
            navigate(page,'proposal')
            page.wait_for_selector('#nodeCanvas')
            assert page.locator('.flow-node').count()==6
            saved=next(r for r in page.request.get('http://127.0.0.1:8766/api/records').json() if r['kind']=='proposal')
            assert any(e['from']==new_node and e['to']=='draft' for e in saved['workspace']['edges'])
            assert next(n for n in saved['workspace']['nodes'] if n['id']=='job')['x']>45
            page.locator('[data-node=final]').click()
            page.on('dialog',lambda dialog:dialog.accept())
            page.locator('#archiveFinal').click()
            page.wait_for_selector('#notice:text-matches("Đã lưu bản thư đã gửi")')
            page.locator('[data-studio-tab=archive]').click()
            page.wait_for_selector('.archive-card')
            page.locator('[data-open-sent]').click()
            assert page.locator('.sent-body').input_value()==letter+' Updated wording.'
            page.locator('[name=sentOutcome]').select_option('won')
            page.locator('[name=sentInteraction]').select_option('replied')
            page.locator('[name=contractValue]').fill('$500')
            page.locator('#saveOutcome').click()
            page.wait_for_selector('.outcome-won')
            page.locator('[data-template-from-sent]').click()
            page.wait_for_selector('.won-tag')
            assert page.locator('.flow-node').count()==7
            page.locator('#saveWorkspace').click()
            page.wait_for_selector('#studioSaveState:text-is("Đã lưu")')
            page.screenshot(path='/tmp/freelance-desk-studio.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            navigate(page,'overview')
            page.locator('#openMonthlyReport').click()
            with page.expect_download() as download:
                page.locator('#downloadMonthlyReport').click()
            assert download.value.suggested_filename.endswith('.xlsx')
            with zipfile.ZipFile(download.value.path()) as workbook:
                assert workbook.testzip() is None
                assert 'Khách hàng' in workbook.read('xl/workbook.xml').decode()
            page.locator('#closeMonthlyReport').click()
            page.locator('.overview-data-details summary').click()
            page.locator('#overviewAnalytics').click()
            page.wait_for_selector('.analytics-workspace')
            assert page.locator('#sidebarNav [data-view=overview]').get_attribute('aria-current')=='page'
            assert page.locator('.analytics-heatmap tbody td').count()==168
            assert page.locator('.analytics-advice li').count()<=3
            assert page.locator('.analytics-letter-observations').is_visible()
            stored=next(r for r in page.request.get('http://127.0.0.1:8766/api/records').json() if r['kind']=='sentproposal')
            assert stored['interaction']=='replied' and stored['body']==letter+' Updated wording.'
            page.locator('#analyticsPeriod').select_option('7')
            page.locator('#analyticsBasis').select_option('received')
            page.locator('.analytics-day-details summary').click()
            assert page.locator('.analytics-day-details tbody tr').count()==7
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            page.reload()
            page.wait_for_selector('.overview-workspace')
            page.locator('[data-overview-view=analytics]').click()
            page.wait_for_selector('.analytics-workspace')
            stored=next(r for r in page.request.get('http://127.0.0.1:8766/api/records').json() if r['kind']=='sentproposal')
            assert stored['interaction']=='replied'
            page.locator('[data-overview-view=overview]').click()
            page.locator('#logout').click()
            page.wait_for_selector('#login', state='visible')
            assert not errors, errors
            browser.close()
            print('PASS: compact job list/search/filters/mobile, sent ribbon toggle, persistence and overview sync, readable job details, description save/cancel, mobile detail layout, login/CRM/profile/webhook, node drafting/review, stale-score detection, additional template connections, drag/save/reload, immutable sent archive, contract outcome, reuse won letter, mobile layout, analytics periods/heatmap/observations persistence and logout; external AI mocked')
    finally:
        process.terminate()
        process.wait()
