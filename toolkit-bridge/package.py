"""Package the user's installed Toolkit with an additive, local-only bridge.
Usage: python toolkit-bridge/package.py PATH_TO_EXTRACTED_EXTENSION [OUTPUT_DIR]
The original folder is read only; no cookie or Chrome profile is included.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

HERE = Path(__file__).resolve().parent
APPEND = "\n// Freelance Desk local bridge (added separately from the original bundle).\nimport './desk-bridge-background.js';\n"
SCRIPT = '<script type="module" src="desk-bridge-entry.js"></script>'

def package(original, destination):
    original, destination = Path(original).resolve(), Path(destination).resolve()
    manifest = json.loads((original / 'manifest.json').read_text())
    if manifest.get('version') != '1.6.0' or manifest.get('background') != {'service_worker': 'background.js', 'type': 'module'}:
        raise ValueError('This patch was verified only against the uploaded Toolkit 1.6.0 module build.')
    expected = json.loads((HERE / 'original-hashes.json').read_text())
    for name, digest in expected.items():
        if hashlib.sha256((original / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Original file differs from the inspected build: {name}')
    destination.mkdir(parents=True, exist_ok=True)
    extension = destination / 'toolkit-desk-bridge'
    if extension.exists():
        raise ValueError('Output already exists; choose an empty destination.')
    shutil.copytree(original, extension, ignore=shutil.ignore_patterns('_metadata'))
    manifest.pop('key', None)  # Keep the installed Web Store edition available under its own ID.
    manifest.pop('update_url', None)  # The store must not overwrite this additive patch.
    manifest['name'] = 'Upwork Toolkit · Freelance Desk Bridge'
    manifest['version_name'] = '1.6.0 + Freelance Desk bridge 2'
    manifest['options_ui'] = {'open_in_tab': True, 'page': 'desk-bridge.html'}
    manifest['action']['default_popup'] = 'desk-bridge.html'
    manifest['host_permissions'] += ['http://127.0.0.1/*', 'http://localhost/*']
    (extension / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    # Original JS bundles remain byte-for-byte identical; only an import is appended to the worker.
    with (extension / 'background.js').open('ab') as f:
        f.write(APPEND.encode())
    html = (original / 'options.html').read_text()
    (extension / 'options.html').write_text(html.replace('</body>', SCRIPT + '\n  </body>'), encoding='utf-8')
    for p in HERE.glob('desk-bridge*'):
        shutil.copy2(p, extension / p.name)
    shutil.copy2(HERE / 'LICENSE', extension / 'FREELANCE-DESK-BRIDGE-LICENSE.txt')
    source_note = {
        'base': 'User-supplied Chrome Web Store Toolkit 1.6.0',
        'upstream': 'https://github.com/neeilya/upwork-toolkit',
        'upstreamReleaseId': '4be0325640df585fb9030a5ddffa756ea0effce0',
        'changes': ['Appended bridge import in background.js', 'Added link script in options.html', 'Icon popup and extension options open connection page directly',
                    'Added desk-bridge files', 'Removed Web Store key/update_url; added localhost host permissions and distinct name'],
        'originalSha256': expected,
    }
    (extension / 'BRIDGE-CHANGES.json').write_text(json.dumps(source_note, indent=2), encoding='utf-8')
    archive = destination / 'Toolkit-Installed-Build-Bridge.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in extension.rglob('*'):
            if p.is_file(): z.write(p, 'toolkit-desk-bridge/' + str(p.relative_to(extension)))
        z.write(HERE / 'INSTALL-WINDOWS.txt', 'HUONG-DAN.txt')
    return extension, archive

if __name__ == '__main__':
    extension, archive = package(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '/tmp/toolkit-bridge-package')
    print(extension)
    print(archive)
