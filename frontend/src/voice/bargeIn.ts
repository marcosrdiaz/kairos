/**
 * Detector de "el usuario está hablando por encima de la respuesta" (corte por voz).
 *
 * El micrófono oye dos cosas mientras suena la respuesta: al usuario y lo que se cuela de los
 * altavoces pese a la cancelación de eco. Cuánto se cuela depende del equipo, así que el
 * detector lo aprende: mientras el usuario calla, compara el volumen del micrófono con el de la
 * respuesta (`echo` ≈ micrófono / respuesta) y sigue el ruido de fondo (`floor`). Solo corta
 * cuando el micrófono supera con margen lo esperable (`margin`) durante `holdMs`.
 *
 * Al empezar a sonar la respuesta hay un calentamiento (`warmupMs`) en el que solo aprende: así
 * no se corta sola en equipos con mucho eco. Antes de que suene (mientras piensa), el umbral es
 * solo el ruido de fondo.
 */

export const BARGE_IN = {
  /** Volumen mínimo (0-1) que cuenta como voz, aunque no suene nada. */
  minLevel: 0.1,
  /** Cuántas veces por encima de lo esperable (fondo + eco) tiene que estar la voz. */
  margin: 2.5,
  /** Cuánto tiene que durar la voz para cortar la respuesta. */
  holdMs: 200,
  /** Eco supuesto al principio (micrófono / respuesta), hasta que lo aprende. */
  initialEcho: 0.1,
  /** Tiempo, desde que empieza a sonar la respuesta, en el que solo aprende el eco. */
  warmupMs: 600,
  /** Audio que se guarda antes de detectar la voz y se manda a transcribir. */
  prerollMs: 800,
} as const;

const LEARN_RATE = 0.08;
const AUDIBLE = 0.04; // por debajo, la respuesta no suena (pausa entre frases o silencio)
const PLAYBACK_WINDOW_MS = 250; // el eco llega con algo de retraso: se usa el pico reciente

export interface BargeSample {
  mic: number;
  playback: number;
  threshold: number;
}

export class BargeDetector {
  private floor = 0;
  private echo: number = BARGE_IN.initialEcho;
  private loudSince: number | null = null;
  private audibleSince: number | null = null;
  private recent: { at: number; level: number }[] = [];
  last: BargeSample = { mic: 0, playback: 0, threshold: BARGE_IN.minLevel };

  /** Añade una medida; devuelve `true` cuando hay que cortar la respuesta. */
  update(mic: number, playback: number, now: number): boolean {
    this.recent.push({ at: now, level: playback });
    while (this.recent.length > 0 && (this.recent[0]?.at ?? now) < now - PLAYBACK_WINDOW_MS) this.recent.shift();
    const peak = Math.max(0, ...this.recent.map((r) => r.level));
    const audible = peak >= AUDIBLE;
    if (!audible) this.audibleSince = null;
    else this.audibleSince ??= now;
    const warming = this.audibleSince !== null && now - this.audibleSince < BARGE_IN.warmupMs;

    const expected = Math.max(this.floor, audible ? this.echo * peak : 0);
    const threshold = Math.max(BARGE_IN.minLevel, expected * BARGE_IN.margin);
    this.last = { mic, playback: peak, threshold };

    if (warming || mic < threshold) {
      // El usuario calla (o aún se está calibrando): aprende fondo y eco.
      if (audible) this.echo += (Math.min(mic / peak, 2) - this.echo) * LEARN_RATE;
      else this.floor += (mic - this.floor) * LEARN_RATE;
      this.loudSince = null;
      return false;
    }
    this.loudSince ??= now;
    return now - this.loudSince >= BARGE_IN.holdMs;
  }
}
