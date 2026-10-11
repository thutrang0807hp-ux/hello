import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import ai_provider
from services import ServiceError

class ModelsTest(unittest.TestCase):
    def test_discovery_pagination_and_save(self):
        replies=[{'models':[{'name':'models/new-flash','displayName':'Flash','supportedGenerationMethods':['generateContent']},{'name':'models/embed','supportedGenerationMethods':['embedContent']}],'nextPageToken':'next token'},{'models':[{'name':'models/new-pro','supportedGenerationMethods':['generateContent']}]}]
        def fetch(req,timeout):
            self.assertNotIn('private-key',req.full_url)
            self.assertEqual(req.get_header('X-goog-api-key'),'private-key')
            return io.BytesIO(json.dumps(replies.pop(0)).encode())
        with patch.dict(os.environ,{'FREELANCE_AI_PROVIDER':'gemini','FREELANCE_AI_KEY':'private-key'}),patch('urllib.request.urlopen',side_effect=fetch):
            models=ai_provider.gemini_models()
        self.assertEqual([m['id'] for m in models],['new-flash','new-pro'])
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'FREELANCE_DATA_DIR':tmp}),patch('ai_provider.gemini_models',return_value=models):
            path=Path(tmp,'local-config.json');path.write_text(json.dumps({'FREELANCE_AI_KEY':'kept','FREELANCE_SLACK_TOKEN':'also-kept'}))
            ai_provider.select_gemini_model('new-flash')
            saved=json.loads(path.read_text());self.assertEqual(saved['FREELANCE_AI_KEY'],'kept');self.assertEqual(saved['FREELANCE_SLACK_TOKEN'],'also-kept');self.assertEqual(os.environ['FREELANCE_AI_MODEL'],'new-flash')
            with self.assertRaises(ServiceError):ai_provider.select_gemini_model('bad-model')
            self.assertEqual(json.loads(path.read_text()),saved)

if __name__=='__main__':unittest.main()
