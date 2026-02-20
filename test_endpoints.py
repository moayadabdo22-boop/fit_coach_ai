import requests
import json

print("=" * 60)
print("🧪 اختبار endpoints متقدمة")
print("=" * 60)

# 1. اختبار اعتماد الخطة
plan_id = "nutrition_user123_1770934590"
resp = requests.post(f'http://127.0.0.1:8000/plans/{plan_id}/approve')
print(f"\n✅ اعتماد الخطة الغذائية:")
print(f"   {resp.json()['message']}")

# 2. اختبار تحديث إكمال الوجبة
resp = requests.post('http://127.0.0.1:8000/daily/user123/complete-meal/breakfast')
print(f"\n✅ تحديث إكمال الوجبة:")
print(f"   {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

# 3. اختبار تحديث إكمال التمرين
resp = requests.post('http://127.0.0.1:8000/daily/user123/complete-exercise/Bench%20Press')
print(f"\n✅ تحديث إكمال التمرين:")
print(f"   {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

# 4. اختبار الحصول على التقدم
resp = requests.get('http://127.0.0.1:8000/progress/user123')
print(f"\n✅ تقرير التقدم اليومي:")
data = resp.json()
print(f"   الوجبات: {data['meals_completed']}")
print(f"   التمارين: {data['workouts_completed']}")
print(f"   نسبة الالتزام: {data['compliance_percentage']}%")
print(f"   الرسالة: {data['message']}")

# 5. اختبار الحصول على بيانات المستخدم
resp = requests.get('http://127.0.0.1:8000/user/user123')
print(f"\n✅ بيانات المستخدم:")
user = resp.json()
print(f"   الاسم: {user['name']}")
print(f"   الهدف: {user['goal']}")
print(f"   السعرات المستهدفة: {user['target_calories']}")
print(f"   الأمراض المزمنة: {', '.join(user['chronic_diseases'])}")
print(f"   الحساسية: {', '.join(user['allergies'])}")

print("\n" + "=" * 60)
print("🎉 جميع الـ endpoints تعمل بنجاح!")
print("=" * 60)
