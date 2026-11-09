/**
 * Cola de audio por frase: cada frase se pide en cuanto llega (en paralelo) y suena en orden.
 *
 * Cada elemento es una promesa de URL: `null` (o un fallo al reproducir) se salta sin parar la
 * cola, así una frase sin audio no deja mudas las siguientes. `stop()` corta lo que suena y
 * descarta lo pendiente.
 */

export interface AudioQueueEvents {
  /** Empieza a sonar algo (también entre frases, si la cola no se ha vaciado). */
  onPlaying?: () => void;
  /** La cola se ha vaciado (o se ha parado). */
  onIdle?: () => void;
}

interface Item {
  url: Promise<string | null>;
  /** Las URL de `URL.createObjectURL` se liberan al terminar. */
  ownsUrl: boolean;
}

export class AudioQueue {
  private readonly items: Item[] = [];
  private readonly audio: HTMLAudioElement;
  private readonly events: AudioQueueEvents;
  private draining = false;
  private generation = 0;
  private finishCurrent: (() => void) | null = null;

  constructor(events: AudioQueueEvents = {}, audio: HTMLAudioElement = new Audio()) {
    this.events = events;
    this.audio = audio;
  }

  get busy(): boolean {
    return this.draining;
  }

  private analyser: AnalyserNode | null = null;
  private samples: Float32Array<ArrayBuffer> | null = null;

  /**
   * Engancha un analizador al elemento de audio (una sola vez) para saber el volumen de lo que
   * suena y animar el visual de voz. Si el navegador no lo permite, la cola suena igual.
   */
  private tap(): void {
    if (this.analyser || typeof AudioContext === "undefined") return;
    if (typeof HTMLMediaElement === "undefined" || !(this.audio instanceof HTMLMediaElement)) return;
    try {
      const context = new AudioContext();
      const source = context.createMediaElementSource(this.audio);
      const analyser = context.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      analyser.connect(context.destination);
      void context.resume();
      this.analyser = analyser;
      this.samples = new Float32Array(analyser.fftSize);
    } catch {
      // Sin analizador: el visual usa su movimiento propio.
    }
  }

  /** Volumen de lo que suena ahora, de 0 a 1 (0 si no suena nada o no hay analizador). */
  level(): number {
    if (!this.analyser || !this.samples || this.audio.paused) return 0;
    this.analyser.getFloatTimeDomainData(this.samples);
    let sum = 0;
    for (const s of this.samples) sum += s * s;
    return Math.min(1, Math.sqrt(sum / this.samples.length) * 5);
  }

  enqueue(url: Promise<string | null>, ownsUrl = true): void {
    // Evita "unhandled rejection" mientras espera su turno; el fallo se trata al reproducir.
    url.catch(() => undefined);
    this.items.push({ url, ownsUrl });
    if (!this.draining) void this.drain();
  }

  stop(): void {
    this.generation += 1;
    for (const item of this.items.splice(0)) {
      if (item.ownsUrl) void item.url.then((u) => u && URL.revokeObjectURL(u), () => undefined);
    }
    this.audio.pause();
    this.finishCurrent?.();
  }

  private async drain(): Promise<void> {
    const generation = this.generation;
    this.draining = true;
    while (this.items.length > 0 && generation === this.generation) {
      const item = this.items.shift() as Item;
      let url: string | null;
      try {
        url = await item.url;
      } catch {
        url = null;
      }
      if (url === null) continue;
      if (generation === this.generation) await this.play(url);
      if (item.ownsUrl) URL.revokeObjectURL(url);
    }
    if (generation === this.generation) {
      this.draining = false;
      this.events.onIdle?.();
    } else if (this.items.length > 0) {
      void this.drain();
    } else {
      this.draining = false;
      this.events.onIdle?.();
    }
  }

  private play(url: string): Promise<void> {
    return new Promise<void>((resolve) => {
      const done = () => {
        this.audio.removeEventListener("ended", done);
        this.audio.removeEventListener("error", done);
        this.finishCurrent = null;
        resolve();
      };
      this.finishCurrent = done;
      this.audio.addEventListener("ended", done);
      this.audio.addEventListener("error", done);
      this.audio.src = url;
      this.tap();
      this.events.onPlaying?.();
      this.audio.play().catch(done);
    });
  }
}
