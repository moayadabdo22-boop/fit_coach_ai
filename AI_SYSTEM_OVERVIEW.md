# AI System Overview (FitCoach)

This document provides a complete, high-level description of the AI system in this project and how user profiles are accessed.

**1) AI Architecture Summary**

The AI in FitCoach is not a single model. It is a layered system built from multiple components that work together:

**2) Multi‑Dataset Training Pipeline**

The backend loads and trains on 50+ datasets located in `ai_backend/datasets`. The pipeline is implemented in:
- `ai_backend/training_pipeline.py`
- `ai_backend/training_engine.py`
- `ai_backend/personalization_engine.py`
- `ai_backend/enhanced_recommendation_engine.py`

The pipeline builds a trained recommendation model that produces personalized workouts and nutrition suggestions based on the user profile (age, weight, goal, experience level, equipment, injuries, allergies).

**3) Dataset‑Based Conversational Responses**

The project includes curated response datasets used for deterministic, fast replies:
- `ai_backend/data/.../conversation_intents.json`
- `ai_backend/data/.../workout_programs.json`
- `ai_backend/data/.../nutrition_programs.json`

These files power short conversational responses and structured plan options.

**4) LLM Chat Layer (Hybrid Mode)**

The LLM layer provides natural, back‑and‑forth conversation. It is managed by:
- `ai_backend/llm_client.py`

Default provider is local **Ollama** (free, offline), but it can be switched to OpenAI by setting `OPENAI_API_KEY` and `LLM_PROVIDER=openai`.

The assistant operates in **Hybrid** mode:
- Dataset responses are prioritized when available.
- If a question needs reasoning or open‑ended dialogue, the LLM handles it.

**5) User Context, Memory, and Progress**

The backend keeps per‑user context and memory (short‑term + long‑term). It also uses progress summaries, plan snapshots, and tracking history to personalize replies.

Core logic is in:
- `ai_backend/main.py`
- `ai_backend/memory_system.py`
- `ai_backend/domain_router.py`

**6) Plan Generation and Approval Flow**

Plan flow is consistent across workout and nutrition:
1. User asks for a plan.
2. System generates several options.
3. User selects an option.
4. User approves it.
5. The approved plan is saved to Supabase and appears in Schedule.

**7) Voice AI**

The project supports speech‑to‑text and text‑to‑speech:
- `ai_backend/voice/stt.py`
- `ai_backend/voice/tts.py`
- `ai_backend/voice/voice_pipeline.py`

Endpoint: `/voice-chat`

**8) Prediction and Analytics Tools**

The backend includes machine‑learning prediction utilities:
- Goal prediction
- Success prediction

These are used when the user explicitly asks for predictions.

**9) How to View User Profiles (Registered Users)**

User profile data is stored in Supabase under `public.profiles`.

**Option A: Supabase Table Editor**
- Open Supabase Dashboard
- Database → Table Editor → `public.profiles`

**Option B: SQL Query (Supabase SQL Editor)**
```sql
select
  p.*,
  u.email
from public.profiles p
join auth.users u on u.id = p.user_id
order by p.created_at desc;
```

**Option C: In‑App**

The current UI shows only the **current user’s** profile, not all users. If you need an admin page to list all users, it must be added.

---

If you want a deeper technical breakdown or diagrams, this document can be extended.

---

## Comprehensive AI Inventory (All AI Components in the Project)

This section lists every AI-related component and what it does.

**1) Multi‑Dataset Training Pipeline**
- **Purpose:** Learns patterns from 50+ datasets to create personalized recommendations.
- **Key files:**
  - `ai_backend/training_pipeline.py`
  - `ai_backend/training_engine.py`
  - `ai_backend/personalization_engine.py`
  - `ai_backend/enhanced_recommendation_engine.py`
- **Outputs:** Personalized workout plans, nutrition plans, food/exercise recommendations.

**2) Recommendation Engines**
- **Base Recommendation Engine:** Standard heuristic recommendations.
- **Enhanced Recommendation Engine:** Uses trained datasets + personalization for higher relevance.
- **Key file:** `ai_backend/enhanced_recommendation_engine.py`

**3) Conversation Intent System (Dataset Responses)**
- **Purpose:** Deterministic responses for common intents (greetings, plan requests, FAQs).
- **Key files:**
  - `ai_backend/data/.../conversation_intents.json`
  - `ai_backend/response_datasets.py`

**4) Plan Generation System**
- **Purpose:** Builds workout and nutrition plans from datasets + user profile.
- **Key files:**
  - `ai_backend/main.py` (plan orchestration)
  - `ai_backend/data/.../workout_programs.json`
  - `ai_backend/data/.../nutrition_programs.json`

**5) LLM Chat Layer**
- **Purpose:** Natural conversation, deeper reasoning, and free‑form coaching.
- **Provider:** Ollama by default (local), OpenAI optional.
- **Key files:**
  - `ai_backend/llm_client.py`
  - `ai_backend/config.py`

**6) Domain Router + Moderation**
- **Purpose:** Ensures the assistant stays in fitness domain and filters unsafe content.
- **Key files:**
  - `ai_backend/domain_router.py`
  - `ai_backend/moderation_layer.py`

**7) Memory & Personal Context**
- **Purpose:** Maintains short‑term and long‑term memory for personalized responses.
- **Key files:**
  - `ai_backend/memory_system.py`
  - `ai_backend/main.py` (memory updates)

**8) Progress & Tracking Analytics**
- **Purpose:** Uses tracking summaries to compute adherence, progress, and performance.
- **Key files:**
  - `ai_backend/main.py` (tracking summary logic)
  - Supabase tables: `workout_completions`, `daily_logs`

**9) Prediction Models**
- **Purpose:** Predict goal suitability and success likelihood.
- **Key files:**
  - `ai_backend/predict.py`
  - `ai_backend/main.py` (prediction endpoints)

**10) Nutrition Knowledge Base**
- **Purpose:** Searches nutrition knowledge text for references and notes.
- **Key file:** `ai_backend/knowledge_engine.py`
- **Data:** `ai_backend/knowledge/dataforproject.txt`

**11) Allergy & Restriction Filters**
- **Purpose:** Filters foods/plans based on allergies, chronic diseases, and preferences.
- **Key files:**
  - `ai_backend/main.py` (restriction building & filtering)
  - `ai_backend/datasets/food_allergy_dataset.csv` (if present)

**12) Voice AI (Speech)**
- **Purpose:** Voice chat support (STT + TTS).
- **Key files:**
  - `ai_backend/voice/stt.py`
  - `ai_backend/voice/tts.py`
  - `ai_backend/voice/voice_pipeline.py`

**13) Hybrid Response Policy**
- **Purpose:** Chooses between dataset replies and LLM replies.
- **Key setting:** `CHAT_RESPONSE_MODE=hybrid`
- **Key file:** `ai_backend/main.py`

---

If you want, I can generate a diagram or a system‑flow chart version of this AI inventory.
