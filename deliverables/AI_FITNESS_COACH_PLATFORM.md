**Overview**
This deliverable documents the full intelligent fitness coach platform design and the concrete implementation added in this repo. The system uses real datasets, deterministic engines, and ML models, with an LLM layer augmented by retrieval from internal catalogs.

**Architecture**
1. Frontend (React / Mobile App)
2. Backend (FastAPI)
3. Datastores
4. ML engines
5. RAG layer
6. Response API

**Datastores**
1. User profile table (`public.users_extended`) extended with full fitness attributes
2. Workout plans (`public.workout_plans`)
3. Nutrition plans (`public.nutrition_plans`)
4. Tracking data (`public.daily_tracking`)
5. Exercise catalog (`public.exercise_catalog`)
6. Nutrition catalog (`public.nutrition_catalog`)
7. Performance reports (`public.performance_reports`)

**Database Schema**
1. Migration file: `supabase/migrations/20260316_add_intelligent_fitness_schema.sql`
2. Added fields: age, gender, height_cm, weight_kg, bmi, workout_preference, equipment, training_days_per_week, session_duration_minutes, injuries, dietary_preferences
3. New tables: exercise_catalog, nutrition_catalog, performance_reports

**Data Pipeline**
1. Raw datasets live in `d:/chatbot coach/dataset_`
2. Prepare derived catalogs using `scripts/prepare_datasets.py`
3. Outputs go to `ai_backend/data/derived/`
4. The backend reads derived catalogs via `ai_backend/data_catalog.py`

**ML Models**
1. Goal prediction model: `ai_backend/train_goal_model.py`
2. Plan intent model: `ai_backend/train_plan_intent_model.py`
3. Success prediction model: `ai_backend/train_success_model.py`
4. Models use scikit-learn pipelines and real datasets

**Recommendation Engines**
1. Workout plan generator: `ai_backend/recommendation_engine.py`
2. Nutrition plan generator: `ai_backend/recommendation_engine.py`
3. Recovery optimizer: `ai_backend/recommendation_engine.py`
4. Progress analytics: `ai_backend/progress_engine.py`

**RAG Layer**
1. Exercise and food retrieval from catalogs: `ai_backend/rag_context.py`
2. Context injected into LLM system prompt in `ai_backend/main.py`

**API Structure**
1. `POST /chat` conversational endpoint
2. `GET /health` health check
3. `GET /v1/profile/{user_id}` get profile
4. `PUT /v1/profile/{user_id}` update profile
5. `POST /v1/plans/workout` generate workout plan options
6. `POST /v1/plans/nutrition` generate nutrition plan options
7. `POST /v1/constraints/summary` health constraints summary
8. `POST /v1/constraints/filter-foods` filter foods by constraints
9. `POST /v1/progress/analyze` progress analytics
10. `POST /v1/recovery/recommendation` recovery optimization
11. `GET /v1/catalog/summary` catalog status

**Training Pipelines**
1. Train goal model: `python ai_backend/train_goal_model.py --dataset d:/chatbot coach/dataset_`
2. Train success model: `python ai_backend/train_success_model.py --dataset d:/chatbot coach/dataset_`
3. Train plan intent model: `python ai_backend/train_plan_intent_model.py --dataset-root d:/chatbot coach/dataset_`

**Deployment**
1. Backend: FastAPI with Uvicorn or Gunicorn
2. Frontend: Vite build and deploy to Vercel, Netlify, or static host
3. Optional Supabase for production persistence
4. Offline mode supported with `ai_backend/data/local_store.json`

**Code Templates**
1. Dataset preparation: `scripts/prepare_datasets.py`
2. Catalog loading: `ai_backend/data_catalog.py`
3. Recommendation engine: `ai_backend/recommendation_engine.py`
4. Health rules: `ai_backend/health_rules.py`
5. Progress analytics: `ai_backend/progress_engine.py`
6. API routes: `ai_backend/api_routes.py`
