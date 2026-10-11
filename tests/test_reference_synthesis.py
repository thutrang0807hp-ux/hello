import json
import os
import unittest
from unittest.mock import patch
from reference_synthesis import library_pool, distill
from services import ServiceError, generate_proposal

class ReferenceSynthesisTests(unittest.TestCase):
    def setUp(self):
        self.records=[{'id':i,'kind':'template','name':f'Reference {i}','body':f'Dashboard user flows and scope sample {i}'} for i in range(1,42)]
        self.calls=[]
    def provider(self,url,payload,headers):
        context=json.loads(payload['input']);self.calls.append(context)
        if 'text' in payload:
            items=context.get('references',context.get('group_findings'))
            ids=[i for r in items for i in r.get('sourceIds',[r.get('id')]) if i]
            body=json.dumps({'plan':'Học cách mở đầu, trình bày giải pháp và hỏi phạm vi từ nhiều mẫu.','sourceIds':ids})
        else:body='Hi, let us clarify dashboard scope.'
        return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':body}]}]}
    @patch.dict(os.environ,{'FREELANCE_AI_KEY':'test-key'})
    def test_all_references_are_read_before_reduce(self):
        samples=library_pool(self.records,[{'mode':'auto','excludedIds':['t-1']}])
        with patch('reference_synthesis.post_json',self.provider):result=distill(samples,'Build dashboard',{})
        read=[r['id'] for c in self.calls if 'references' in c for r in c['references']]
        self.assertEqual(len(read),40);self.assertNotIn('t-1',read);self.assertEqual(result['readCount'],40)
        self.assertEqual(len(result['sources']),40);self.assertTrue(any('group_findings' in c for c in self.calls))
    def test_manual_pool_only_contains_selected_records(self):
        result=library_pool(self.records,[{'mode':'manual','selectedIds':['t-2','t-8','t-99']}])
        self.assertEqual({r['id'] for r in result},{'t-2','t-8'})
    @patch.dict(os.environ,{'FREELANCE_AI_KEY':'test-key'})
    def test_synthesis_plan_is_passed_to_drafter(self):
        with patch('reference_synthesis.post_json',self.provider),patch('services.post_json',self.provider):
            result=generate_proposal({'requirements':'Dashboard','_library_samples':library_pool(self.records,[{'mode':'manual','selectedIds':['t-2','t-8']}])},{})
        self.assertEqual(result['referenceSynthesis']['readCount'],2);self.assertIn('reference_synthesis',self.calls[-1]);self.assertEqual(len(result['referenceShortlist']),2)
    @patch.dict(os.environ,{'FREELANCE_AI_KEY':'test-key'})
    def test_invented_reference_id_is_rejected(self):
        def invalid(*args):return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"plan":"Bad","sourceIds":["invented"]}'}]}]}
        with patch('reference_synthesis.post_json',invalid),self.assertRaises(ServiceError):distill(library_pool(self.records,[{'mode':'manual','selectedIds':['t-2']}]),'Dashboard',{})
    def test_empty_pool_needs_no_provider(self):
        with patch('reference_synthesis.post_json') as provider:
            self.assertEqual(distill([],'Dashboard',{})['readCount'],0);provider.assert_not_called()

class ParagraphEditingTests(unittest.TestCase):
    @patch.dict(os.environ,{'FREELANCE_AI_KEY':'test-key'})
    def test_edit_request_has_selection_and_full_context(self):
        with patch('services.post_json',return_value={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Shorter paragraph.'}]}]}) as provider:
            result=generate_proposal({'requirements':'Dashboard','rewriteParagraph':True,'selectedParagraph':'Long paragraph.','existingDraft':'Long paragraph. Rest unchanged.','instructions':'Shorten'},{})
        payload=provider.call_args.args[1]
        self.assertIn('ONLY selected_paragraph',payload['instructions'])
        context=json.loads(payload['input'])
        self.assertEqual(context['selected_paragraph'],'Long paragraph.')
        self.assertEqual(context['existing_draft'],'Long paragraph. Rest unchanged.')
        self.assertEqual(result['body'],'Shorter paragraph.')
