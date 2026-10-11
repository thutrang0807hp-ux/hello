"""Private local configuration; never sent to the frontend or exported."""
import json
import os
from pathlib import Path

NAMES = ('FREELANCE_AI_AUTO_JOBS', 'FREELANCE_AI_PROVIDER', 'FREELANCE_AI_KEY', 'FREELANCE_AI_MODEL', 'FREELANCE_SLACK_TOKEN', 'FREELANCE_SLACK_CHANNEL', 'FREELANCE_TELEGRAM_TOKEN', 'FREELANCE_TELEGRAM_CHAT_ID', 'FREELANCE_PASSWORD')


def config_path():
    return Path(os.environ.get('FREELANCE_DATA_DIR', Path(__file__).resolve().parent / 'data')) / 'local-config.json'


def load():
    path = config_path()
    if path.exists():
        try:
            values = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(values, dict) or any(not isinstance(value, str) for value in values.values()):
                raise ValueError()
            for name in NAMES:
                if values.get(name) and not os.environ.get(name):
                    os.environ[name] = values[name]
        except (ValueError, OSError):
            raise RuntimeError('Cannot read local settings. Run configure.py again or restore your backup.') from None


def save(values):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump({name: values[name] for name in NAMES if values.get(name)}, stream, ensure_ascii=False, indent=2)
    temporary.replace(path)
    path.chmod(0o600)
