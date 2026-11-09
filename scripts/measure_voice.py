"""Mide la latencia de la voz de punta a punta (T2-16, RF-14): «primera palabra < 2 s».

Reloj desde que se suelta el botón (diseño del MVP §2): `stop` en `WS /voice/stt` → `final`
→ `POST /portfolios/{id}/ask` hasta la primera `sentence` → `POST /voice/tts` hasta el primer
byte de audio. Es lo que hace el frontend (T2-14), contra un backend que ya está corriendo y
con ElevenLabs y Claude reales. No cuenta el aviso de IA (que suena antes y lo tapa): mide la
primera palabra de la respuesta, el caso peor.

El audio de las preguntas se genera una vez con la voz de `.env` (PCM 16 kHz) y se manda a
ritmo real, en trozos de 100 ms, como lo haría el micrófono.

    make up   # o el backend en local con la clave de ElevenLabs en el entorno
    cd backend && uv run python ../scripts/measure_voice.py [--runs 10] [--base http://localhost:8000]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from websockets.asyncio.client import connect

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    ("laura", "¿Por qué ha bajado mi cartera?"),
    ("laura", "¿Me afecta lo del BCE?"),
    ("javier", "¿Voy bien con mi plan?"),
]
TARGET_MS = 2000
REQUIRED_OK = 8  # de 10
CHUNK = 3200  # 100 ms de PCM 16 kHz mono 16 bits
SILENCE = b"\x00\x00" * 4800  # 300 ms antes y después, como al pulsar y soltar


@dataclass
class Run:
    question: str
    stt_ms: float
    first_sentence_ms: float
    tts_first_byte_ms: float
    transcript: str

    @property
    def total_ms(self) -> float:
        return self.stt_ms + self.first_sentence_ms + self.tts_first_byte_ms


def _env() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.is_file():
        sys.exit("Falta .env en la raíz del repo (ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID…)")
    pairs = (line.split("=", 1) for line in path.read_text("utf-8").splitlines() if "=" in line)
    return {k.strip(): v.strip() for k, v in pairs if not k.lstrip().startswith("#")}


def _question_audio(text: str, env: dict[str, str]) -> bytes:
    """PCM 16 kHz de la pregunta, con la voz y el modelo de `.env` (ElevenLabs)."""
    response = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{env['ELEVENLABS_VOICE_ID']}",
        params={"output_format": "pcm_16000"},
        headers={"xi-api-key": env["ELEVENLABS_API_KEY"]},
        json={"text": text, "model_id": env.get("ELEVENLABS_TTS_MODEL") or "eleven_flash_v2_5"},
        timeout=30,
    )
    response.raise_for_status()
    return SILENCE + response.content + SILENCE


async def _transcribe(ws_url: str, pcm: bytes) -> tuple[str, float]:
    async with connect(ws_url) as ws:
        await ws.send(
            json.dumps(
                {"type": "start", "sample_rate": 16000, "encoding": "pcm_s16le", "language": "es"}
            )
        )
        for i in range(0, len(pcm), CHUNK):
            await ws.send(pcm[i : i + CHUNK])
            await asyncio.sleep(0.1)  # ritmo real
        released = time.perf_counter()
        await ws.send(json.dumps({"type": "stop"}))
        while True:
            message = json.loads(await ws.recv())
            if message["type"] == "final":
                return message["text"], (time.perf_counter() - released) * 1000
            if message["type"] == "error":
                raise RuntimeError(f"STT: {message}")


def _first_sentence(
    client: httpx.Client, portfolio: str, question: str, session: str
) -> tuple[dict[str, object], float]:
    start = time.perf_counter()
    body = {"question": question, "channel": "voice", "session_id": session}
    with client.stream("POST", f"/portfolios/{portfolio}/ask", json=body, timeout=60) as response:
        response.raise_for_status()
        lines = response.iter_lines()
        for line in lines:
            if not line.startswith("data:"):
                continue
            event = json.loads(line[5:])
            if event["type"] == "sentence":
                elapsed = (time.perf_counter() - start) * 1000
                for _ in lines:  # deja terminar el turno (registra el resto de frases)
                    pass
                return event, elapsed
            if event["type"] == "error":
                raise RuntimeError(f"/ask: {event}")
    raise RuntimeError("/ask terminó sin frases")


def _tts_first_byte(client: httpx.Client, turn_id: str, index: int) -> float:
    start = time.perf_counter()
    with client.stream(
        "POST", "/voice/tts", json={"turn_id": turn_id, "index": index}, timeout=30
    ) as response:
        response.raise_for_status()
        chunks = response.iter_bytes()
        next(chunks)
        elapsed = (time.perf_counter() - start) * 1000
        for _ in chunks:
            pass
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="deja el backend como en el guion: /demo/reset con preload (BCE y petróleo) y "
        "replay de los resultados de NVIDIA (paso 3)",
    )
    args = parser.parse_args()

    env = _env()
    api = f"{args.base.rstrip('/')}/api/v1"
    ws_url = api.replace("http", "ws", 1) + "/voice/stt"
    print("Generando el audio de las preguntas…")
    audio = {q: _question_audio(q, env) for _, q in QUESTIONS}
    session = f"ses_measure{int(time.time())}"

    runs: list[Run] = []
    with httpx.Client(base_url=api) as client:
        if args.prepare:
            print("Preparando el estado del guion (reset + preload + replay NVIDIA)…")
            client.post("/demo/reset", json={"preload": True}, timeout=120).raise_for_status()
            client.post("/demo/replay/nvda-2025-02", json={}, timeout=120).raise_for_status()
        # Calentamiento (no cuenta): primera llamada de la sesión (aviso de IA) y caché del
        # prompt de cada cartera, como se hace antes de la demo.
        for portfolio in sorted({p for p, _ in QUESTIONS}):
            _first_sentence(client, portfolio, "¿Voy bien?", session)
        for i in range(args.runs):
            portfolio, question = QUESTIONS[i % len(QUESTIONS)]
            transcript, stt_ms = asyncio.run(_transcribe(ws_url, audio[question]))
            event, first_ms = _first_sentence(client, portfolio, transcript, session)
            tts_ms = _tts_first_byte(client, str(event["turn_id"]), int(str(event["index"])))
            run = Run(question, stt_ms, first_ms, tts_ms, transcript)
            runs.append(run)
            mark = "✓" if run.total_ms < TARGET_MS else "✗"
            print(
                f"{i + 1:>2} {mark} total {run.total_ms:6.0f} ms = STT {stt_ms:5.0f}"
                f" + 1.ª frase {first_ms:5.0f} + TTS {tts_ms:4.0f}  «{transcript}» ({portfolio})"
            )

    ok = sum(r.total_ms < TARGET_MS for r in runs)
    print(f"\n{ok}/{len(runs)} por debajo de {TARGET_MS} ms (hacen falta {REQUIRED_OK}/10)")
    for name, values in (
        ("total", [r.total_ms for r in runs]),
        ("STT final tras soltar", [r.stt_ms for r in runs]),
        ("primera frase de /ask", [r.first_sentence_ms for r in runs]),
        ("TTS primer byte", [r.tts_first_byte_ms for r in runs]),
    ):
        print(
            f"  {name:<24} mediana {statistics.median(values):6.0f} ms · máx {max(values):6.0f} ms"
        )
    sys.exit(0 if ok * 10 >= REQUIRED_OK * len(runs) else 1)


if __name__ == "__main__":
    main()
