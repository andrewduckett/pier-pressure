import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_RANGE_PAIR,
  TEMPERATURE,
  VERDICT,
  cardStyles,
  forecastEntity,
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
function declarations(selector: string, styles = cardStyles()): string[] {
  const css = styles.replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)];
  return rules
    .filter(([, selectors]) => selectors?.split(",").some((part) => part.trim() === selector))
    .flatMap(([, , body]) => (body ?? "").split(";").map((part) => part.trim()));
}

const NARROW = "@container pierpressure (width < 450px)";

// The rules inside the narrow card's container query, as their own stylesheet.
function narrowStyles(): string {
  const css = cardStyles();
  const start = css.indexOf(NARROW);
  if (start < 0) return "";
  const open = css.indexOf("{", start);
  let depth = 0;
  for (let at = open; at < css.length; at += 1) {
    if (css[at] === "{") depth += 1;
    if (css[at] === "}") depth -= 1;
    if (depth === 0) return css.slice(open + 1, at);
  }
  return "";
}

// The stylesheet with the narrow card's rules left out.
function wideStyles(): string {
  const inner = narrowStyles();
  return inner === "" ? cardStyles() : cardStyles().replace(inner, "");
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

function keyEntry(card: PierPressureCard, series: string): HTMLElement | null {
  return (
    card.shadowRoot?.querySelector<HTMLElement>(
      `.strip [data-chart="temperature"] .key [data-series="${series}"]`,
    ) ?? null
  );
}

describe("a Temperature chart key entry's icon", () => {
  it.each([
    ["temperature", "Temperature"],
    ["dew_point", "Dew point"],
  ])("names the %s line for hovering and for a screen reader", async (series, name) => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const icon = keyEntry(card, series)?.querySelector(".icon");
    expect([
      icon?.getAttribute("role"),
      icon?.getAttribute("title"),
      icon?.getAttribute("aria-label"),
    ]).toEqual(["img", name, name]);
  });

  it("sits between the line's colour sample and its name", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4]]),
    });

    const parts = [...(keyEntry(card, "temperature")?.children ?? [])].map((part) => part.className);
    expect(parts).toEqual(["swatch", "icon", "name"]);
  });

  it("comes before the line's message", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const parts = [...(keyEntry(card, "dew_point")?.children ?? [])].map((part) => part.className);
    expect(parts).toEqual(["swatch", "icon", "name", "missing"]);
  });

  it("leaves the screen reader one name to read, the icon's", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const name = keyEntry(card, "dew_point")?.querySelector(".name");
    expect(name?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("the layout", () => {
  it("follows the card's own width", () => {
    expect(declarations("ha-card")).toContain("container: pierpressure / inline-size");
  });

  it("switches for a card narrower than 450 px", () => {
    expect(cardStyles()).toContain(NARROW);
  });

  it("follows no width of the browser window", () => {
    expect(cardStyles()).not.toContain("@media");
  });

  it("is chosen by no card option", async () => {
    const plain = await mountCard({ [VERDICT]: NIGHT });
    const optioned = await mountCard({ [VERDICT]: NIGHT });
    optioned.setConfig({ type: "custom:pierpressure-card", pier: "backyard", layout: "narrow" });
    await optioned.updateComplete;

    expect(optioned.shadowRoot?.innerHTML).toBe(plain.shadowRoot?.innerHTML);
  });
});

describe("a card 450 px or wider", () => {
  it.each([".rank", ".legend"])("hides each %s", (selector) => {
    expect(declarations(selector, wideStyles())).toContain("display: none");
  });

  it("shows each label's name", () => {
    expect(declarations(".label .name", wideStyles())).not.toContain("display: none");
  });
});

describe("a card narrower than 450 px", () => {
  it("hides each label's and key entry's name", () => {
    expect(declarations(".label .name", narrowStyles())).toContain("display: none");
  });

  it("shows each rank number", () => {
    expect(declarations(".rank", narrowStyles())).toContain("display: block");
  });

  it("shows the legend", () => {
    expect(declarations(".legend", narrowStyles())).toContain("display: grid");
  });
});
