# FitCoach AI

Fitness coaching web app with:
- React + Vite frontend
- Python backend (`ai_backend`)
- Optional Supabase Edge function (`supabase/functions/ai-coach`)

## Run frontend

```bash
npm install
npm run dev
```

## Run backend

```bash
cd ai_backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## One-time setup scripts

Windows PowerShell:

```powershell
.\scripts\setup.ps1
```

Mac/Linux:

```bash
bash scripts/setup.sh
```

## Dataset preparation

1. Place raw datasets in `d:\chatbot coach\dataset_` or set `DATASET_ROOT`.
2. Build derived catalogs:
```bash
python scripts/prepare_datasets.py --dataset-root "d:\chatbot coach\dataset_"
```
3. Derived outputs are written to `ai_backend/data/derived/`.

## Free AI alternatives 

You can run the chat with free/local providers:
- Ollama local (recommended free): `http://127.0.0.1:11434`
- Groq free tier API
- Hugging Face Inference API (free tier)

### Example (Ollama)

1. Install Ollama.
2. Pull a model:
```bash
ollama pull llama3.2:3b
```
3. Keep Ollama running, then set backend env:
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

## Environment files

- Frontend: copy `.env.example` to `.env` in the repo root.
- Backend: copy `ai_backend/.env.example` to `ai_backend/.env`.

## Supabase Edge function env (optional)

If using `supabase/functions/ai-coach`, set:
- `AI_GATEWAY_URL` (e.g. `http://127.0.0.1:11434/v1/chat/completions` or other OpenAI-compatible endpoint)
- `AI_MODEL` (e.g. `llama3.1:8b`)
- `AI_API_KEY` (only if your provider requires it)
