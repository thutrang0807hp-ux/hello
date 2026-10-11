import unittest
from workflow import validate_workspace
from services import ServiceError

class WorkspaceEditingTests(unittest.TestCase):
    def test_empty_workspace_can_be_saved(self):
        value={'version':1,'nodes':[],'edges':[],'scale':1}
        self.assertEqual(validate_workspace(value),value)

    def test_empty_workspace_rejects_dangling_connection(self):
        with self.assertRaises(ServiceError):
            validate_workspace({'version':1,'nodes':[],'edges':[{'from':'a','to':'b'}]})

    def test_editor_zoom_limits_can_be_saved(self):
        for scale in [.25,2]:
            self.assertEqual(validate_workspace({'version':1,'nodes':[],'edges':[],'scale':scale})['scale'],scale)
        for scale in [.24,2.01]:
            with self.assertRaises(ServiceError):
                validate_workspace({'version':1,'nodes':[],'edges':[],'scale':scale})
