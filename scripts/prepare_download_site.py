"""Create a deployable download page only when an actual PE installer exists."""
import argparse
import hashlib
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]


def prepare(installer, output):
    installer, output = Path(installer), Path(output)
    with installer.open('rb') as stream:
        header = stream.read(64)
        if len(header) < 64 or header[:2] != b'MZ':
            raise ValueError('Installer is not a Windows executable')
        stream.seek(struct.unpack_from('<I', header, 60)[0])
        if stream.read(4) != b'PE\0\0':
            raise ValueError('Installer has no valid PE signature')
    raw = installer.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    name = 'FreelanceDesk-Setup.exe'
    template = (ROOT / 'download-site/index.html').read_text(encoding='utf-8')
    start, end = '<!-- DOWNLOAD_START -->', '<!-- DOWNLOAD_END -->'
    before, remainder = template.split(start)
    _, after = remainder.split(end)
    card = (f'<a class="download" href="{name}" download="{name}">↓ Tải xuống cho Windows</a>'
            f'<p class="meta">EXE · {len(raw) / 1024 / 1024:.1f} MB · Windows x64</p>'
            '<p class="meta"><a href="FreelanceDesk-Setup.exe.sha256">Mã kiểm tra SHA-256</a></p>')
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(installer, output / name)
    (output / 'index.html').write_text(before + card + after, encoding='utf-8')
    (output / (name + '.sha256')).write_text(f'{digest}  {name}\n', encoding='ascii')
    print(f'Prepared download page with installer ({len(raw)} bytes) and SHA-256.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('installer', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.installer, args.output)
