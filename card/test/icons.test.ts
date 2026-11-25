import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_RANGE_PAIR,
  VERDICT,
  cardStyles,
  moonLane,
  mountCard,
  target,
  targetEntity,
  targetLanes,
  verdictEntity,
} from "./harness";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

// The axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z.
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

const EVENING = { start: "2026-10-31T21:00:00Z", end: "2026-11-01T02:00:00Z" };

const ROW_NAMES = [
  "Sun altitude",
  "Moon altitude",
  "Cloud cover",
  "Cloud range",
  "Cloud low",
  "Cloud mid",
  "Cloud high",
  "Wind gust",
  "Seeing",
  "Transparency",
  "Humidity",
  "Wind speed",
  "Wind direction",
  "Rain chance",
];

function rowLabel(card: PierPressureCard, key: string): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(`.strip [data-row="${key}"] .label`) ?? null;
}

// Every row's label and the Moon up lane's, top to bottom.
function iconLabels(card: PierPressureCard): HTMLElement[] {
  return [
    ...(card.shadowRoot?.querySelectorAll<HTMLElement>(
      '.strip [data-row] .label, .strip [data-lane="moon_up"] .label',
    ) ?? []),
  ];
}

// A rule's declarations, comments left out, for a rule the test DOM does not lay out.
function declarations(selector: string): string[] {
  const css = cardStyles().replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)];
  return rules
    .filter(([, selectors]) => selectors?.split(",").some((part) => part.trim() === selector))
    .flatMap(([, , body]) => (body ?? "").split(";").map((part) => part.trim()));
}

async function withTarget(): Promise<PierPressureCard> {
  return mountCard({
    [VERDICT]: NIGHT,
    ...CLOUD_RANGE_PAIR,
    [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
  });
}

describe("a row's icon", () => {
  it("is named after its row for hovering and for a screen reader", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const icon = rowLabel(card, "seeing")?.querySelector(".icon");
    expect([
      icon?.getAttribute("role"),
      icon?.getAttribute("title"),
      icon?.getAttribute("aria-label"),
    ]).toEqual(["img", "Seeing", "Seeing"]);
  });

  it("comes before its row's name", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const parts = [...(rowLabel(card, "seeing")?.children ?? [])].map((part) => part.className);
    expect(parts).toEqual(["icon", "name"]);
  });

  it("hides its drawing from a screen reader", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const drawing = rowLabel(card, "seeing")?.querySelector(".icon svg");
    expect(drawing?.getAttribute("aria-hidden")).toBe("true");
  });

  it("leaves the screen reader one name to read, the icon's", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const name = rowLabel(card, "seeing")?.querySelector(".name");
    expect([name?.textContent, name?.getAttribute("aria-hidden")]).toEqual(["Seeing", "true"]);
  });

  it("is drawn once in each row's label and the Moon up lane's", async () => {
    const card = await withTarget();

    const names = iconLabels(card).map((label) =>
      [...label.querySelectorAll(".icon")].map((icon) => icon.getAttribute("title")),
    );
    expect(names).toEqual([...ROW_NAMES, "Moon up"].map((name) => [name]));
  });

  it("is a different drawing for each row", async () => {
    const card = await withTarget();

    const drawings = iconLabels(card).map((label) => label.querySelector(".icon svg")?.innerHTML);
    expect(new Set(drawings).size).toBe(ROW_NAMES.length + 1);
  });

  it("names the Moon up lane", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const icon = moonLane(card)?.querySelector(".label .icon");
    expect(icon?.getAttribute("aria-label")).toBe("Moon up");
  });
});

describe("a target lane's label", () => {
  it("has no icon", async () => {
    const card = await withTarget();

    expect(targetLanes(card)[0]?.querySelectorAll(".label .icon").length).toBe(0);
  });

  it("holds its rank number, named Target and the rank", async () => {
    const card = await withTarget();

    const rank = targetLanes(card)[0]?.querySelector(".label .rank");
    expect([
      rank?.textContent,
      rank?.getAttribute("title"),
      rank?.getAttribute("aria-label"),
    ]).toEqual(["1", "Target 1", "Target 1"]);
  });

  it("reads Target and the rank as its name, for a screen reader too", async () => {
    const card = await withTarget();

    const name = targetLanes(card)[0]?.querySelector(".label .name");
    expect([name?.textContent, name?.hasAttribute("aria-hidden")]).toEqual(["Target 1", false]);
  });
});

describe("the icons' styles", () => {
  it.each(["width: 16px", "height: 16px", "fill: none", "stroke: currentColor", "stroke-width: 2"])(
    "draw each icon with %s",
    (declaration) => {
      expect(declarations(".icon svg")).toContain(declaration);
    },
  );
});
