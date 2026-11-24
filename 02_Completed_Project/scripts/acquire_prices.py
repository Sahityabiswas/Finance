"""Download auditable public equity history; raw responses are never overwritten silently."""
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.parse, json, hashlib, concurrent.futures, time

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data'/'raw'
RAW.mkdir(parents=True, exist_ok=True)
SYMBOLS = ['HDFCBANK.NS','ICICIBANK.NS','SBIN.NS','BAJFINANCE.NS','SHRIRAMFIN.NS','MUTHOOTFIN.NS','^NSEI']
START = int(datetime(2020,12,28,tzinfo=timezone.utc).timestamp())
END = int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())

def fetch(symbol):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol)+'?'+urllib.parse.urlencode({'period1':START,'period2':END,'interval':'1d','events':'div,splits'})
    filename=symbol.replace('^','')+'.json'
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=45) as r:
                body=r.read()
                headers=dict(r.headers)
            payload=json.loads(body)
            assert payload['chart']['error'] is None
            result=payload['chart']['result'][0]
            assert len(result['timestamp'])>1200
            (RAW/filename).write_bytes(body)
            return {'symbol':symbol,'url':url,'raw_file':'data/raw/'+filename,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'observations':len(result['timestamp']),'http_headers':headers,'events':result.get('events',{})}
        except Exception:
            if attempt==2: raise
            time.sleep(2)

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        sources=list(pool.map(fetch,SYMBOLS))
    manifest={'provider':'Yahoo Finance chart API (secondary vendor; NSE-listed securities)','request_start':'2020-12-28','request_end_exclusive':'2026-01-01','analysis_period':['2021-01-01','2025-12-31'],'sources':sources,'adjustment_policy':'Use provider adjusted close for equity returns; provider OHLC is split-adjusted. Adj close additionally reflects dividend adjustments. Never apply split factors again. NIFTY 50 is a price index, not a total-return index.'}
    (ROOT/'data'/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for s in sources:
        print(s['symbol'],s['observations'],s['bytes'],list(s['events']))
