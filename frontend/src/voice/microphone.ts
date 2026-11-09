/**
 * Micrófono → PCM 16 kHz, 16 bits, mono (lo que espera `WS /voice/stt`).
 *
 * El AudioContext va a la frecuencia nativa del dispositivo (Firefox no deja conectar un
 * micrófono a un contexto de otra frecuencia) y un AudioWorklet promedia y diezma a 16 kHz.
 * Manda trozos de 100 ms. `stop()` vacía lo pendiente antes de resolver: así no se pierde el
 * final de la frase al soltar el botón.
 */
import { STT_SAMPLE_RATE } from "../api/voice";

const CHUNK_SAMPLES = STT_SAMPLE_RATE / 10;

// Se carga como módulo del worklet desde un Blob: no hace falta un fichero aparte en public/.
const WORKLET_SOURCE = `
class Pcm16kProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / ${STT_SAMPLE_RATE};
    this.pos = 0; this.acc = 0; this.n = 0; this.len = 0;
    this.buf = new Int16Array(${CHUNK_SAMPLES});
    this.port.onmessage = (e) => {
      if (e.data === "flush") { this.flush(); this.port.postMessage("flushed"); }
    };
  }
  flush() {
    if (this.len === 0) return;
    const out = this.buf.slice(0, this.len);
    this.port.postMessage(out.buffer, [out.buffer]);
    this.len = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      this.acc += ch[i]; this.n++; this.pos += 1;
      if (this.pos >= this.ratio) {
        this.pos -= this.ratio;
        const s = Math.max(-1, Math.min(1, this.acc / this.n));
        this.buf[this.len++] = s < 0 ? s * 0x8000 : s * 0x7fff;
        this.acc = 0; this.n = 0;
        if (this.len === this.buf.length) this.flush();
      }
    }
    return true;
  }
}
registerProcessor("pcm16k", Pcm16kProcessor);
`;

export interface Microphone {
  /** Para la captura, manda lo pendiente y libera el micrófono. */
  stop(): Promise<void>;
  /** Volumen actual de la voz, de 0 a 1 (para animar la esfera). */
  level?: () => number;
}

export class MicrophoneDeniedError extends Error {
  constructor(cause: unknown) {
    super("Sin acceso al micrófono", { cause });
    this.name = "MicrophoneDeniedError";
  }
}

export async function startMicrophone(onChunk: (pcm: ArrayBuffer) => void): Promise<Microphone> {
  if (!navigator.mediaDevices?.getUserMedia || typeof AudioWorkletNode === "undefined") {
    throw new MicrophoneDeniedError("API de audio no disponible");
  }
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });
  } catch (err) {
    throw new MicrophoneDeniedError(err);
  }
  const context = new AudioContext();
  const url = URL.createObjectURL(new Blob([WORKLET_SOURCE], { type: "text/javascript" }));
  try {
    await context.audioWorklet.addModule(url);
  } finally {
    URL.revokeObjectURL(url);
  }
  const source = context.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(context, "pcm16k");
  let onFlushed: (() => void) | null = null;
  node.port.onmessage = (event: MessageEvent<ArrayBuffer | string>) => {
    if (event.data === "flushed") onFlushed?.();
    else if (event.data instanceof ArrayBuffer) onChunk(event.data);
  };
  // Conectado al destino con volumen 0: algunos navegadores no procesan nodos sin salida.
  const mute = context.createGain();
  mute.gain.value = 0;
  source.connect(node);
  node.connect(mute).connect(context.destination);
  // Solo lectura del volumen (no altera lo que se manda al STT).
  const analyser = context.createAnalyser();
  analyser.fftSize = 512;
  source.connect(analyser);
  const samples = new Float32Array(analyser.fftSize);

  return {
    level() {
      analyser.getFloatTimeDomainData(samples);
      let sum = 0;
      for (const s of samples) sum += s * s;
      return Math.min(1, Math.sqrt(sum / samples.length) * 6);
    },
    async stop() {
      await new Promise<void>((resolve) => {
        onFlushed = resolve;
        node.port.postMessage("flush");
        setTimeout(resolve, 300); // por si el contexto ya no procesa
      });
      source.disconnect();
      analyser.disconnect();
      node.disconnect();
      mute.disconnect();
      for (const track of stream.getTracks()) track.stop();
      await context.close();
    },
  };
}
