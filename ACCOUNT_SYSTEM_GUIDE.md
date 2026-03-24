# ✅ نظام إدارة الحسابات والبيانات | Account & Data Management System

## 📋 سير العملية الكاملة

### 1️⃣ **التسجيل والدخول (Auth)**
```
الصفحة: localhost:8080/auth

• اختر: "Sign In" أو "Sign Up"
• أدخل: البريد الإلكتروني + كلمة المرور
• Sign Up: أضف الاسم أيضاً
• اضغط الزر → محفوظ في localStorage
```

**النتيجة**: 
- ✅ حساب جديد بـ User ID فريد
- ✅ بيانات محفوظة في `fitcoach_mock_user`

---

### 2️⃣ **الإعدادات الأولية (Onboarding)**
```
الصفحة: localhost:8080/onboarding

• الخطوة 1: الاسم + الاسم المستخدم
• الخطوة 2: الطول والوزن
• الخطوة 3: الأمراض المزمنة + الحساسيات ✨
• الخطوة 4: الأهداف
• الخطوة 5: الموقع
• اضغط "Start Training"
```

**البيانات الخاصة**:
```javascript
كل مستخدم له بيانات منفصلة:
{
  user_id: "user_test@example_1234567890",
  name: "محمد",
  age: 25,
  gender: "male",
  weight: 75,
  height: 180,
  goal: "bulking",
  location: "gym",
  chronicConditions: "سكري",        // ✨ جديد
  allergies: "فول سوداني",           // ✨ جديد
  onboarding_completed: true
}
```

تُحفظ في: `localStorage['fitcoach_profile_user_test@example_1234567890']`

---

### 3️⃣ **الملف الشخصي والتعديل (Profile)**
```
الصفحة: localhost:8080/profile

• عرض البيانات الكاملة
• اضغط "Edit Data" → فورم تعديل
• عدّل "الأمراض" و "الحساسيات"
• اضغط "Save Changes"
```

**التحديثات**:
- ✅ تُحدث في React Context مباشرة
- ✅ تُحفظ في localStorage فوراً
- ✅ تُرسل للـ Chatbot في الرسالة التالية

---

### 4️⃣ **الدردشة مع الـ AI (Coach)**
```
الصفحة: localhost:8080/coach

عند إرسال رسالة، يُرسل:
{
  message: "رسالتي",
  user_profile: {
    name: "محمد",
    age: 25,
    chronicConditions: "سكري",       // ✨ تُرسل تلقائياً
    allergies: "فول سوداني",          // ✨ تُرسل تلقائياً
    // +باقي البيانات
  }
}
```

**الـ AI يفهم**:
- ✅ الأمراض المزمنة للمستخدم
- ✅ الحساسيات والمنع الغذائي
- ✅ يعطي نصائح مخصصة

---

## 🔐 كيفية حفظ البيانات منفصلة لكل مستخدم

### في localStorage:
```javascript
// مفتاح المستخدم (فريد):
'fitcoach_mock_user': {
  id: "user_test@example_1234567890",
  email: "test@example.com",
  user_metadata: { name: "محمد" }
}

// بيانات الملف الشخصي (منفصلة لكل مستخدم):
'fitcoach_profile_user_test@example_1234567890': {
  user_id: "user_test@example_1234567890",
  name: "محمد",
  chronicConditions: "سكري",
  allergies: "فول سوداني",
  onboardingCompleted: true,
  // +باقي البيانات
}
```

### في React Context:
```typescript
// UserContext يحتفظ بـ user.id → يحدد مفتاح التخزين
const getProfileStorageKey = (userId: string) => 
  `fitcoach_profile_${userId}`;

// عند تغيير الملف الشخصي:
useEffect(() => {
  if (user) {
    localStorage.setItem(
      getProfileStorageKey(user.id), 
      JSON.stringify(profile)
    );
  }
}, [profile, user?.id]);
```

---

## 📊 مثال عملي كامل

### **المستخدم 1: أحمد**
```
1. تسجيل: Email: ahmed@example.com → ID: user_ahmed@example_1
2. Onboarding:
   - الاسم: أحمد
   - المرض: ضغط الدم العالي
   - الحساسية: الحليب
3. يحفظ في:
   - fitcoach_mock_user
   - fitcoach_profile_user_ahmed@example_1
4. Chat يستقبل: "أحمد عنده ضغط دم عالي وحساسية من الحليب"
```

### **المستخدم 2: فاطمة**
```
1. تسجيل: Email: fatima@example.com → ID: user_fatima@example_2
2. Onboarding:
   - الاسم: فاطمة
   - المرض: سكري
   - الحساسية: الفول السوداني
3. يحفظ في:
   - fitcoach_mock_user
   - fitcoach_profile_user_fatima@example_2
4. Chat يستقبل: "فاطمة عندها سكري وحساسية من الفول"
```

**كل شخص بـ localStorage ومعلومات منفصلة تماماً** ✅

---

## 🔄 سير البيانات عند التعديل

```
User edits allergies in Profile
        ↓
updateProfile() في Context
        ↓
localStorage يتحدث فوراً
        ↓
useEffect يحفظـها
        ↓
User يذهب إلى Chat
        ↓
buildCombinedUserProfile() يقرأ من Context
        ↓
البيانات الجديدة تُرسل مع الرسالة
        ↓
Chatbot يرد بناءً على البيانات الجديدة ✅
```

---

## ✨ الميزات الجديدة

### ✅ تم تطبيقه:
1. **Tabs واضحة**: Sign In vs Sign Up
2. **Routing صحيح**: 
   - Sign Up → Onboarding → Profile
   - Sign In → Profile/Workouts
3. **بيانات منفصلة**: كل user له localStorage خاص
4. **تعديل مباشر**: Profile page فيها form تعديل
5. **تحديث فوري**: البيانات تتحدث في Chat مباشرة

---

## 🧪 للاختبار

### اختبر 1: حسابين منفصلين
```
1. فتح incognito tab
2. User 1: test1@test.com → Sign Up → Allergies: "Peanuts"
3. User 2: test2@test.com → Sign Up → Allergies: "Milk"
4. عودة إلى User 1 → Profile → Allergies = "Peanuts" ✅
5. عودة إلى User 2 → Profile → Allergies = "Milk" ✅
```

### اختبر 2: التعديل والـ Chat
```
1. Sign Up: ahmad@test.com
2. Allergies: "None"
3. عدّل في Profile: "Peanuts"
4. اذهب إلى Chat
5. أرسل رسالة
6. يجب يقول الـ Chat انو عندك حساسية من الفول ✅
```

---

## 📱 الصفحات المهمة

| الصفحة | الرابط | الوظيفة |
|--------|--------|--------|
| Auth | /auth | دخول/تسجيل جديد |
| Onboarding | /onboarding | إعدادات أولية |
| Profile | /profile | عرض وتعديل البيانات |
| Coach | /coach | الدردشة مع الـ AI |
| Workouts | /workouts | التمارين |

---

## 🎯 الحالة النهائية

🟢 **جاهز للاستخدام الكامل**

- ✅ حسابات منفصلة
- ✅ بيانات آمنة ومحفوظة
- ✅ تعديل سهل
- ✅ Chatbot يفهم الأمراض والحساسيات
- ✅ All working locally without Supabase ✨

