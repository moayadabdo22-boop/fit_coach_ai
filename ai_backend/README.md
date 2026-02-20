# AI Fitness Coach Backend - Architecture & Setup

## 📊 System Overview

The AI Fitness Coach backend is a production-ready FastAPI service that powers intelligent fitness coaching through:

- **Domain-Restricted AI**: Only answers fitness, training, and nutrition questions
- **Multi-Language Support**: English, Arabic Fusha, and Jordanian Dialect
- **Agent Architecture**: Main coach agent with specialized tools
- **Memory Systems**: Short-term (conversation) and long-term (user context)
- **Content Moderation**: Toxicity filtering and bad words detection
- **RAG Knowledge Base**: Semantic search over exercises and nutrition data
- **Tool Calling**: Integration with user profiles and progress tracking

## 🏗️ Architecture Components

### 1. **Domain Router** (`domain_router.py`)
Semantic classifier that determines if queries are within fitness/nutrition domain.

**Key Features:**
- Semantic similarity checking against fitness topics
- Keyword-based quick filtering for off-domain queries
- Multilingual support (English, Arabic)
- Configurable confidence threshold (default: 0.35)

**Usage:**
```python
router = DomainRouter()
is_in_domain, score = router.is_in_domain("I want to build muscle", language="en")
if not is_in_domain:
    response = router.get_out_of_domain_response(language)
```

### 2. **Memory System** (`memory_system.py`)
Dual-layer memory for context persistence.

**Components:**
- **ShortTermMemory**: Last N messages (default: 10)
- **LongTermMemory**: User profile, preferences, goals, patterns
- **MemorySystem**: Complete memory orchestration

**Features:**
- Automatic message tracking
- Context-aware system prompts
- Profile data integration
- Pattern recognition for behavior tracking

### 3. **Moderation Layer** (`moderation_layer.py`)
Content filtering and safety checks.

**Features:**
- Bad words filtering (English & Arabic)
- Toxicity detection
- Safe fallback responses
- Per-language configurations

**Usage:**
```python
moderation = ModerationLayer()
filtered_text, has_bad_words = moderation.filter_content(text, language="en")
if not moderation.is_safe_response(response):
    response = moderation.get_safe_fallback(language)
```

### 4. **Tool System** (`tools_system.py`)
Tool registry and execution framework.

**Available Tools:**
- `get_user_profile`: Retrieve user fitness profile
- `update_user_profile`: Update user preferences
- `get_user_progress`: Get progress history
- `log_workout`: Log completed workout
- `log_meals`: Log meals
- `search_exercises`: Find relevant exercises

**Tool Definitions:**
```python
registry = ToolRegistry()
tools = registry.get_tool_definitions()  # OpenAI-compatible format
```

### 5. **LLM Client** (`llm_client.py`)
OpenAI API wrapper with streaming support.

**Features:**
- Chat completions (streaming & non-streaming)
- Tool calling support
- Token counting
- Error handling and logging

**Usage:**
```python
llm = LLMClient()
response = llm.chat_completion(messages, temperature=0.7)
for chunk in llm.chat_completion_stream(messages):
    print(chunk, end="", flush=True)
```

### 6. **Coach Agent** (`coach_agent.py`)
Main orchestrator combining all components.

**Workflow:**
1. Domain check
2. Input moderation
3. Memory retrieval
4. RAG context lookup
5. LLM response generation
6. Tool execution (if needed)
7. Output moderation
8. Memory storage

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- Supabase project (optional, for persistence)

### Installation Steps

1. **Create Python environment:**
```bash
cd ai_backend
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Download AI models (first run):**
The sentence-transformers model will auto-download on first use (~400MB).

5. **Start backend:**
```bash
uvicorn ai_backend.main:app --reload --host 127.0.0.1 --port 8000
```

## 📝 API Endpoints

### `POST /chat`
Main chat endpoint for user interactions.

**Request:**
```json
{
  "message": "I want to build chest muscle at home",
  "user_id": "optional-user-id",
  "language": "en",
  "conversation_id": "optional-conv-id",
  "stream": false
}
```

**Response:**
```json
{
  "reply": "Great! Here's how to build chest at home...",
  "conversation_id": "conv-id",
  "language": "en"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "model": "gpt-4o",
  "backends_loaded": 1
}
```

### `GET /conversation/{conversation_id}`
Get conversation history.

**Query Parameters:**
- `user_id` (optional): User identifier

### `POST /conversation/{conversation_id}/clear`
Clear all conversation messages.

## 🔧 Configuration

Key environment variables in `.env`:

```
# LLM
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7

