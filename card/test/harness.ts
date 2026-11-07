import type { HassEntity, HomeAssistant, PierPressureCard } from "../src/pierpressure-card";

export const VERDICT = "sensor.pierpressure_backyard_verdict";

export function verdictEntity(state: string, attributes: Record<string, unknown> = {}): HassEntity {
  return { state, attributes };
}

export async function mountCard(
  states?: Record<string, HassEntity>,
  pier = "backyard",
  timeZone = "UTC",
): Promise<PierPressureCard> {
  const card = document.createElement("pierpressure-card") as PierPressureCard;
  card.setConfig({ type: "custom:pierpressure-card", pier });
  document.body.append(card);
  if (states !== undefined) {
    const hass: HomeAssistant = { states, config: { time_zone: timeZone } };
    card.hass = hass;
  }
  await card.updateComplete;
  return card;
}

export function field(card: PierPressureCard, name: string): string | undefined {
  return card.shadowRoot?.querySelector(`[data-field="${name}"]`)?.textContent?.trim();
}

export function cardText(card: PierPressureCard): string {
  return card.shadowRoot?.textContent?.replace(/\s+/g, " ").trim() ?? "";
}
