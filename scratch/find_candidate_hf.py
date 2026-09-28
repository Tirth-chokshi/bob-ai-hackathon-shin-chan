import urllib.request
import json
import pandas as pd
import io

url = 'https://huggingface.co/api/datasets?search=twitter&limit=80&full=true'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))

print(f"Retrieved {len(data)} datasets")
for d in data:
    did = d['id']
    siblings = [s['rfilename'] for s in d.get('siblings', []) if s['rfilename'].endswith(('.csv', '.parquet', '.json'))]
    if siblings:
        print(f"Dataset: {did} | Files: {siblings[:2]}")
