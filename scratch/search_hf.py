import urllib.request
import json

queries = ['twitter bot', 'twitter misinformation', 'disinformation', 'election tweets', 'rumour']
found = {}

for q in queries:
    url = f"https://huggingface.co/api/datasets?search={urllib.parse.quote(q)}&limit=15"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data:
                did = item.get('id')
                dl = item.get('downloads', 0)
                if did not in found and dl > 5:
                    found[did] = dl
    except Exception as e:
        print(f"Error on {q}: {e}")

sorted_datasets = sorted(found.items(), key=lambda x: x[1], reverse=True)
print(f"Found {len(sorted_datasets)} candidate datasets:")
for did, dl in sorted_datasets[:25]:
    print(f"{did:50} | downloads: {dl}")
