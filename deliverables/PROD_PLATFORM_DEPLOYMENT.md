**Deployment Instructions**

Local Development
1. Frontend
  - `npm install`
  - `npm run dev`
2. Backend
  - `cd ai_backend`
  - `python -m venv venv`
  - `venv\\Scripts\\activate`
  - `pip install -r requirements.txt`
  - `uvicorn main:app --host 127.0.0.1 --port 8002 --reload`

Environment
- Frontend: `.env`
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_AI_BACKEND_URL`
- Backend: `ai_backend/.env`
  - `OPENAI_API_KEY`
  - `API_HOST`, `API_PORT`

Docker (template)
1. Build
  - `docker build -t fit-coach-backend -f ai_backend/Dockerfile .`
2. Run
  - `docker run -p 8002:8002 --env-file ai_backend/.env fit-coach-backend`

CI/CD (high-level)
- Run lint + unit tests
- Build Docker image
- Deploy to cloud (Render, Fly.io, AWS, GCP)

Database
- Apply schema from `deliverables/PROD_PLATFORM_SCHEMA.sql`
- Configure RLS policies in Supabase

