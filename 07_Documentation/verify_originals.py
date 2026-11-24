"""Verify that every original file matches the preservation manifest."""
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / '01_Original_Project'
manifest = HERE / 'ORIGINAL_FILE_HASHES.sha256'
expected = dict(line.split('  ', 1)[::-1] for line in manifest.read_text(encoding='utf-8').splitlines())
found = {path.relative_to(BASE).as_posix(): path for path in BASE.rglob('*') if path.is_file()}
bad = sorted(set(expected) ^ set(found))
bad += [name for name in expected.keys() & found.keys()
        if sha256(found[name].read_bytes()).hexdigest() != expected[name]]
if bad:
    sys.exit('FAIL: missing, extra or altered original files\n' + '\n'.join(bad))
print(f'PASS: {len(expected):,} unchanged original files')
