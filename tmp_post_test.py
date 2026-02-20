import json
import urllib.request
url='http://127.0.0.1:8000/chat'
data={'message':'recommend me 3 leg exercises'}
req=urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=10) as r:
    print(r.read().decode())
