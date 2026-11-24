"""Download public NSE bhavcopy archives; preserve response provenance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import requests
import datetime

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'options_raw'
RAW.mkdir(parents=True, exist_ok=True)

def download(item):
    label, url = item
    result = dict(label=label, url=url, retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        response = requests.get(url, timeout=(10, 30), headers={'User-Agent':'Mozilla/5.0'})
        result.update(status=response.status_code, size=len(response.content), content_type=response.headers.get('Content-Type'))
        if response.ok and response.content.startswith(b'PK'):
            path=RAW / (label + '.zip')
            path.write_bytes(response.content)
            result.update(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(response.content).hexdigest())
    except Exception as exc:
        result['error']=str(exc)
    print(json.dumps(result), flush=True)
    (RAW / (label + '_provenance.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    filename='BhavCopy_NSE_FO_0_0_0_20251231_F_0000.csv.zip'
    urls=[(f'fo_20251231_{i}',base+filename) for i,base in enumerate([
        'https://nsearchives.nseindia.com/content/fo/',
        'https://archives.nseindia.com/content/fo/',
        'https://nsearchives.nseindia.com/content/fo/udiff/',
        'https://archives.nseindia.com/content/fo/udiff/',
    ])]
    list(ThreadPoolExecutor(max_workers=4).map(download,urls))
