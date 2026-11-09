"""Genera `data/voice/disclaimer.mp3` (aviso de IA de la voz) con la voz y el modelo de `.env`.

cd backend && uv run python ../scripts/gen_disclaimer.py

Solo hace falta repetirlo si cambia la voz (`ELEVENLABS_VOICE_ID`) o el texto del aviso.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# En Docker el código está en /app (directorio de trabajo); en local, en <repo>/backend.
for candidate in (Path.cwd(), ROOT / "backend"):
    if (candidate / "app" / "__init__.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break


def main() -> None:
    from app.config import Settings
    from app.voice import elevenlabs, service

    settings = Settings(_env_file=ROOT / ".env")
    if not settings.elevenlabs_api_key:
        sys.exit("Falta ELEVENLABS_API_KEY en .env")
    config = elevenlabs.VoiceConfig(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        tts_model=settings.elevenlabs_tts_model,
        stt_model=settings.elevenlabs_stt_model,
    )
    audio = b"".join(elevenlabs.synthesize(service.DISCLAIMER_TEXT, config))
    service.DISCLAIMER_MP3.write_bytes(audio)
    print(f"{service.DISCLAIMER_MP3} ({len(audio)} bytes): {service.DISCLAIMER_TEXT}")


if __name__ == "__main__":
    main()
