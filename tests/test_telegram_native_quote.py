import unittest
from html.parser import HTMLParser
from job_notification import render,units


class Parsed(HTMLParser):
    def __init__(self):
        super().__init__();self.all=[];self.quote=[];self.quoted=False;self.tags=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag)
        if tag=='blockquote':
            self.quoted=True
            assert 'expandable' in dict(attrs)
        if tag=='a':self.links.append(dict(attrs)['href'])
    def handle_endtag(self,tag):
        if tag=='blockquote':self.quoted=False
    def handle_data(self,data):
        self.all.append(data)
        if self.quoted:self.quote.append(data)


class NativeQuoteTests(unittest.TestCase):
    def job(self,notes):
        return {'name':'Build dashboard','notes':notes,'url':'https://www.upwork.com/jobs/~fixture','budget':'$500','clientInfo':{'rating':4.8,'country':'US','totalHires':25,'paymentVerified':True}}

    def parse(self,job):
        markup=render(job);p=Parsed();p.feed(markup)
        self.assertLessEqual(units(''.join(p.all)),4096)
        return markup,p

    def test_complete_description_is_inside_same_expandable_message(self):
        notes=('Complete paragraph with all details.\n'*60)
        markup,p=self.parse(self.job(notes))
        self.assertEqual(''.join(p.quote),notes)
        self.assertNotIn('Mô tả vượt giới hạn',markup)
        self.assertNotIn('callback_data',markup)
        self.assertEqual(p.tags.count('blockquote'),1)

    def test_long_description_is_explicitly_marked_and_source_link_preserved(self):
        job=self.job('Long description. '*2000)
        markup,p=self.parse(job)
        self.assertIn('Mô tả vượt giới hạn một tin Telegram',markup)
        self.assertTrue(''.join(p.quote).endswith('…'))
        self.assertEqual(p.links,[job['url']])

    def test_unicode_and_long_metadata_always_fit_visible_telegram_limit(self):
        for length in [1,1000,3000,4000,10000]:
            job=self.job(('😀\n'*length));job['name']='😀'*1000;job['budget']='x'*200;job['clientInfo']['country']='😀'*500
            self.parse(job)

    def test_description_markup_cannot_escape_the_quote(self):
        notes='</blockquote><script>alert(1)</script> & <a href="https://evil.example">fake</a>'
        _,p=self.parse(self.job(notes))
        self.assertEqual(''.join(p.quote),notes)
        self.assertNotIn('script',p.tags)
        self.assertEqual(p.links,['https://www.upwork.com/jobs/~fixture'])

    def test_pending_jobs_with_old_callback_key_still_use_native_quote(self):
        job=self.job('Existing queued description');job['_telegramDetails']='abcdefghijklmnop'
        markup,p=self.parse(job)
        self.assertEqual(''.join(p.quote),job['notes'])
        self.assertIn('Mở job trên Upwork',markup)

    def test_full_source_href_and_missing_description_are_clear(self):
        job=self.job('');job['url']='https://www.upwork.com/jobs/~fixture?query='+'a'*1500+'&x="test"'
        markup,p=self.parse(job)
        self.assertEqual(p.links,[job['url']])
        self.assertIn('Nguồn chưa gửi mô tả',markup)
