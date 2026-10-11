import unittest
from datetime import date
from client_lifecycle import archive_unanswered, record_client_events

class ClientLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client={'clientGroup':'talk','clientStage':'new','clientInquiryDate':'2026-09-27','name':'Lead'}
        self.today=date(2026,10,11)
    def test_exact_fourteen_days(self):
        result=archive_unanswered(self.client,self.today)
        self.assertEqual(result['clientStage'],'closed-no-contract')
        self.assertEqual(result['clientGroup'],'archive')
        self.assertEqual(result['clientLostReason'],'silent')
        self.assertEqual(result['clientArchivedDate'],'2026-10-11')
        self.assertEqual(self.client['clientGroup'],'talk')
    def test_thirteen_days_waits(self):
        self.assertIsNone(archive_unanswered(self.client,date(2026,10,10)))
    def test_reply_on_or_after_inquiry_prevents_archive(self):
        for reply in ['2026-09-27','2026-10-01']:
            self.assertIsNone(archive_unanswered(dict(self.client,lastReplyDate=reply),self.today))
    def test_older_reply_does_not_cancel_new_inquiry(self):
        self.assertIsNotNone(archive_unanswered(dict(self.client,lastReplyDate='2026-09-20'),self.today))
    def test_missing_invalid_or_future_inquiry(self):
        for value in ['',None,'garbage','2026-10-12']:
            self.assertIsNone(archive_unanswered(dict(self.client,clientInquiryDate=value),self.today))
    def test_only_new_leads(self):
        for change in [{'clientStage':'discussing'},{'clientGroup':'active'},{'clientGroup':'archive'}]:
            self.assertIsNone(archive_unanswered(dict(self.client,**change),self.today))
    def test_invalid_reply_does_not_assume_silence(self):
        self.assertIsNone(archive_unanswered(dict(self.client,lastReplyDate='invalid'),self.today))

class ClientEventTests(unittest.TestCase):
    def test_new_lead_does_not_invent_conversation(self):
        c=record_client_events({'clientGroup':'talk','clientStage':'new'},now='2026-10-11T09:00:00+07:00')
        self.assertNotIn('clientTalkAt',c)
    def test_discussion_and_contract_dates_preserved(self):
        c=record_client_events({'clientGroup':'talk','clientStage':'discussing'}, {'clientGroup':'talk','clientStage':'new'},'2026-10-11T09:00:00+07:00')
        c=record_client_events({'clientGroup':'active','clientStage':'working'},c,'2026-10-12T09:00:00+07:00')
        self.assertEqual(c['clientTalkAt'],'2026-10-11T09:00:00+07:00')
        self.assertEqual(c['clientContractAt'],'2026-10-12T09:00:00+07:00')
        closed=record_client_events({'clientGroup':'archive','clientStage':'closed-contract'},c,'2026-10-13T09:00:00+07:00')
        reopened=record_client_events({'clientGroup':'active','clientStage':'working'},closed,'2026-10-14T09:00:00+07:00')
        self.assertEqual(reopened['clientContractAt'],c['clientContractAt'])
    def test_legacy_reopening_does_not_invent_old_dates(self):
        c=record_client_events({'clientGroup':'active'}, {'clientGroup':'archive','clientStage':'closed-contract'},'2026-10-11T09:00:00+07:00')
        self.assertNotIn('clientTalkAt',c)
        self.assertNotIn('clientContractAt',c)
    def test_manual_reply_uses_recorded_day(self):
        c=record_client_events({'lastReplyDate':'2026-10-03'}, {'clientGroup':'talk','clientStage':'new'},'2026-10-11T09:00:00+07:00')
        self.assertEqual(c['clientTalkAt'],'2026-10-03T00:00:00+07:00')
