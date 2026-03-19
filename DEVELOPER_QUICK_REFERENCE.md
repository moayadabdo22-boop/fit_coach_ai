# 🚀 Developer Quick Reference Guide
## Enterprise Platform Implementation Cheat Sheet

**Last Updated**: March 19, 2026  
**For**: Developers implementing AI Fitness Coach v2.0  
**Time**: Read in 5 minutes, implement in 1 hour  

---

## 📁 File Structure Created

```
project_root/
├── ENTERPRISE_UPGRADE_COMPLETE.md          ← Overview
├── SYSTEM_ARCHITECTURE_v2.md               ← Full architecture
├── PHASE_1_IMPLEMENTATION_GUIDE.md         ← Deployment guide
├── supabase/migrations/
│   ├── 20260319_core_data_tables.sql       ← Plans, progress, workouts, meals
│   ├── 20260319_favorites_achievements.sql ← Gamification tables
│   └── 20260319_notifications_admin.sql    ← Admin & compliance tables
├── ai_backend/
│   ├── auth/
│   │   └── auth_manager.py                 ← JWT, passwords, sessions
│   ├── requirements.txt                    ← Dependencies
│   └── main.py                             ← FastAPI app (add endpoints)
├── src/
│   ├── lib/
│   │   └── database.types.ts              ← Generated Supabase types
│   ├── hooks/
│   │   └── useHealthHistoryTracking.ts    ← Activity tracking
│   └── pages/
│       ├── Dashboard.tsx                   ← New analytics page
│       ├── Leaderboard.tsx                 ← New gamification page
│       └── AdminPanel.tsx                  ← New admin page
└── tests/
    ├── test_auth.py
    ├── test_database.py
    └── test_api.py
```

---

## ⚡ Quick Start Commands

### 1. Deploy Database (5 minutes)
```bash
# Login to Supabase
supabase login

# Push migrations
supabase db push

# Verify
supabase db status

# Generate types
supabase gen types typescript --project-id fwjamapspffchephqqdr > src/lib/database.types.ts
```

### 2. Install Dependencies (2 minutes)
```bash
# Backend dependencies
cd ai_backend
pip install pyjwt bcrypt redis loguru

# Frontend dependencies (already installed)
cd ../
npm install
```

### 3. Test Auth System (5 minutes)
```bash
# Test JWT token creation
python -c "
from ai_backend.auth.auth_manager import JWTManager
token = JWTManager.create_access_token('user123', 'user')
print(f'✓ Token created: {token[:50]}...')
print(f'✓ Auth system ready')
"
```

---

## 🔑 Core Patterns

### Database Operations (TypeScript)
```typescript
// Query progress logs
const { data: progress, error } = await supabase
  .from('daily_progress')
  .select('*')
  .eq('user_id', userId)
  .gte('log_date', startDate)
  .order('log_date', { ascending: false })

// Insert new plan
const { data: plan, error } = await supabase
  .from('plans_history')
  .insert({
    user_id: userId,
    plan_type: 'workout',
    plan_content: {...},
    start_date: new Date(),
    end_date: addDays(new Date(), 30),
    duration_days: 30
  })

// Update points
const { data, error } = await supabase
  .from('user_points')
  .upsert({
    user_id: userId,
    points_total: currentPoints + 50,
    level: calculateLevel(currentPoints)
  })
```

### Authentication (Python)
```python
from ai_backend.auth.auth_manager import (
    AuthenticationService,
    LoginRequest,
    RegisterRequest,
    UserRole
)

# Initialize
auth = AuthenticationService()

# Register user
register_req = RegisterRequest(
    email="user@example.com",
    password="SecurePass123!",
    name="John Doe"
)
tokens = auth.register(register_req, ip_address="192.168.1.1")

# Login user
login_req = LoginRequest(
    email="user@example.com",
    password="SecurePass123!"
)
tokens = auth.login(login_req, device_id="device123", ip_address="...")

# Verify token
payload = auth.jwt_manager.verify_token(access_token, TokenType.ACCESS)
user_id = payload.sub

# Logout
auth.logout(access_token)
```