# Supabase
VITE_SUPABASE_URL=https://...
VITE_SUPABASE_ANON_KEY=...

# Server
API_HOST=127.0.0.1
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=./ai_backend/logs/app.log

# Memory
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_ENABLED=true
```

## 📊 Database Schema

**Required Supabase Tables:**

### `users_extended`
Extended user profiles with fitness context.

```sql
- id (UUID, PK) - references auth.users
- goal (TEXT) - muscle_gain, fat_loss, etc.
- fitness_level (TEXT) - beginner, intermediate, advanced
- chronic_diseases (TEXT[])
- allergies (TEXT[])
- preferred_language (TEXT)
- target_calories (INTEGER)
```

### `workout_plans`
User workout plans with approval workflow.

```sql
- id (UUID, PK)
- user_id (UUID, FK)
- plan_json (JSONB) - Full plan details
- start_date (DATE)
- approved (BOOLEAN)
- created_at (TIMESTAMP)
```

### `nutrition_plans`
User nutrition plans.

```sql
- id (UUID, PK)
- user_id (UUID, FK)
- plan_json (JSONB) - Meal details, macros
- daily_calories (INTEGER)
- approved (BOOLEAN)
```

### `daily_tracking`
Daily progress tracking.

```sql
- id (UUID, PK)
- user_id (UUID, FK)
- date (DATE)
- workout_completed (BOOLEAN)
- meals_completed (BOOLEAN)
- workout_notes (TEXT)
- meals_notes (TEXT)
```

### `chat_memory`
Long-term conversation storage.

```sql
- id (UUID, PK)
- user_id (UUID, FK)
- conversation_id (TEXT)
- message_index (INTEGER)
- role (TEXT) - user, assistant
- content (TEXT)
- metadata (JSONB)
```

## 🧠 Key Concepts

### Memory Management
- **Short-term**: Last 10 messages remain in memory
- **Long-term**: User profile, goals, and patterns persist in DB
- **System prompt**: Dynamically includes user context

### Domain Routing
Ensures the AI only answers questions within its expertise:
- ✅ Fitness, training, workouts
- ✅ Nutrition, meal planning, diet
- ✅ Injury prevention, recovery
- ❌ Medicine, politics, personal advice

### Content Moderation
- Filters bad words in user input
- Monitors response safety
- Provides appropriate fallback messages
- Language-aware filtering

### Tool Calling
Agents can invoke tools like:
- Retrieve user profile
- Log completed workouts
- Search exercise database
- Update progress

## 🧪 Testing

### Start development server:
```bash
uvicorn ai_backend.main:app --reload
```

### Test endpoints with cURL:
```bash
# Basic chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to build biceps", "language": "en"}'

# Health check
curl http://localhost:8000/health

# Get history
curl "http://localhost:8000/conversation/default?user_id=user123"
```

### Test with Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Tell me about chest muscles",
        "language": "en",
    }
)
print(response.json())
```

## 📈 Performance Optimization

### RAG Caching
Embeddings are cached after first load (~400MB model).

### Connection Pooling
Reuses agents per user to avoid reinitializing.

### Streaming
Supports token-by-token streaming for real-time UI updates.

### Rate Limiting
Configurable per endpoint (default: 100 req/60s).

## 🔐 Security

- ✅ Input validation (Pydantic)
- ✅ Content filtering
- ✅ SQL injection prevention (Supabase)
- ✅ CORS configuration
- ✅ API key validation
- ⚠️ TODO: Rate limiting per IP
- ⚠️ TODO: Request signing

## 📝 Logging

All events logged to `./ai_backend/logs/app.log`:
- User interactions
- Tool execution
- Errors and exceptions
- System events

**Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🚨 Troubleshooting

### Module import errors
```bash
# Ensure you're in the right directory
cd fit-coach-ai-main
source ai_backend/venv/bin/activate
```

### OpenAI API errors
- Check `OPENAI_API_KEY` is valid
- Verify account has credits
- Check rate limits

### Supabase connection issues
- Verify URL and key in `.env`
- Check Supabase project is active
- Verify RLS policies are correct

### Memory issues
- Reduce `SHORT_TERM_MEMORY_SIZE`
- Enable caching
- Monitor `logs/app.log` for errors

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
