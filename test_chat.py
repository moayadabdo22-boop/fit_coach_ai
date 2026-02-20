import requests
import json

tests = [
    ('thanks', 'en'),
    ('goodbye', 'en'),
    ('كيفك أنت؟', 'ar'),
    ('شنو أخبارك؟', 'ar'),
    ('leg workout', 'en'),
    ('تمارين الأرجل', 'ar'),
    ('protein calories nutrition', 'en'),
    ('تغذية بروتين وجبات', 'ar'),
    ('what is the capital of france', 'en'),
]

for msg, lang in tests:
    resp = requests.post('http://127.0.0.1:8000/chat', json={'message': msg, 'language': lang})
    data = resp.json()
    print(f'📝 "{msg}" ({lang})')
    print(f'💭 {data["reply"][:80]}...' if len(data['reply']) > 80 else f'💭 {data["reply"]}')
    print()