### API Endpoint Pattern
```python
from fastapi import APIRouter, Depends, HTTPException
from ai_backend.auth.auth_manager import AuthenticationService

router = APIRouter(prefix="/api/v2", tags=["data"])
auth = AuthenticationService()

@router.post("/plans/generate")
async def create_plan(
    plan_data: dict,
    authorization: str = Header(None)
):
    """Create new workout/nutrition plan"""
    try:
        # Verify token
        token = authorization.replace("Bearer ", "")
        payload = auth.jwt_manager.verify_token(token, TokenType.ACCESS)
        user_id = payload.sub
        
        # Generate plan (call training pipeline)
        plan = await training_pipeline.generate_plan(
            user_id=user_id,
            plan_type=plan_data['plan_type'],
            duration_days=plan_data['duration_days']
        )
        
        # Save to database
        result = await supabase.table('plans_history').insert({
            'user_id': user_id,
            **plan
        }).execute()
        
        return {'success': True, 'plan': result.data[0]}
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

### React Component Pattern
```typescript
import { useUser } from '@/contexts/UserContext'
import { useEffect, useState } from 'react'
import { supabase } from '@/integrations/supabase/client'

export function ProgressDashboard() {
  const { user } = useUser()
  const [progress, setProgress] = useState<DailyProgress[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    if (!user) return
    
    const fetchProgress = async () => {
      const { data } = await supabase
        .from('daily_progress')
        .select('*')
        .eq('user_id', user.id)
        .gte('log_date', lastWeek)
        .order('log_date', { ascending: false })
      
      setProgress(data || [])
      setLoading(false)
    }
    
    fetchProgress()
  }, [user])
  
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Your Progress</h1>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <ProgressChart data={progress} />
      )}
    </div>
  )
}
```

---

## 📊 Database Quick Reference

### Most Common Queries

#### Insert Progress Log
```sql
INSERT INTO daily_progress (user_id, log_date, weight, calories_consumed, mood)
VALUES ($1, CURRENT_DATE, $2, $3, $4)
ON CONFLICT (user_id, log_date) DO UPDATE
SET weight = $2, calories_consumed = $3, mood = $4
```

#### Get User's Plans
```sql
SELECT * FROM plans_history
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 10
```

#### Leaderboard Top 10
```sql
SELECT user_id, points, level, rank()
OVER (ORDER BY points DESC) as position
FROM user_points
ORDER BY points DESC
LIMIT 10
```

#### Award Achievement
```sql
INSERT INTO user_achievements (user_id, achievement_key, points_earned)
VALUES ($1, $2, $3)
ON CONFLICT (user_id, achievement_key) DO NOTHING
```

#### Update Points
```sql
UPDATE user_points
SET points_total = points_total + $1,
    points_month = points_month + $1
WHERE user_id = $2
```

---

## 🔐 Security Checklist

- [ ] JWT secrets in environment variables (not hardcoded)
- [ ] Passwords hashed with bcrypt (12 rounds)
- [ ] All sensitive data encrypted
- [ ] CORS whitelist configured
- [ ] Rate limiting enabled
- [ ] Audit logging for sensitive operations
- [ ] HTTPS enforced in production
- [ ] RLS policies enabled on all tables
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use ORM/Parameterized)

### Essential Environment Variables
```bash
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
REDIS_HOST=localhost
REDIS_PORT=6379
SUPABASE_URL=https://fwjamapspffchephqqdr.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://user:pass@localhost/fitcoach
```

---

## 📈 Performance Tips

### Database
```sql
-- Create indexes for hot queries
CREATE INDEX idx_user_points_level ON user_points(level DESC);
CREATE INDEX idx_daily_progress_user_date ON daily_progress(user_id, log_date DESC);
CREATE INDEX idx_achievements_user ON user_achievements(user_id, unlock_date DESC);

-- Verify indexes are being used
EXPLAIN ANALYZE SELECT * FROM daily_progress WHERE user_id = $1;
```

### Backend (Python)
```python
# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_cached(user_id: str):
    return supabase.table('profiles').select('*').eq('user_id', user_id).execute()

# Use connection pooling
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0)
```

### Frontend (React)
```typescript
// Use React Query for efficient data fetching
import { useQuery } from '@tanstack/react-query'

const { data: progress, isLoading } = useQuery({
  queryKey: ['progress', userId],
  queryFn: () => fetchProgress(userId),
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 30 * 60 * 1000   // 30 minutes
})

// Memoize expensive computations
const scoreCard = useMemo(() => 
  calculateScore(progress), [progress]
)
```

---

## 🧪 Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Test auth system
pytest tests/test_auth.py -v
python -c "from ai_backend.auth.auth_manager import AuthenticationService; print('✓')"

# Test database
pytest tests/test_database.py -v

# Test API endpoints
pytest tests/test_api.py -v

# Check code coverage
pytest tests/ --cov=ai_backend --cov-report=html

# Type checking
mypy ai_backend/

# Lint
pylint ai_backend/
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
```bash
# Run tests
pytest tests/ -v

