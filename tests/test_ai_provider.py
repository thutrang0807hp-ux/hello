import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import ai_provider
import configure
import local_config
import services
import job_radar
from reference_synthesis import distill


def gemini(text, finish='STOP'):
    return {'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': 'private thinking', 'thought': True}, {'text': text}]}}]}


class GeminiProviderTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'FREELANCE_AI_PROVIDER': 'gemini', 'FREELANCE_AI_KEY': 'fake-key-for-tests', 'FREELANCE_AI_MODEL': ''})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_gemini_draft_transport_and_private_credentials(self):
        with patch('services.post_json', return_value=gemini('Hi, I can design the dashboard.')) as send:
            reply = services.generate_proposal({'requirements': 'Design dashboard', 'language': 'English'}, {'experience': 'Verified work'})
        self.assertEqual(reply['model'], 'gemini-2.5-flash')
        self.assertEqual(reply['body'], 'Hi, I can design the dashboard.')
        url, body, headers = send.call_args.args
        self.assertEqual(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent')
        self.assertEqual(headers, {'x-goog-api-key': 'fake-key-for-tests'})
        self.assertNotIn('fake-key-for-tests', url + json.dumps(body))
        self.assertEqual(body['generationConfig']['thinkingConfig']['thinkingBudget'], 0)
        self.assertIn('do not invent', body['systemInstruction']['parts'][0]['text'])
        context = json.loads(body['contents'][0]['parts'][0]['text'])
        self.assertEqual(context['freelancer_profile']['experience'], 'Verified work')

    def test_gemini_paragraph_rewrite_keeps_context_and_selected_text(self):
        with patch('services.post_json', return_value=gemini('Replacement.')) as send:
            result = services.generate_proposal({'requirements': 'Dashboard', 'rewriteParagraph': True, 'existingDraft': 'First. Second.', 'selectedParagraph': 'Second.'}, {})
        payload = send.call_args.args[1]
        context = json.loads(payload['contents'][0]['parts'][0]['text'])
        self.assertEqual(context['selected_paragraph'], 'Second.')
        self.assertEqual(context['existing_draft'], 'First. Second.')
        self.assertIn('Rewrite ONLY', payload['systemInstruction']['parts'][0]['text'])
        self.assertEqual(result['body'], 'Replacement.')

    def test_gemini_review_has_json_schema_and_existing_validation(self):
        review = {'score': 82, 'summary': 'Good', 'strengths': ['Relevant'], 'weaknesses': [], 'suggestions': ['Add scope'],
                  'criteria': [{'name': str(i), 'score': 80, 'reason': 'Relevant'} for i in range(4)]}
        with patch('services.post_json', return_value=gemini(json.dumps(review))) as send:
            result = services.evaluate_proposal({'body': 'Letter', 'requirements': 'Dashboard'}, {})
        generation = send.call_args.args[1]['generationConfig']
        self.assertEqual(generation['responseMimeType'], 'application/json')
        self.assertIn('criteria', generation['responseJsonSchema']['required'])
        self.assertEqual(result['review']['score'], 82)
        with patch('services.post_json', return_value=gemini(json.dumps({**review, 'score': 101}))), self.assertRaises(services.ServiceError):
            services.evaluate_proposal({'body': 'Letter', 'requirements': 'Dashboard'}, {})

    def test_gemini_job_assessment_schema_and_missing_data_caps(self):
        assessment = {'summary': 'Dashboard', 'priceComment': 'Unknown', 'clarityComment': 'Unknown', 'riskComment': 'Unknown',
                      'warnings': [], 'budgetScore': 25, 'clarityScore': 20, 'safetyScore': 15}
        with patch('job_radar.post_json', return_value=gemini(json.dumps(assessment))) as send:
            result = job_radar.evaluate({'name': 'Dashboard'})
        self.assertEqual((result['budgetScore'], result['clarityScore'], result['safetyScore']), (10, 5, 7))
        self.assertIn('budgetScore', send.call_args.args[1]['generationConfig']['responseJsonSchema']['required'])

    def test_gemini_reference_batches_and_reduce_all_samples(self):
        seen = []
        def transport(url, body, headers):
            context = json.loads(body['contents'][0]['parts'][0]['text'])
            items = context.get('references', context.get('group_findings'))
            ids = [ident for item in items for ident in item.get('sourceIds', [item.get('id')])]
            if 'references' in context: seen.extend(ids)
            return gemini(json.dumps({'plan': 'Combine relevant structure', 'sourceIds': ids}))
        samples = [{'id': 't-'+str(i), 'sourceId': i, 'name': 'Example '+str(i), 'body': 'Unique '+str(i)} for i in range(12)]
        with patch('reference_synthesis.post_json', side_effect=transport) as send:
            result = distill(samples, 'Dashboard', {})
        self.assertEqual(len(seen), 12)
        self.assertEqual(len(result['sources']), 12)
        self.assertEqual(result['readCount'], 12)
        self.assertEqual(send.call_count, 3)

    def test_manual_job_scoring_even_with_legacy_automatic_setting(self):
        self.assertFalse(ai_provider.automatic_jobs())
        self.assertEqual(job_radar.present({'name': 'Dashboard'}, None)['state'], 'not_evaluated')
        with patch.dict(os.environ, {'FREELANCE_AI_AUTO_JOBS': '1'}):
            self.assertFalse(ai_provider.automatic_jobs())
        with patch.dict(os.environ, {'FREELANCE_AI_PROVIDER': 'openai', 'FREELANCE_AI_AUTO_JOBS': ''}):
            self.assertFalse(ai_provider.automatic_jobs())

    def test_model_name_encoded_and_optional_models_prefix_removed(self):
        with patch.dict(os.environ, {'FREELANCE_AI_MODEL': 'models/gemini-2.5-flash-lite'}):
            self.assertEqual(ai_provider.model(), 'gemini-2.5-flash-lite')

    def test_openai_billing_error_is_preserved_during_distillation(self):
        error=urllib.error.HTTPError('https://test.invalid',429,'quota',{},io.BytesIO(json.dumps({'error':{'code':'insufficient_quota'}}).encode()))
        with patch.dict(os.environ,{'FREELANCE_AI_PROVIDER':'openai'}),patch('reference_synthesis.post_json',side_effect=error),self.assertRaises(services.ServiceError) as caught:
            distill([{'id':'t-1','sourceId':1,'name':'Example','body':'Sample'}],'Job',{})
        self.assertIn('credit',str(caught.exception))
        self.assertNotIn('fake-key',str(caught.exception))

    def test_google_404_diagnostics_redact_key(self):
        detail={'error':{'message':'Model unavailable for fake-key-for-tests'}}
        error=urllib.error.HTTPError('https://test.invalid',404,'Not found',{},io.BytesIO(json.dumps(detail).encode()))
        with patch('services.post_json',side_effect=error),self.assertRaises(services.ServiceError) as caught:
            services.generate_proposal({'requirements':'Dashboard'}, {})
        self.assertIn('Model unavailable',str(caught.exception))
        self.assertNotIn('fake-key',str(caught.exception))

    def test_errors_do_not_expose_keys_or_fall_back_to_other_provider(self):
        for status, expected in [(429, 'hạn mức'), (403, 'khóa API'), (404, 'proxy'), (500, 'gặp lỗi')]:
            error = urllib.error.HTTPError('https://test.invalid/private', status, 'private key details', {}, io.BytesIO())
            with patch('services.post_json', side_effect=error) as send, self.assertRaises(services.ServiceError) as caught:
                services.generate_proposal({'requirements': 'Dashboard'}, {})
            self.assertIn(expected, str(caught.exception))
            self.assertNotIn('fake-key', str(caught.exception))
            self.assertEqual(send.call_count, 1)

    def test_partial_blocked_empty_and_malformed_outputs_are_rejected(self):
        invalid = [gemini('Partial', 'MAX_TOKENS'), gemini(''), {'promptFeedback': {'blockReason': 'SAFETY'}}, {}, {'candidates': None}]
        for value in invalid:
            with patch('services.post_json', return_value=value), self.assertRaises(services.ServiceError):
                services.generate_proposal({'requirements': 'Dashboard'}, {})

    def test_provider_and_key_validation_before_network(self):
        with patch.dict(os.environ, {'FREELANCE_AI_PROVIDER': 'unknown'}), self.assertRaises(services.ServiceError):
            ai_provider.model()
        with patch.dict(os.environ, {'FREELANCE_AI_KEY': ''}), patch('services.post_json') as send, self.assertRaises(services.ServiceError):
            services.generate_proposal({'requirements': 'Dashboard'}, {})
        send.assert_not_called()


class ProviderConfigurationTests(unittest.TestCase):
    def test_legacy_defaults_to_openai(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ai_provider.provider(), 'openai')
            self.assertEqual(ai_provider.model(), 'gpt-4.1-mini')

    def test_switch_provider_resets_old_key_model_and_keeps_notifications_password(self):
        previous = {'FREELANCE_PASSWORD': 'keep-private', 'FREELANCE_AI_KEY': 'old-private', 'FREELANCE_AI_MODEL': 'gpt-4.1-mini',
                    'FREELANCE_SLACK_TOKEN': 'keep-slack', 'FREELANCE_SLACK_CHANNEL': 'keep-channel'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'local-config.json'; path.write_text(json.dumps(previous))
            with patch('configure.config_path', return_value=path), patch('builtins.input', side_effect=['1', '', '', '']), \
                 patch('configure.getpass.getpass', side_effect=['', 'new-gemini-key', '', '']), patch('configure.save') as save, patch('builtins.print'):
                self.assertTrue(configure.configure())
            saved = save.call_args.args[0]
        self.assertEqual(saved['FREELANCE_AI_PROVIDER'], 'gemini')
        self.assertEqual(saved['FREELANCE_AI_KEY'], 'new-gemini-key')
        self.assertNotIn('FREELANCE_AI_MODEL', saved)
        self.assertEqual(saved['FREELANCE_PASSWORD'], previous['FREELANCE_PASSWORD'])
        self.assertEqual(saved['FREELANCE_SLACK_TOKEN'], previous['FREELANCE_SLACK_TOKEN'])

    def test_local_config_persists_and_loads_gemini(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'FREELANCE_DATA_DIR': directory}, clear=True):
            local_config.save({'FREELANCE_AI_PROVIDER': 'gemini', 'FREELANCE_AI_KEY': 'fake-key'})
            local_config.load()
            self.assertEqual(ai_provider.provider(), 'gemini')
            self.assertEqual(ai_provider.model(), 'gemini-2.5-flash')


if __name__ == '__main__':
    unittest.main()
