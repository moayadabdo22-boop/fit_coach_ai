# Voice Stack (Fully Local)

This folder provides a local voice-to-voice pipeline:

Audio -> Whisper STT -> Ollama (via backend chat flow) -> Piper/Coqui TTS -> WAV

## Environment Variables

- `WHISPER_MODEL` (default: `openai/whisper-base`)
- `VOICE_TTS_ENGINE` (default: `piper`, options: `piper`, `coqui`)
- `PIPER_BIN` (default: `piper`)
- `PIPER_MODEL_PATH` or per-language:
  - `PIPER_MODEL_PATH_EN`
  - `PIPER_MODEL_PATH_AR`
- `PIPER_CONFIG_PATH` (optional)
- `COQUI_TTS_MODEL` (optional, when `VOICE_TTS_ENGINE=coqui`)

Generated audio files are written to: `ai_backend/static/audio/`
Served by FastAPI under: `/static/audio/<file>.wav`