# Check environment variables
test -z "$JWT_SECRET_KEY" && echo "ERROR: JWT_SECRET_KEY not set"

# Verify migrations
supabase migrations list

# Build frontend
npm run build

# Check bundle size
npm run build -- --analyze
```

### Deployment
```bash
# Database
supabase db push

# Backend
docker build -t fitcoach-api .
docker push fitcoach-api

# Frontend
npm run build
aws s3 sync dist/ s3://fitcoach-app/

# Verify
curl https://api.fitcoach.app/health
curl https://fitcoach.app
```

### Post-Deployment
```bash
# Monitor logs
tail -f logs/api.log
tail -f logs/errors.log

# Check health
curl -H "Authorization: Bearer $TEST_TOKEN" \
  https://api.fitcoach.app/api/v2/health

# Test key endpoints
curl -X POST https://api.fitcoach.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"TestPass123!"}'
```

---

## 🔥 Most Important Files to Review

### 1. SYSTEM_ARCHITECTURE_v2.md
**Why**: Complete picture of what you're building  
**Read**: Chapters 1-3 (Architecture, Database, APIs)  
**Time**: 20 minutes  

### 2. PHASE_1_IMPLEMENTATION_GUIDE.md
**Why**: Step-by-step deployment instructions  
**Read**: All sections  
**Time**: 15 minutes  

### 3. auth_manager.py
**Why**: Security foundation for entire platform  
**Read**: JWTManager, PasswordManager, SessionManager classes  
**Time**: 15 minutes  

### 4. Database Migration Files
**Why**: Understand data structure  
**Read**: Focus on your domain (plans/progress/gamification)  
**Time**: 15 minutes  

---

## ⏱️ Implementation Timeline

| Phase | Task | Time | Dependency |
|-------|------|------|-----------|
| 1 | Database migrations | 30 min | None |
| 2 | Generate TypeScript types | 10 min | Phase 1 |
| 3 | Deploy auth system | 20 min | Phase 1,2 |
| 4 | Create API endpoints | 6 hours | Phase 3 |
| 5 | Build React components | 8 hours | Phase 2,4 |
| 6 | Integration testing | 4 hours | Phase 5 |
| **TOTAL** | | **19 hours** | |

---

## 🆘 Troubleshooting

### Issue: "Table doesn't exist"
```sql
-- Check if table exists
SELECT EXISTS (
  SELECT FROM pg_tables 
  WHERE tablename = 'plans_history'
);

-- If not, re-run migration
```

### Issue: "Token verification failed"
```python
# Check JWT secret is set
import os
assert os.getenv('JWT_SECRET_KEY'), "JWT_SECRET_KEY not set"

# Verify token hasn't been revoked
from auth_manager import JWTManager
payload = JWTManager.verify_token(token, TokenType.ACCESS)
```

### Issue: "TypeScript types out of sync"
```bash
# Regenerate from Supabase schema
supabase gen types typescript > src/lib/database.types.ts

# Update client import
import type { Database } from '@/lib/database.types'
```

### Issue: "RLS policy blocking queries"
```sql
-- Check policies
SELECT * FROM pg_policies WHERE tablename = 'daily_progress';

-- Verify WITH (check_option='LOCAL')
CREATE POLICY "user_read" ON daily_progress
  FOR SELECT USING (auth.uid() = user_id);
```

---

## 📚 Additional Resources

- **FastAPI**: https://docs.fastapi.io/
- **Supabase**: https://supabase.com/docs
- **React Query**: https://tanstack.com/query/latest
- **JWT Best Practices**: https://tools.ietf.org/html/rfc7519
- **HIPAA Security**: https://www.hhs.gov/hipaa/for-professionals/index.html
- **GDPR Compliance**: https://gdpr-info.eu/

---

## ✅ Completion Verification

After implementation, verify:

```bash
# ✓ Database Tables Exist
supabase:> SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema='public';
-- Should show 18+ tables

# ✓ TypeScript Types Generated
test -f src/lib/database.types.ts && echo "✓ Types exist"

# ✓ Auth System Works
python -c "from ai_backend.auth.auth_manager import AuthenticationService; print('✓')"

# ✓ Frontend Builds
npm run build && echo "✓ Build successful"

# ✓ Tests Pass
pytest tests/ -q && echo "✓ All tests passed"
```

---

**Status**: Ready to implement  
**Questions**: Review SYSTEM_ARCHITECTURE_v2.md  
**Support**: Check PHASE_1_IMPLEMENTATION_GUIDE.md troubleshooting section  

✨ **Happy coding! You're building something amazing.** ✨
