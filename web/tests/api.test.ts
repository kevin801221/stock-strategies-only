import { expect, test, vi } from "vitest";
import { api, ApiError } from "@/lib/api";

test("validation errors are readable instead of object strings", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [{ loc: ["body", "limit"], msg: "must be positive" }] }), { status: 422 })));
  try { await expect(api.startRun("default")).rejects.toThrow("limit：must be positive"); }
  finally { vi.unstubAllGlobals(); }
});

test("an HTML proxy failure still produces a useful API error", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>Bad Gateway</html>", { status: 502 })));
  try { await expect(api.listStrategies()).rejects.toBeInstanceOf(ApiError); }
  finally { vi.unstubAllGlobals(); }
});

test("network failures explain how to recover", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
  try { await expect(api.listStrategies()).rejects.toThrow("無法連線至服務"); }
  finally { vi.unstubAllGlobals(); }
});
