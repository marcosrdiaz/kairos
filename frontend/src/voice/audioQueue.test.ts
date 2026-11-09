import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AudioQueue } from "./audioQueue";

/** Elemento de audio falso: cada `play()` "suena" y termina en el siguiente tick. */
class FakeAudio extends EventTarget {
  src = "";
  played: string[] = [];
  paused = false;
  failOn = new Set<string>();
  play(): Promise<void> {
    this.played.push(this.src);
    if (this.failOn.has(this.src)) return Promise.reject(new Error("bloqueado"));
    setTimeout(() => this.dispatchEvent(new Event("ended")), 0);
    return Promise.resolve();
  }
  pause(): void {
    this.paused = true;
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

const flush = () => new Promise((r) => setTimeout(r, 5));

describe("AudioQueue", () => {
  let audio: FakeAudio;
  beforeEach(() => {
    audio = new FakeAudio();
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it("reproduce en el orden de llegada aunque el audio de la segunda frase llegue antes", async () => {
    const onIdle = vi.fn();
    const queue = new AudioQueue({ onIdle }, audio as unknown as HTMLAudioElement);
    const first = deferred<string | null>();
    queue.enqueue(first.promise);
    queue.enqueue(Promise.resolve("blob:2"));
    await flush();
    expect(audio.played).toEqual([]);
    first.resolve("blob:1");
    await flush();
    await flush();
    expect(audio.played).toEqual(["blob:1", "blob:2"]);
    expect(onIdle).toHaveBeenCalledTimes(1);
    expect(queue.busy).toBe(false);
  });

  it("salta las frases sin audio y las que fallan, y sigue con las demás", async () => {
    audio.failOn.add("blob:mala");
    const queue = new AudioQueue({}, audio as unknown as HTMLAudioElement);
    queue.enqueue(Promise.resolve(null));
    queue.enqueue(Promise.reject(new Error("503")));
    queue.enqueue(Promise.resolve("blob:mala"));
    queue.enqueue(Promise.resolve("blob:buena"));
    await flush();
    await flush();
    expect(audio.played).toEqual(["blob:mala", "blob:buena"]);
  });

  it("stop() corta y descarta lo pendiente", async () => {
    const queue = new AudioQueue({}, audio as unknown as HTMLAudioElement);
    const later = deferred<string | null>();
    queue.enqueue(Promise.resolve("blob:1"));
    queue.enqueue(later.promise);
    await flush();
    queue.stop();
    later.resolve("blob:2");
    await flush();
    expect(audio.paused).toBe(true);
    expect(audio.played).toEqual(["blob:1"]);
  });

  it("no libera las URL que no son suyas (el aviso de IA)", async () => {
    const queue = new AudioQueue({}, audio as unknown as HTMLAudioElement);
    queue.enqueue(Promise.resolve("/api/v1/voice/disclaimer"), false);
    await flush();
    expect(URL.revokeObjectURL).not.toHaveBeenCalled();
  });
});
