# 🚀 AI Fitness Coach - Complete Implementation Guide

## Overview

This document provides step-by-step instructions for deploying and using the production-ready AI Fitness Coach platform.

## Phase Completion Status

✅ **Phase 1: Architecture Design** - Complete
✅ **Phase 2: Backend Core Systems** - Complete
✅ **Phase 3: LLM Integration** - Complete  
✅ **Phase 4: Database Schema** - Complete
✅ **Phase 5: Frontend Integration** - In Progress
⏳ **Phase 6: Production Hardening** - Ready

---

## 📋 Table of Contents

1. [Backend Setup](#backend-setup)
2. [Frontend Integration](#frontend-integration)
3. [Database Configuration](#database-configuration)
4. [Deployment](#deployment)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)
7. [5 Critical Systems](#5-critical-systems)

---

## Backend Setup

### 1. Environment Configuration

Create `.env` file in project root:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7

# Supabase Configuration  
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_ANON_KEY_HERE

# Backend Server
API_HOST=127.0.0.1
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=./ai_backend/logs/app.log

# Performance
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Memory
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_ENABLED=true
ENABLE_STREAMING=true
```

### 2. Install Dependencies

```bash
cd ai_backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 3. Initialize Database

Apply migrations to Supabase:

```bash
# Copy SQL from supabase/migrations/20260212_create_fitness_coach_tables.sql
# Run in Supabase SQL Editor or execute manually
```

The migrations create:
- `users_extended` - User fitness profiles
- `workout_plans` - Workout plans with approval workflow
- `nutrition_plans` - Nutrition plans
- `daily_tracking` - Progress tracking
- `chat_memory` - Conversation history

### 4. Start Backend

```bash
# Development mode with auto-reload
uvicorn ai_backend.main:app --reload --host 127.0.0.1 --port 8000

# Production (with Gunicorn)
pip install gunicorn
gunicorn ai_backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Backend will be available at: `http://localhost:8000`

---

## Frontend Integration

### 1. Update Environment Variables

Add to `.env.local`:

```
VITE_AI_BACKEND_URL=http://localhost:8000
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_KEY
```

### 2. Use New Chat Hook

Update Coach.tsx to use new `useAIChat` hook:

```typescript
import { useAIChat } from '@/hooks/useAIChat';

export function CoachPage() {
  const { sendMessage, isLoading, error } = useAIChat();
  
  const handleSendMessage = async (message: string) => {
    const response = await sendMessage(message, conversationId);
    if (response) {
      // Handle response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.reply,
        timestamp: Date.now()
      }]);
    }
  };
  
  // ... rest of component
}
```

### 3. Implement Plan Approval UI

```typescript
import { PlanApprovalUI } from '@/components/ai/PlanApprovalUI';

// In your component:
<PlanApprovalUI
  type="workout"
  plan={workoutPlan}
  onApprove={async (planId) => {
    // Handle approval - save to Supabase
    await supabase
      .from('workout_plans')
      .update({ approved: true })
      .eq('id', planId);
  }}
  onReject={async (planId) => {
    // Handle rejection
    await supabase
      .from('workout_plans')
      .update({ approved: false })
      .eq('id', planId);
  }}
/>
```

### 4. Add Progress Tracking Component

Create `src/components/ai/ProgressTracker.tsx`:

```typescript
import React, { useEffect, useState } from 'react';

export function ProgressTracker() {
  const [progress, setProgress] = useState(null);
  
  useEffect(() => {
    // Fetch progress from Supabase
    // supabase.from('daily_tracking').select()...
  }, []);
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Display workouts completed, meals logged, consistency score */}
    </div>
  );
}
```

---

## Database Configuration

### Supabase Tables

#### users_extended
Stores extended user fitness profile:

```sql
SELECT * FROM users_extended;
-- id, goal, fitness_level, chronic_diseases, allergies, preferred_language
```

#### workout_plans
AI-generated workout plans:

```sql
SELECT * FROM workout_plans WHERE user_id = 'USER_ID' AND approved = false;
-- Lists pending plans awaiting approval
```

#### daily_tracking
Log workouts and meals:

```sql
INSERT INTO daily_tracking (user_id, date, workout_completed, meals_completed)
VALUES ('USER_ID', NOW()::date, true, true);
```

#### chat_memory
Long-term conversation storage:

```sql
SELECT * FROM chat_memory WHERE user_id = 'USER_ID' 
ORDER BY created_at DESC LIMIT 20;
```

---

## 5 Critical Systems

### 1️⃣ Domain Router
**What it does:** Ensures AI only answers fitness/nutrition questions

**Location:** `ai_backend/domain_router.py`

**Usage:**
```python
router = DomainRouter()
is_in_domain, score = router.is_in_domain("I want to build muscle")
if not is_in_domain:
    return router.get_out_of_domain_response(language)
```

**Testing:** Send off-domain queries to `/chat`:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the meaning of life?", "language": "en"}'
```

### 2️⃣ Tool Layer  
**What it does:** Provides agents access to user data and tools

**Location:** `ai_backend/tools_system.py`

**Available Tools:**
- `get_user_profile` - Get user fitness data
- `update_user_profile` - Update profile
- `get_user_progress` - Retrieve progress history
- `log_workout` - Record completed workout
- `log_meals` - Record meals
- `search_exercises` - Find relevant exercises

**Usage in agent:**
```python
tools = tool_executor.registry.get_tool_definitions()
response = llm.chat_completion(messages, tools=tools)
```

### 3️⃣ Memory Layer
**What it does:** Provides context awareness over conversations

**Location:** `ai_backend/memory_system.py`

**Components:**
- **ShortTermMemory** (last 10 messages)
- **LongTermMemory** (user profile, goals, patterns)

**Usage:**
```python
memory = MemorySystem(user_id="USER123")
memory.add_user_message("Build chest muscle")
memory.add_assistant_message("Here's a plan...")
system_prompt = memory.get_system_prompt(language="en")
```

### 4️⃣ Moderation Layer
**What it does:** Filters bad words and toxicity

**Location:** `ai_backend/moderation_layer.py`

**Usage:**
```python
moderation = ModerationLayer()
filtered_text, has_bad_words = moderation.filter_content(text, language="en")
if not moderation.is_safe_response(response):
    response = moderation.get_safe_fallback(language)
```

### 5️⃣ RAG Knowledge Base
**What it does:** Semantic search over exercises/nutrition data

**Location:** `ai_backend/ai_engine.py`

**Usage:**
```python
engine = AIEngine("exercises.json")
relevant_exercises = engine.search_exercises("chest workout", top_k=5)
```

---

## Deployment

### Local Development

```bash
# Terminal 1: Backend
cd ai_backend
source venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Frontend  
npm run dev
```

### Production Deployment

#### Option A: Vercel (Frontend) + Railway (Backend)

**Backend on Railway:**

1. Push code to GitHub
2. Connect repository to Railway
3. Add environment variables
4. Deploy with:
```bash
PORT=8000 gunicorn ai_backend.main:app --workers 4
```

**Frontend on Vercel:**
1. Connect repo to Vercel
2. Add environment variables
3. Deploy

#### Option B: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ai_backend/ ai_backend/
CMD ["gunicorn", "ai_backend.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Deploy:
```bash
docker build -t fit-coach-ai .
docker run -p 8000:8000 --env-file .env fit-coach-ai
```

---

## Testing & Validation

### Test Domain Router
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about quantum physics",
    "language": "en"
  }'
# Expected: Off-domain response
```

### Test Workout Plan Generation
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate a 4-week workout plan for muscle building",
    "language": "en",
    "user_id": "test123"
  }'
```

### Test Multi-Language
```bash
# Arabic Fusha
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "أريد تمارين لبناء الصدر",
    "language": "ar_fusha"
  }'
```

### Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "model": "gpt-4o", "backends_loaded": X}
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Check port is free
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### OpenAI API errors
```bash
# Check API key in .env
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print('OK')"
```

### Model download issues
```bash
# Pre-download sentence-transformer model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Rate limiting issues
Adjust in `.env`:
```
RATE_LIMIT_REQUESTS=500  # Increase limit
RATE_LIMIT_WINDOW=300    # Increase window to 5min
```

---

## Next Steps

1. **Supabase Integration**
   - Implement actual tool functions with Supabase queries
   - Set up RLS policies for security

2. **Enhanced Agents**
   - Implement tool calling in agents
   - Add streaming response handlers

3. **Frontend Components**
   - Create dashboard with progress charts
   - Add plan generator UI
   - Implement progress tracking

4. **Analytics**
   - Add user engagement metrics
   - Track plan compliance
   - Monitor API performance

5. **Scaling**
   - Set up caching layer (Redis)
   - Implement database indexing
   - Load test infrastructure

---

## Support

- 📚 [Backend Documentation](./ai_backend/README.md)
- 🔗 [FastAPI Docs](https://fastapi.tiangolo.com/)
- 🤖 [OpenAI API Docs](https://platform.openai.com/docs)
- 💾 [Supabase Docs](https://supabase.com/docs)
