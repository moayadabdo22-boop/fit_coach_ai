# 🚀 Quick Reference Guide - AI Fitness Coach

## Start Development

```bash
# Backend
cd ai_backend && source venv/bin/activate && uvicorn main:app --reload

# Frontend (in new terminal)
npm run dev
```

## Core Components

### Backend Structure
```
ai_backend/
├── main.py              # FastAPI app
├── config.py            # Configuration
├── coach_agent.py       # Main agent
├── domain_router.py     # ✅ Domain checking
├── memory_system.py     # ✅ Conversation memory
├── moderation_layer.py  # ✅ Content filtering
├── tools_system.py      # ✅ Tool registry
├── llm_client.py        # OpenAI wrapper
├── ai_engine.py         # RAG/FAISS
├── specialized_agents.py # Workout/Nutrition/Progress agents
├── production_utils.py  # Rate limit, cache, streaming
└── exercises.json       # Exercise database
```

## 5 Critical Systems

### 1. Domain Router
**File:** `domain_router.py`
```python
from domain_router import DomainRouter
router = DomainRouter()
is_in_domain, score = router.is_in_domain("I want to build muscle", language="en")
```

### 2. Tool Layer
**File:** `tools_system.py`
```python
from tools_system import ToolRegistry
registry = ToolRegistry()
tools_list = registry.get_tool_definitions()  # OpenAI format
```

### 3. Memory System
**File:** `memory_system.py`
```python
from memory_system import MemorySystem
memory = MemorySystem(user_id="USER123")
memory.add_user_message("Build chest")
context = memory.get_system_prompt(language="en")
```

### 4. Moderation
**File:** `moderation_layer.py`
```python
from moderation_layer import ModerationLayer
mod = ModerationLayer()
filtered, has_bad = mod.filter_content(text, language="en")
```

### 5. RAG (Exercise Search)
**File:** `ai_engine.py`
```python
from ai_engine import AIEngine
engine = AIEngine("exercises.json")
results = engine.search_exercises("chest workout", top_k=5)
```

## API Endpoints

```bash
# Chat
POST /chat
{
  "message": "Build chest muscle",
  "user_id": "optional",
  "language": "en",  # or "ar_fusha", "ar_jordanian"
  "stream": false
}

# Health
GET /health

# History
GET /conversation/{id}?user_id=user123

# Clear
POST /conversation/{id}/clear
```

## Frontend Integration

### Use Chat Hook
```typescript
import { useAIChat } from '@/hooks/useAIChat';

const { sendMessage, isLoading, error } = useAIChat();

const response = await sendMessage("Build muscle plan");
```

### Display Plan
```typescript
import { PlanApprovalUI } from '@/components/ai/PlanApprovalUI';

<PlanApprovalUI
  type="workout"
  plan={plan}
  onApprove={handleApprove}
  onReject={handleReject}
/>
```

## Database Quick Commands

```sql
-- View user profile
SELECT * FROM users_extended WHERE id = 'USER_ID';

-- Get pending plans
SELECT * FROM workout_plans WHERE user_id = 'USER_ID' AND approved = false;

-- Log workout
INSERT INTO daily_tracking (user_id, date, workout_completed)
VALUES ('USER_ID', NOW()::date, true);

-- Get conversation history
SELECT * FROM chat_memory WHERE user_id = 'USER_ID' ORDER BY created_at DESC LIMIT 20;
```

## Configuration

### .env Variables
```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
VITE_SUPABASE_URL=https://...
VITE_SUPABASE_ANON_KEY=...
API_HOST=127.0.0.1
API_PORT=8000
```

## Common Tasks

### Add New Tool
```python
# In tools_system.py
self.register_tool(
    "my_tool",
    ToolType.PROFILE,
    {
        "description": "What it does",
        "parameters": {
            "properties": {...},
            "required": [...]
        }
    }
)

# In ToolExecutor._handle_tool_name()
async def _my_tool(self, args, user_id):
    # Implementation
    return ToolResult(success=True, ...)
```

### Add New Language
```python
# In domain_router.py
responses = {
    "en": "...",
    "ar_fusha": "...",
    "ar_jordanian": "...",
    "new_lang": "..."  # Add here
}

# In memory_system.py
system_prompts = {
    "en": "...",
    "ar_fusha": "...",
    "new_lang": "..."  # Add here
}
```

### Extend Moderation
```python
# In moderation_layer.py
BAD_WORDS_EN.add("new_word")
BAD_WORDS_AR.add("كلمة")

# Or update patterns
PATTERN_EN = re.compile(r'...', re.IGNORECASE)
```

## Testing

```bash
# Test domain router
curl http://localhost:8000/chat -d '{"message": "politics"}'

# Test fitness query
curl http://localhost:8000/chat -d '{"message": "build muscle"}'

# Test Arabic
curl http://localhost:8000/chat -d '{"message": "أريد تمارين", "language": "ar_fusha"}'

# Test health
curl http://localhost:8000/health
```

## Logging

```python
from utils_logger import log_event, log_error, log_agent_action

# Log events
log_event("CHAT_SUCCESS", user_id, {"language": "en"})

# Log errors
log_error("LLM_ERROR", user_id, exception, {"context": "..."})

# Log agent actions
log_agent_action("CoachAgent", "generate_plan", user_id, {"duration": 28})
```

## Rate Limiting

```python
from production_utils import get_rate_limiter

limiter = get_rate_limiter()
allowed, info = limiter.is_allowed("user123")
if not allowed:
    # Return 429 Too Many Requests
```

## Caching

```python
from production_utils import get_cache_manager

cache = get_cache_manager()
cache.set("key", value)
value = cache.get("key")
cache.clear()
```

## Debugging

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
```

### Check Logs
```bash
tail -f ai_backend/logs/app.log
```

### Test LLM
```python
from llm_client import LLMClient
llm = LLMClient()
response = llm.chat_completion([{"role": "user", "content": "Hi"}])
print(response)
```

### Test Domain Router
```python
from domain_router import DomainRouter
router = DomainRouter()
print(router.is_in_domain("I want to build muscle"))
# Expected: (True, 0.8+)
print(router.is_in_domain("What is the meaning of life"))
# Expected: (False, <0.35)
```

## Deployment Checklist

- [ ] `.env` configured with API keys
- [ ] Database migrations applied
- [ ] Backend tests passing
- [ ] Frontend tests passing
- [ ] Rate limiting configured
- [ ] Logging enabled
- [ ] CORS configured for production domain
- [ ] Monitoring/alerts set up
- [ ] Backups configured
- [ ] SSL certificates configured

## Useful Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Format code
black ai_backend/

# Type checking
mypy ai_backend/

# Run tests
pytest ai_backend/

# Build Docker
docker build -t fit-coach-ai .

# Deploy
git push origin main  # Auto-deploys if CI/CD configured
```

## Resources

- 📖 [Backend README](./ai_backend/README.md)
- 📋 [Implementation Guide](./IMPLEMENTATION_GUIDE.md)
- 📊 [Project Summary](./PROJECT_SUMMARY.md)
- 🔗 [FastAPI Docs](https://fastapi.tiangolo.com)
- 🤖 [OpenAI Docs](https://platform.openai.com/docs)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -i :8000` then kill process |
| OpenAI API error | Check `OPENAI_API_KEY` and account credits |
| Model download fails | Run manually: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` |
| CORS errors | Check `CORS_ORIGINS` in `.env` |
| Rate limit errors | Increase `RATE_LIMIT_REQUESTS` in `.env` |
| Supabase connection fails | Verify URL and key in `.env` |
