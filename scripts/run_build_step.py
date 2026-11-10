"""Retain a short build error in GitHub annotations when logs require sign-in."""
import subprocess
import sys

result = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding='utf-8', errors='replace')
print(result.stdout, flush=True)
if result.returncode:
    lines = result.stdout.splitlines()
    # One annotation preserves the final exception even when GitHub truncates the list.
    detail = '\n'.join(lines[-24:])
    escaped = detail.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print('::error::' + escaped, flush=True)
sys.exit(result.returncode)
