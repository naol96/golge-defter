import type { Analytics, SimulationResult, Snapshot } from "./types";
import { demoAnalytics, demoSimulate, demoSnapshot } from "./demo";

export const DB = "data/golge.db";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, { signal, headers: { Accept: "application/json" } });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError("Kokpit sunucusuna ulaşılamadı.", 0);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError((body as { error?: string } | null)?.error || res.statusText, res.status);
  return body as T;
}

export interface AnalyticsParams {
  hours: number;
  bucket: number;
  limit?: number;
}

export interface DataSource {
  kind: "live" | "demo";
  snapshot(signal?: AbortSignal): Promise<Snapshot>;
  analytics(p: AnalyticsParams, signal?: AbortSignal): Promise<Analytics>;
  simulate(text: string): Promise<SimulationResult>;
}

export const liveSource: DataSource = {
  kind: "live",
  snapshot: (signal) => getJson(`/api/snapshot?db=${encodeURIComponent(DB)}`, signal),
  analytics: ({ hours, bucket, limit = 200 }, signal) =>
    getJson(`/api/analytics?db=${encodeURIComponent(DB)}&hours=${hours}&bucket=${bucket}&limit=${limit}`, signal),
  async simulate(text) {
    const res = await fetch("/api/simulate-rule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).catch(() => {
      throw new ApiError("Kokpit sunucusuna ulaşılamadı.", 0);
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new ApiError(data.error || "Simülasyon başarısız", res.status);
    return data as SimulationResult;
  },
};

export const demoSource: DataSource = {
  kind: "demo",
  snapshot: async () => demoSnapshot(),
  analytics: async (p) => demoAnalytics(p.hours, p.bucket),
  simulate: async (text) => demoSimulate(text),
};
