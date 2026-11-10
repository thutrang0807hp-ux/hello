# Build only on Windows x64, with Python 3.12.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
# Dynamic backend imports must be included even though runpy starts the module.
modules = [p.stem for p in root.glob('*.py') if p.stem not in
           {'configure', 'choose_data', 'install_desktop', 'uninstall_desk', 'run'}]
datas = [(str(root / 'public'), 'public')]
binaries = []
hiddenimports = modules
for package in ('webview', 'pystray', 'clr_loader'):
    data, binary, hidden = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += hidden

a = Analysis([str(root / 'frozen_entry.py')], pathex=[str(root)],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[str(root / 'packaging' / 'hooks')])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='FreelanceDesk',
          console=False, icon=str(root / 'public' / 'desktop.ico'))
coll = COLLECT(exe, a.binaries, a.datas, name='FreelanceDesk')
