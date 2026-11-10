import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_download_site', Path(__file__).resolve().parents[1] / 'scripts/prepare_download_site.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DownloadSiteTests(unittest.TestCase):
    def test_missing_or_zip_installer_cannot_create_download_button(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                module.prepare(root / 'missing.exe', root / 'site')
            fake = root / 'source.exe'
            fake.write_bytes(b'PK' + bytes(100))
            with self.assertRaises(ValueError):
                module.prepare(fake, root / 'site')
            self.assertFalse((root / 'site').exists())

    def test_site_contains_exact_input_file_and_checksum(self):
        # Minimal PE header is a generator fixture, not a runnable executable.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = bytearray(80)
            raw[:2] = b'MZ'
            struct.pack_into('<I', raw, 60, 64)
            raw[64:68] = b'PE\0\0'
            installer = root / 'installer.exe'
            installer.write_bytes(raw)
            module.prepare(installer, root / 'site')
            self.assertEqual((root / 'site/FreelanceDesk-Setup.exe').read_bytes(), raw)
            html = (root / 'site/index.html').read_text(encoding='utf-8')
            self.assertIn('href="FreelanceDesk-Setup.exe"', html)
            self.assertNotIn('EXE-Source.zip', html)
            self.assertNotIn('Đang chuẩn bị bản cài EXE', html)
            self.assertIn(module.hashlib.sha256(raw).hexdigest(), (root / 'site/FreelanceDesk-Setup.exe.sha256').read_text())
