import requests
import json

tests = [
    ('مرحبا', 'ar-jd'),
    ('خطة غذائية', 'ar-jd'),
    ('خطة تمارين', 'ar-jd'),
    ('hi', 'en'),
    ('nutrition plan', 'en'),
    ('شو اسمك', 'ar-jd'),
]

print("=" * 60)
print("🧪 اختبار نظام الشات المتقدم")
print("=" * 60)

for msg, lang in tests:
    try:
        resp = requests.post('http://127.0.0.1:8000/chat', 
                           json={'message': msg, 'language': lang, 'user_id': 'user123'})
        data = resp.json()
        print(f"\n✅ '{msg}' ({lang})")
        print(f"💬 {data['reply'][:120]}")
        if data.get('action'): 
            print(f"🎯 Action: {data['action']}")
            if data.get('data'): 
                print(f"📊 Data: {data['data']}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("🎉 جميع الاختبارات انتهت!")
print("=" * 60)
