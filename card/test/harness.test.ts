import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, mountCard, verdictEntity } from "./harness";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

describe("mounting the card", () => {
  it("pins the browser's clock before the test night's dusk", async () => {
    await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(new Date().toISOString()).toBe("2026-10-31T12:00:00.000Z");
  });

  it("keeps a clock the test pinned", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-01T09:00:00Z"));

    await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(new Date().toISOString()).toBe("2026-11-01T09:00:00.000Z");
  });

  it("leaves no pinned clock after a test", () => {
    expect(vi.isFakeTimers()).toBe(false);
  });
});
