"""Export tracked source, docs/tests and required Toolkit artifacts; never runtime data."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INCLUDED_DOWNLOADS = {'downloads/Toolkit-Installed-Build-Bridge.zip', 'downloads/Toolkit-Installed-Build-Source.zip'}
SECRET = re.compile(rb'(?:AIza[0-9A-Za-z_-]{30,}|sk-(?:proj-)?[0-9A-Za-z_-]{32,}|xox[baprs]-[0-9A-Za-z-]{16,}|[0-9]{8,12}:[0-9A-Za-z_-]{30,})')
PRIVATE_NAMES = {'.git', 'data', '__pycache__', 'node_modules', '.env', '.env.local', 'gmail-private.json', 'local-config.json', 'workspace.sqlite3', 'webhook-token', '.storage-location.json', 'storage-location.json', 'desktop-server.json', 'background-server.log', 'desktop-diagnostic.txt', '.desktop-venv', '.desktop-installed-files.json'}


def inspect(name, raw):
    parts=PurePosixPath(name).parts
    if any(p in PRIVATE_NAMES or (p.startswith('.env.') and p!='.env.example') for p in parts) or '..' in parts or name.startswith('/'):
        raise RuntimeError('Private/unsafe path: '+name)
    if SECRET.search(raw):
        # Report path only; never print the matched value.
        raise RuntimeError('Potential credential pattern; review before exporting: '+name)
    if name.endswith('.zip'):
        with zipfile.ZipFile(BytesIO(raw)) as nested:
            if nested.testzip() is not None:raise RuntimeError('Corrupt nested ZIP: '+name)
            for child in nested.namelist():
                if not child.endswith('/'):inspect(name+'!/'+child,nested.read(child))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files={}
    for name in filter(None,tracked):
        if name.startswith('downloads/') and name not in INCLUDED_DOWNLOADS:continue
        raw=(ROOT/name).read_bytes();inspect(name,raw);files[name]=raw
    files['downloads/README.md']=('Hai gói Toolkit đi kèm:\n'
        '- Toolkit-Installed-Build-Bridge.zip: bản extension cầu nối để cài trên Chrome.\n'
        '- Toolkit-Installed-Build-Source.zip: mã nguồn tương ứng và giấy phép.\n'
        'Mã ứng dụng Freelance Desk nằm tại thư mục cha, không cần chép ZIP app cũ.\n').encode()
    required=['DOC-TRUOC-KHI-SUA.md','AGENTS.md','HANDOFF-VALIDATION.txt','PROMPT-CHO-CODEX-MOI.txt','server.py','upwork_mail.py','public/index.html','public/upwork-mail.js','tests/test_upwork_mail.py']
    for name in required:
        if name not in files:raise RuntimeError('Missing tracked handoff file: '+name)
    manifest={'project':'Freelance Desk','created_at':datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
        'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        'note':'Tracked working-tree files; manifest hashes identify exact exported content. Runtime data and private configuration excluded.',
        'sha256':{name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
    files['HANDOFF-MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):z.writestr('FreelanceDesk-Handoff/'+name,raw)
    with zipfile.ZipFile(args.output) as z:
        if z.testzip() is not None:raise RuntimeError('ZIP integrity failed')
        for name,digest in manifest['sha256'].items():
            if hashlib.sha256(z.read('FreelanceDesk-Handoff/'+name)).hexdigest()!=digest:raise RuntimeError('Hash mismatch: '+name)
    print(f'PASS handoff ZIP: {len(files)} files, {args.output.stat().st_size} bytes; private paths/token patterns excluded, nested archives and hashes verified.')


if __name__=='__main__':main()
