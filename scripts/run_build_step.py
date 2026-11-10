"""Retain a short build error in GitHub annotations when logs require sign-in."""
import subprocess
import sys

result = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding='utf-8', errors='replace')
print(result.stdout, flush=True)
if result.returncode:
    for line in result.stdout.splitlines()[-18:]:
        escaped = line.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::error::' + escaped, flush=True)
sys.exit(result.returncode)
