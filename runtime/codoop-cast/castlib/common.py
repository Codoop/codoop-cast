import contextlib
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid


class CastError(Exception):
    def __init__(self, code, message, next_action=None):
        super().__init__(message)
        self.code = code
        self.next_action = next_action


def root_path(explicit=None):
    value = explicit or os.environ.get('CODOOP_CAST_HOME')
    if value:
        return Path(value).expanduser().resolve()
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return base / 'codoop-cast'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def new_id():
    return uuid.uuid4().hex


def item_path(root, kind, ident):
    if not ident or any(c not in '0123456789abcdef' for c in ident) or len(ident) != 32:
        raise CastError('invalid_id', 'Invalid record ID.')
    return root / kind / ident


@contextlib.contextmanager
def lock(root, name):
    directory = root / 'locks'
    directory.mkdir(parents=True, exist_ok=True)
    f = (directory / (name + '.lock')).open('a+b')
    try:
        f.seek(0)
        if os.name == 'nt':
            import msvcrt
            if f.read(1) == b'':
                f.write(b'0')
                f.flush()
            f.seek(0)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise CastError('busy', 'Another process is using this feature. Retry after it finishes.')
        else:
            import fcntl
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise CastError('busy', 'Another process is using this feature.')
        yield
    finally:
        f.close()  # OS releases the lock on close or process death.


def result(status='ready', **kwargs):
    return dict(status=status, **kwargs)
